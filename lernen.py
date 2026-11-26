"""Der Scout wertet seine eigenen Ideen aus und passt sich an."""
import config


def eigene_bilanz(journal, muster):
    """Ergebnisse der letzten 40 abgeschlossenen Ideen eines Musters."""
    fertig = [i for i in journal if i["muster"] == muster and "netto" in i][-40:]
    n = len(fertig)
    return {
        "n": n,
        "ziel": sum(i["status"] == "ziel" for i in fertig) / n if n else 0.0,
        "schnitt": sum(i["netto"] for i in fertig) / n if n else 0.0,
    }


def pausiert(journal, muster):
    """Muster stumm schalten, wenn es in echt Verlust bringt. Es läuft still weiter
    und wird wieder gemeldet, sobald die neueren Ergebnisse im Plus sind."""
    b = eigene_bilanz(journal, muster)
    return b["n"] >= config.MIN_EIGENE_FAELLE and b["schnitt"] < 0


def angepasste_chance(historisch, journal, muster):
    """Mischt alte Daten (Gewicht: 50 Fälle) mit den eigenen echten Ergebnissen."""
    b = eigene_bilanz(journal, muster)
    return (50 * historisch + b["n"] * b["ziel"]) / (50 + b["n"])


def wochenbericht(journal, namen):
    zeilen = []
    for name in namen:
        b = eigene_bilanz(journal, name)
        if b["n"]:
            zeilen.append(f"{name}: {b['n']} fertig, Ziel {b['ziel']:.0%}, "
                          f"Schnitt {b['schnitt']:+.2%}" + (" (pausiert)" if pausiert(journal, name) else ""))
    return "\n".join(zeilen) or "Noch keine abgeschlossenen Ideen."
