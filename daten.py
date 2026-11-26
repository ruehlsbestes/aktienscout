"""Kurse und Nachrichten aus kostenlosen Quellen (nur Standardbibliothek)."""
import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

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


def nachrichten(symbol, name, stunden=48):
    """Neue Schlagzeilen mit einfacher Bewertung: +1 gut, -1 schlecht, 0 neutral."""
    if symbol.endswith(".DE"):
        suche = urllib.parse.quote(f'"{name}" Aktie when:2d')
        url = f"https://news.google.com/rss/search?q={suche}&hl=de&gl=DE&ceid=DE:de"
    else:
        url = ("https://feeds.finance.yahoo.com/rss/2.0/headline?"
               f"s={urllib.parse.quote(symbol)}&region=US&lang=en-US")
    grenze = datetime.now(timezone.utc) - timedelta(hours=stunden)
    treffer = []
    for eintrag in ET.fromstring(_laden(url)).iter("item"):
        titel = (eintrag.findtext("title") or "").strip()
        try:
            wann = parsedate_to_datetime(eintrag.findtext("pubDate"))
        except (TypeError, ValueError):
            continue
        # Nur Schlagzeilen, in denen die Firma wirklich vorkommt.
        if wann < grenze or name.split()[0].lower() not in titel.lower():
            continue
        wert = -1 if _enthaelt(titel, SCHLECHT) else 1 if _enthaelt(titel, GUT) else 0
        treffer.append({"titel": titel, "link": eintrag.findtext("link") or "", "wert": wert,
                        "zeit": wann.isoformat()})
    return sorted(treffer, key=lambda n: n["zeit"], reverse=True)
