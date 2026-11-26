"""Aktien-Scout.

  python3 scout.py scan     prüfen und Meldungen schicken (läuft automatisch)
  python3 scout.py bericht  zeigen, wie gut die Muster an alten Kursen waren
  python3 scout.py bilanz   zeigen, wie die bisherigen Ideen ausgingen
  python3 scout.py test     Testnachricht aufs Handy
"""
import json
import os
import secrets
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from pathlib import Path

import config
import daten
import lernen
import strategie

ORDNER = Path(__file__).resolve().parent / "ablage"


def laden(name, standard):
    pfad = ORDNER / name
    return json.loads(pfad.read_text("utf-8")) if pfad.exists() else standard


def speichern(name, inhalt):
    ORDNER.mkdir(exist_ok=True)
    neu = ORDNER / (name + ".neu")
    neu.write_text(json.dumps(inhalt, ensure_ascii=False, indent=1), "utf-8")
    neu.replace(ORDNER / name)


def kanal():
    if os.environ.get("NTFY_TOPIC"):  # in der Cloud kommt der Name aus einem Geheimnis
        return os.environ["NTFY_TOPIC"]
    k = laden("kanal.json", None)
    if not k:
        k = {"topic": "aktienscout-" + secrets.token_hex(8)}
        speichern("kanal.json", k)
    return k["topic"]


def senden(titel, text, wichtig=False, link=None):
    nachricht = {"topic": kanal(), "title": titel, "message": text, "priority": 4 if wichtig else 3}
    if link:
        nachricht["click"] = link
    anfrage = urllib.request.Request("https://ntfy.sh/", data=json.dumps(nachricht).encode(),
                                     headers={"Content-Type": "application/json"})
    urllib.request.urlopen(anfrage, timeout=20).read()


def alle_kurse_holen():
    def eins(symbol):
        try:
            return symbol, daten.kurse(symbol)
        except Exception as fehler:
            print("Kursfehler", symbol, fehler)
            return symbol, None
    with ThreadPoolExecutor(6) as pool:
        return {s: k for s, k in pool.map(eins, config.AKTIEN) if k}


def modell(alle):
    """Wahrscheinlichkeiten einmal am Tag neu berechnen."""
    m = laden("modell.json", None)
    if not m or m.get("stand") != date.today().isoformat():
        m = strategie.lernen({s: k[0] for s, k in alle.items()})
        m["stand"] = date.today().isoformat()
        speichern("modell.json", m)
    return m


def euro(wert, waehrung, kurs):
    return wert * (kurs if waehrung == "USD" else 1.0)


def zahl(x, stellen=2):
    return f"{x:,.{stellen}f}".replace(",", " ").replace(".", ",")


