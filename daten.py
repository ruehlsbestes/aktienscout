"""Kurse und Nachrichten aus kostenlosen Quellen (nur Standardbibliothek)."""
import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

import config

KOPF = {"User-Agent": "Mozilla/5.0"}


def _laden(url, versuche=3):
    for i in range(versuche):
        try:
            anfrage = urllib.request.Request(url, headers=KOPF)
            with urllib.request.urlopen(anfrage, timeout=20) as antwort:
                return antwort.read()
        except Exception:
            if i == versuche - 1:
                raise
            time.sleep(2 * (i + 1))


def kurse(symbol, zeitraum="10y"):
    """Liefert (abgeschlossene Tageskerzen, aktueller Kurs, Währung)."""
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}"
           f"?range={zeitraum}&interval=1d&events=split")
    ergebnis = json.loads(_laden(url))["chart"]["result"][0]
    meta, werte = ergebnis["meta"], ergebnis["indicators"]["quote"][0]
    versatz = meta.get("gmtoffset", 0)
    tage = []
    for i, zeit in enumerate(ergebnis.get("timestamp", [])):
        o, h, l, c = (werte[k][i] for k in ("open", "high", "low", "close"))
        if None in (o, h, l, c) or min(o, h, l, c) <= 0:
            continue
        datum = datetime.fromtimestamp(zeit + versatz, timezone.utc).date().isoformat()
        tage.append({"d": datum, "o": o, "h": h, "l": l, "c": c})
    # Den laufenden Handelstag weglassen: er ist noch nicht fertig.
    ende = meta.get("currentTradingPeriod", {}).get("regular", {}).get("end")
    if tage and ende:
        ende_tag = datetime.fromtimestamp(ende + versatz, timezone.utc).date().isoformat()
        if tage[-1]["d"] == ende_tag and time.time() < ende + 1200:
            tage.pop()
    return tage, meta.get("regularMarketPrice"), meta.get("currency", "EUR")


def dollar_in_euro():
    _, preis, _ = kurse("EURUSD=X", "5d")
    return 1.0 / preis


SCHLECHT = ["gewinnwarnung", "prognose gesenkt", "senkt prognose", "klage", "ermittlung", "razzia",
            "rückruf", "herabgestuft", "stellenabbau", "einbruch", "absturz", "skandal", "insolvenz",
            "profit warning", "lawsuit", "sues", "probe", "investigation", "recall", "downgrade",
            "cuts forecast", "cuts guidance", "misses", "plunge", "plunges", "slumps", "fraud"]
GUT = ["prognose angehoben", "hebt prognose", "rekord", "übertrifft", "hochgestuft", "großauftrag",
       "aktienrückkauf", "dividende erhöht", "upgrade", "upgraded", "beats", "record", "raises guidance",
       "raises forecast", "buyback", "surges", "soars", "wins contract"]


def _enthaelt(text, woerter):
    umgeben = " " + "".join(z if z.isalnum() else " " for z in text.lower()) + " "
    return any(f" {w} " in umgeben for w in woerter)


def _norm(text):
    return " " + " ".join("".join(z if z.isalnum() else " " for z in text.lower()).split()) + " "


def _google(suche, sprache, stunden):
    land = "hl=de&gl=DE&ceid=DE:de" if sprache == "de" else "hl=en-US&gl=US&ceid=US:en"
    q = urllib.parse.quote(f"{suche} when:{max(1, stunden // 24)}d")
    return f"https://news.google.com/rss/search?q={q}&{land}"


def _feed(url, stunden):
    grenze = datetime.now(timezone.utc) - timedelta(hours=stunden)
    for eintrag in ET.fromstring(_laden(url, 2)).iter("item"):
        titel = (eintrag.findtext("title") or "").strip()
        try:
            wann = parsedate_to_datetime(eintrag.findtext("pubDate"))
            if wann < grenze:
                continue
        except (TypeError, ValueError):
            continue
        link = eintrag.findtext("link") or ""
        wert = -1 if _enthaelt(titel, SCHLECHT) else 1 if _enthaelt(titel, GUT) else 0
        yield {"titel": titel, "link": link if link.startswith("https://") else "", "wert": wert,
               "zeit": wann.astimezone(timezone.utc).isoformat()}


def _sammeln(urls, stunden):
    """Mehrere Quellen zusammenführen; eine ausgefallene Quelle stört nicht."""
    treffer, fehler = {}, []
    for url in urls:
        try:
            for n in _feed(url, stunden):
                treffer.setdefault(_norm(n["titel"]), n)
        except Exception as f:
            fehler.append(f)
    if len(fehler) == len(urls):
        raise fehler[0]
    return sorted(treffer.values(), key=lambda n: n["zeit"], reverse=True)


def nachrichten(symbol, name, stunden=48):
    """Schlagzeilen zu einem Wert (deutsch und englisch): +1 gut, -1 schlecht, 0 neutral."""
    krypto = symbol.endswith("-EUR")
    name = config.SUCHNAMEN.get(symbol, name)
    urls = [_google(f'"{name}" {"Kurs" if krypto else "Aktie"}', "de", stunden),
            _google(f'"{name}" {"crypto" if krypto else "stock"}', "en", stunden)]
    if "." not in symbol:
        urls.append("https://feeds.finance.yahoo.com/rss/2.0/headline?"
                    f"s={urllib.parse.quote(symbol.replace('-EUR', '-USD'))}&region=US&lang=en-US")
    # Nur Schlagzeilen, in denen der Name wirklich als Wort vorkommt.
    return [n for n in _sammeln(urls, stunden) if _norm(name) in _norm(n["titel"])]


ALLGEMEIN = [("Börse Aktien", "de"), ("DAX heute", "de"), ("Quartalszahlen Prognose", "de"),
             ("Gewinnwarnung", "de"), ("Übernahme Angebot Aktie", "de"), ("Kryptowährung Bitcoin", "de"),
             ("stock market today", "en"), ("earnings guidance shares", "en"), ("analyst upgrade downgrade", "en"),
             ("merger acquisition deal shares", "en"), ("crypto market", "en"), ("Federal Reserve ECB interest rates", "en")]


def marktnachrichten(werte, stunden=24):
    """Breite Suche über allgemeine Markt-Themen, Schlagzeilen den Werten zuordnen."""
    namen = [(s, n, _norm(config.SUCHNAMEN.get(s, n))) for s, n in werte.items()]
    ergebnis = []
    for n in _sammeln([_google(q, sprache, stunden) for q, sprache in ALLGEMEIN], stunden):
        titel = _norm(n["titel"])
        passend = next(((s, name) for s, name, such in namen if such in titel), (None, None))
        ergebnis.append({**n, "symbol": passend[0], "name": passend[1]})
    return ergebnis
