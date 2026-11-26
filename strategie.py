"""Kaufmuster, Nachspielen an alten Kursen und Wahrscheinlichkeiten.

Regeln beim Nachspielen (bewusst vorsichtig):
- Signal nach Börsenschluss, Kauf nur, wenn der Kurs am Folgetag den Kaufkurs erreicht.
- Werden Ziel und Notbremse am selben Tag berührt, zählt die Notbremse.
- Nach Ablauf der Haltedauer wird zum Schlusskurs verkauft.
"""
import config

# (Ziel, Notbremse) als Vielfache der üblichen Tagesschwankung, Haltedauer in Handelstagen
PLAENE = [(1.0, 1.5, 4), (1.5, 1.5, 7), (2.0, 2.0, 10), (3.0, 2.0, 15), (4.0, 2.5, 20)]

MUSTER = {
    "Rücksetzer im Aufwärtstrend": lambda m: m["c"] > m["s200"] and m["rsi3"] < 20,
    "Ausbruch auf 3-Monats-Hoch": lambda m: m["c"] > m["s200"] and m["c"] > m["hoch63"],
    "Starker Absturz (Gegenbewegung)": lambda m: m["r5"] < -2.5 * m["atr"] / m["c"],
    "Trend dreht nach oben": lambda m: m["c"] > m["s50"] and m["vortag"] <= m["s50_vortag"]
                                       and m["s50"] > m["s200"],
}

KOSTEN = (2 * config.GEBUEHR_PRO_ORDER / config.EINSATZ_EURO) + config.SPREAD_PROZENT / 100


def merkmale(tage):
    """Kennzahlen je Tag; None, solange zu wenig Vorgeschichte da ist."""
    c = [t["c"] for t in tage]
    summe = [0.0]
    for x in c:
        summe.append(summe[-1] + x)
    schnitt = lambda i, n: (summe[i + 1] - summe[i + 1 - n]) / n
    spanne = [0.0] + [max(t["h"] - t["l"], abs(t["h"] - c[i - 1]), abs(t["l"] - c[i - 1]))
                      for i, t in enumerate(tage) if i > 0]
    ergebnis = [None] * len(tage)
    for i in range(201, len(tage)):
        diff = [c[j] - c[j - 1] for j in range(i - 2, i + 1)]
        auf = sum(d for d in diff if d > 0)
        ab = -sum(d for d in diff if d < 0)
        ergebnis[i] = {
            "c": c[i], "vortag": c[i - 1], "s50": schnitt(i, 50), "s50_vortag": schnitt(i - 1, 50),
            "s200": schnitt(i, 200), "atr": sum(spanne[i - 13:i + 1]) / 14,
            "rsi3": 100 * auf / (auf + ab) if auf + ab else 50,
            "hoch63": max(c[i - 63:i]), "r5": c[i] / c[i - 5] - 1,
        }
    return ergebnis


def nachspielen(folgetage, kauf, ziel, bremse, dauer):
    """Spielt einen Plan durch. Status: offen, nicht_gekauft, wartet, ziel, bremse, zeit."""
    if not folgetage:
        return {"status": "wartet"}
    erster = folgetage[0]
    if erster["l"] > kauf:
        return {"status": "nicht_gekauft"}
    preis = min(erster["o"], kauf)
    for n, t in enumerate(folgetage[:dauer]):
        if n > 0 and t["o"] <= bremse:
            return _ende("bremse", preis, t["o"], t["d"])
        if n > 0 and t["o"] >= ziel:
            return _ende("ziel", preis, t["o"], t["d"])
        if t["l"] <= bremse:
            return _ende("bremse", preis, bremse, t["d"])
        # Am Kauftag ist die Reihenfolge unbekannt: Ziel zählt nur bei Kauf zur Eröffnung.
        if t["h"] >= ziel and (n > 0 or erster["o"] <= kauf):
            return _ende("ziel", preis, ziel, t["d"])
    if len(folgetage) >= dauer:
        t = folgetage[dauer - 1]
        return _ende("zeit", preis, t["c"], t["d"])
    return {"status": "offen", "kaufpreis": preis}


def _ende(status, kauf, verkauf, datum):
    return {"status": status, "kaufpreis": kauf, "verkauf": verkauf, "datum": datum,
            "netto": verkauf / kauf - 1 - KOSTEN}


def _auswerten(faelle):
    n = len(faelle)
    if not n:
        return None
    return {
        "n": n,
        "ziel": sum(f["status"] == "ziel" for f in faelle) / n,
        "bremse": sum(f["status"] == "bremse" for f in faelle) / n,
        "zeit": sum(f["status"] == "zeit" for f in faelle) / n,
        "plus": sum(f["netto"] > 0 for f in faelle) / n,
        "schnitt": sum(f["netto"] for f in faelle) / n,
    }


def lernen(alle_kurse):
    """Prüft jedes Muster: Plan auf alten Daten wählen, auf neueren Daten kontrollieren."""
    daten = sorted(t["d"] for tage in alle_kurse.values() for t in tage)
    trennung = daten[int(len(daten) * 0.65)]
    sammlung = {(name, p): ([], []) for name in list(MUSTER) + ["_immer"] for p in PLAENE}
    for tage in alle_kurse.values():
        werte = merkmale(tage)
        for p_i, plan in enumerate(PLAENE):
            z, b, dauer = plan
            frei_ab = {}
            for i in range(201, len(tage) - dauer):
                m = werte[i]
                passend = [n for n, regel in MUSTER.items() if regel(m)]
                # Vergleichswert "irgendwann kaufen": jeden 3. Tag reicht.
                if i % 3 == 0:
                    passend.append("_immer")
                passend = [n for n in passend if i >= frei_ab.get(n, 0)]
                if not passend:
                    continue
                e = nachspielen(tage[i + 1:i + 1 + dauer], m["c"], m["c"] + z * m["atr"],
                                m["c"] - b * m["atr"], dauer)
                if "netto" not in e:
                    continue
                for n in passend:
                    sammlung[(n, plan)][tage[i]["d"] >= trennung].append(e)
                    if n != "_immer":
                        frei_ab[n] = i + dauer  # keine doppelt gezählten Fälle je Aktie

    bericht = {"trennung": trennung, "muster": {}}
    for name in MUSTER:
        # Planwahl NUR mit den alten Daten, sonst schummelt der Test.
        alt = {p: _auswerten(sammlung[(name, p)][0]) for p in PLAENE}
        gueltig = [p for p in PLAENE if alt[p]]
        if not gueltig:
            continue
        plan = max(gueltig, key=lambda p: alt[p]["schnitt"])
        neu = _auswerten(sammlung[(name, plan)][1])
        immer = _auswerten(sammlung[("_immer", plan)][1])
        if not neu or not immer:
            continue
        vorsprung = neu["schnitt"] - immer["schnitt"]
        brauchbar = (neu["n"] >= config.MIN_FAELLE
                     and alt[plan]["schnitt"] > 0
                     and neu["schnitt"] * 100 >= config.MIN_GEWINN_PROZENT
                     and vorsprung * 100 >= config.MIN_VORSPRUNG_PROZENT)
        bericht["muster"][name] = {"plan": plan, "alt": alt[plan], "neu": neu, "immer": immer,
                                   "vorsprung": vorsprung, "brauchbar": brauchbar}
    return bericht