def ideen_suchen(alle, m, journal):
    heute = date.today().isoformat()
    frei = config.MAX_IDEEN_PRO_TAG - sum(i["erstellt"] == heute and not i.get("still") for i in journal)
    laufend = {i["symbol"] for i in journal if i["status"] in ("wartet", "offen")}
    belegt = sum(i["status"] in ("wartet", "offen") and not i.get("still") for i in journal)
    konto = config.STARTKAPITAL + sum(i["netto"] * config.EINSATZ_EURO
                                      for i in journal if "netto" in i and not i.get("still"))
    frei = min(frei, int(konto // config.EINSATZ_EURO) - belegt)
    kandidaten = []
    for symbol, (tage, preis, waehrung) in alle.items():
        if symbol in laufend or len(tage) < 260:
            continue
        # Kerze zu alt (z. B. Datenfehler)? Dann nichts vorschlagen.
        if (date.today() - date.fromisoformat(tage[-1]["d"])).days > 4:
            continue
        werte = strategie.merkmale(tage)[-1]
        for name, info in m["muster"].items():
            if info["brauchbar"] and strategie.MUSTER[name](werte):
                z, b, dauer = info["plan"]
                ziel, bremse = werte["c"] + z * werte["atr"], werte["c"] - b * werte["atr"]
                # Kurs schon weggelaufen oder unter der Notbremse: Idee veraltet.
                if not bremse < preis < werte["c"] + 0.5 * (ziel - werte["c"]):
                    continue
                kandidaten.append((info["neu"]["schnitt"], symbol, name, info, werte["c"], ziel,
                                   bremse, dauer, tage[-1]["d"], waehrung))
    kandidaten.sort(reverse=True)

    usd = daten.dollar_in_euro() if kandidaten else 1.0
    gewaehlt = set()
    for _, symbol, name, info, kauf, ziel, bremse, dauer, signaltag, waehrung in kandidaten:
        still = lernen.pausiert(journal, name)
        if (frei <= 0 and not still) or symbol in gewaehlt:
            continue
        firma = config.AKTIEN[symbol]
        try:
            news = daten.nachrichten(symbol, firma)
        except Exception as fehler:
            print("Newsfehler", symbol, fehler)
            continue
        schlecht = [n for n in news if n["wert"] < 0]
        gut = [n for n in news if n["wert"] > 0]
        if len(schlecht) > len(gut):
            print(f"{firma}: Idee verworfen wegen schlechter News: {schlecht[0]['titel']}")
            continue
        n = info["neu"]
        chance = lernen.angepasste_chance(n["ziel"], journal, name)
        eigen = lernen.eigene_bilanz(journal, name)
        k, zk, bk = (euro(x, waehrung, usd) for x in (kauf, ziel, bremse))
        gewinn = config.EINSATZ_EURO * (ziel / kauf - 1 - strategie.KOSTEN)
        verlust = config.EINSATZ_EURO * (bremse / kauf - 1 - strategie.KOSTEN)
        text = (
            f"Kaufen: max. {zahl(k)} € (Limit-Order, nur nächster Handelstag)\n"
            f"Verkaufen: {zahl(zk)} € (+{zahl((ziel / kauf - 1) * 100, 1)} %)\n"
            f"Notbremse: {zahl(bk)} € ({zahl((bremse / kauf - 1) * 100, 1)} %)\n"
            f"Spätestens verkaufen nach {dauer} Handelstagen\n\n"
            f"In {n['n']} ähnlichen Fällen:\n"
            f"Ziel erreicht {n['ziel']:.0%} | Notbremse {n['bremse']:.0%} | Zeit abgelaufen {n['zeit']:.0%}\n"
            f"Am Ende im Plus: {n['plus']:.0%}\n"
            f"Ziel-Chance mit eigener Erfahrung ({eigen['n']} Ideen): {chance:.0%}\n"
            f"Schnitt je Fall: {zahl(n['schnitt'] * 100)} % (Zufallskauf: {zahl(info['immer']['schnitt'] * 100)} %)\n\n"
            f"Bei {zahl(config.EINSATZ_EURO, 0)} € nach Gebühren: Ziel {zahl(gewinn)} €, "
            f"Notbremse {zahl(verlust)} € (vor Steuer)\n"
            f"Muster: {name}\n"
            f"News: {len(gut)} gut, {len(schlecht)} schlecht"
            + (f"\n„{news[0]['titel'][:110]}“" if news else "")
            + ("\nHinweis: US-Aktie, Euro-Kurse schwanken mit dem Dollar." if waehrung == "USD" else "")
        )
        if not still:
            senden(f"Kauf-Idee: {firma}", text, wichtig=True, link=news[0]["link"] if news else None)
            print(f"\n=== {firma} ===\n{text}")
        journal.append({"symbol": symbol, "firma": firma, "muster": name, "erstellt": heute,
                        "signaltag": signaltag, "kauf": kauf, "ziel": ziel, "bremse": bremse,
                        "dauer": dauer, "waehrung": waehrung, "status": "wartet",
                        "chance": chance, "still": still,
                        "news_gut": len(gut), "news_schlecht": len(schlecht)})
        gewaehlt.add(symbol)
        frei -= 0 if still else 1
    if not gewaehlt:
        print("Keine neue Idee: kein Muster mit genug Vorteil passt gerade.")


def ideen_pruefen(alle, journal):
    """Meldet Kauf, Ziel, Notbremse oder Zeitablauf für laufende Ideen."""
    for idee in journal:
        if idee["status"] not in ("wartet", "offen") or idee["symbol"] not in alle:
            continue
        melden = (lambda *a: None) if idee.get("still") else senden
        tage, preis, waehrung = alle[idee["symbol"]]
        folge = [t for t in tage if t["d"] > idee["signaltag"]]
        # Aktien-Splits u. Ä. verschieben alte Kurse: Idee dann abbrechen.
        alt = next((t["c"] for t in tage if t["d"] == idee["signaltag"]), None)
        if alt and abs(alt / idee["kauf"] - 1) > 0.02:
            idee["status"] = "abgebrochen"
            melden(f"{idee['firma']}: bitte selbst prüfen", "Alte Kurse wurden angepasst (z. B. Split).")
            continue
        e = strategie.nachspielen(folge, idee["kauf"], idee["ziel"], idee["bremse"], idee["dauer"])
        usd = daten.dollar_in_euro() if waehrung == "USD" else 1.0
        # Während des Handels: sofort warnen, wenn Ziel oder Notbremse erreicht sind.
        if e["status"] == "offen" and preis:
            marke = "ziel" if preis >= idee["ziel"] else "bremse" if preis <= idee["bremse"] else None
            if marke and idee.get("gewarnt") != marke:
                wort = "Zielkurs erreicht" if marke == "ziel" else "Notbremse erreicht"
                melden(f"{idee['firma']}: {wort}",
                       f"Aktuell etwa {zahl(euro(preis, waehrung, usd))} €. Falls gekauft: jetzt verkaufen prüfen.", True)
                idee["gewarnt"] = marke
        if "kaufpreis" in e:
            idee.update(kaufpreis=e["kaufpreis"], gekauft_am=folge[0]["d"])
        if "verkauf" in e:
            idee.update(verkauf=e["verkauf"], verkauft_am=e["datum"])
        if e["status"] == idee["status"] or e["status"] == "wartet":
            continue
        idee["status"] = e["status"]
        if e["status"] == "nicht_gekauft":
            melden(f"{idee['firma']}: Kaufkurs nicht erreicht", "Order streichen. Idee ist erledigt.")
        elif e["status"] == "offen":
            melden(f"{idee['firma']}: Kaufkurs erreicht",
                   f"Verkaufsorder bei {zahl(euro(idee['ziel'], waehrung, usd))} €, "
                   f"Notbremse bei {zahl(euro(idee['bremse'], waehrung, usd))} €.")
        else:
            idee["netto"] = e["netto"]
            wort = {"ziel": "Ziel erreicht", "bremse": "Notbremse", "zeit": "Zeit abgelaufen: verkaufen"}
            melden(f"{idee['firma']}: {wort[e['status']]}",
                   f"Ergebnis nach Gebühren: {zahl(e['netto'] * 100)} % "
                   f"(≈ {zahl(e['netto'] * config.EINSATZ_EURO)} €)", True)


def stand_speichern(alle):
    """Momentaufnahme für das Dashboard."""
    kurse = {s: {"name": config.AKTIEN[s], "preis": preis, "waehrung": w,
                 "verlauf": [[x["d"], round(x["c"], 2)] for x in tage[-90:]]}
             for s, (tage, preis, w) in alle.items() if preis and tage}
    speichern("stand.json", {"zeit": datetime.now().isoformat(timespec="minutes"),
                             "usd": daten.dollar_in_euro(), "einsatz": config.EINSATZ_EURO,
                             "start": config.STARTKAPITAL, "gebuehr": config.GEBUEHR_PRO_ORDER,
                             "kosten": strategie.KOSTEN,
                             "kurse": kurse})


def scan():
    alle = alle_kurse_holen()
    if len(alle) < len(config.AKTIEN) // 2:
        sys.exit("Zu wenige Kurse geladen, Abbruch. Internet prüfen.")
    m = modell(alle)
    journal = laden("journal.json", [])
    try:
        ideen_pruefen(alle, journal)
        ideen_suchen(alle, m, journal)
        # Eilmeldungen zu Aktien mit laufender Idee
        gesehen = laden("gesehen.json", [])
        for idee in [i for i in journal if i["status"] in ("wartet", "offen") and not i.get("still")]:
            for n in daten.nachrichten(idee["symbol"], idee["firma"], stunden=6):
                if n["wert"] < 0 and n["titel"] not in gesehen:
                    senden(f"Warnung {idee['firma']}", n["titel"], True, n["link"])
                    gesehen.append(n["titel"])
        speichern("gesehen.json", gesehen[-500:])
        woche = "{}-{}".format(*date.today().isocalendar()[:2])
        if journal and laden("woche.json", None) != woche:
            senden("Wochen-Analyse", lernen.wochenbericht(journal, strategie.MUSTER))
            speichern("woche.json", woche)
    finally:
        speichern("journal.json", journal)
    stand_speichern(alle)
    print("Fertig:", datetime.now().strftime("%d.%m. %H:%M"))


def bericht():
    m = modell(alle_kurse_holen())
    print(f"\nKontrollzeitraum ab {m['trennung']}, Einsatz {config.EINSATZ_EURO:.0f} €, "
          f"Kosten je Kauf+Verkauf {strategie.KOSTEN:.2%}\n")
    for name, i in m["muster"].items():
        z, b, dauer = i["plan"]
        n = i["neu"]
        print(f"{name}  (Haltedauer {dauer} Tage, {n['n']} Fälle)")
        print(f"  Ziel {n['ziel']:.0%} | Notbremse {n['bremse']:.0%} | Zeit {n['zeit']:.0%} | im Plus {n['plus']:.0%}")
        print(f"  Schnitt nach Gebühren: alt {i['alt']['schnitt']:+.2%}, neu {n['schnitt']:+.2%}, "
              f"Zufallskauf {i['immer']['schnitt']:+.2%}")
        print(f"  -> {'wird gemeldet' if i['brauchbar'] else 'zu schwach, wird nicht gemeldet'}\n")


def bilanz():
    journal = laden("journal.json", [])
    fertig = [i for i in journal if "netto" in i]
    print(f"Ideen gesamt: {len(journal)}, abgeschlossen: {len(fertig)}")
    for i in journal:
        print(f"  {i['erstellt']} {i['firma']:<20} {i['status']:<14}"
              + (f"{i['netto']:+.2%}" if "netto" in i else ""))
    print("\n" + lernen.wochenbericht(journal, strategie.MUSTER))
    if fertig:
        treffer = sum(i["status"] == "ziel" for i in fertig) / len(fertig)
        summe = sum(i["netto"] for i in fertig) * config.EINSATZ_EURO
        print(f"Ziel erreicht: {treffer:.0%} | Summe nach Gebühren: {summe:+.2f} € (vor Steuer)")


if __name__ == "__main__":
    befehl = sys.argv[1] if len(sys.argv) > 1 else "scan"
    if befehl == "test":
        senden("Aktien-Scout", "Testnachricht: dein Handy ist verbunden.", True)
        print("Gesendet an Kanal:", kanal())
    elif befehl in ("scan", "bericht", "bilanz"):
        {"scan": scan, "bericht": bericht, "bilanz": bilanz}[befehl]()
    else:
        print(__doc__)
