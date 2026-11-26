"""Ein Durchlauf bei GitHub. Alles Persönliche wird verschlüsselt, das Protokoll bleibt leer."""
import contextlib
import io
import json
import os
import subprocess
import sys
from pathlib import Path

import scout
import web

HIER = Path(__file__).resolve().parent
ZUSTAND = HIER / "zustand.enc"
SEITE = HIER / "site"
DATEIEN = ["journal.json", "gesehen.json", "woche.json", "modell.json"]


def openssl(daten, entschluesseln=False):
    befehl = ["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-iter", "200000", "-md", "sha256",
              "-salt", "-pass", "env:PASSWORT"] + (["-d"] if entschluesseln else [])
    return subprocess.run(befehl, input=daten, capture_output=True, check=True).stdout


def main():
    if not os.environ.get("PASSWORT") or not os.environ.get("NTFY_TOPIC"):
        sys.exit("Geheimnisse PASSWORT und NTFY_TOPIC fehlen.")
    # Lässt sich der alte Stand nicht öffnen, hier abbrechen statt ihn zu überschreiben.
    if ZUSTAND.exists():
        for name, inhalt in json.loads(openssl(ZUSTAND.read_bytes(), True)).items():
            scout.speichern(name, inhalt)
    fehler = None
    try:
        # Protokolle öffentlicher Projekte kann jeder lesen: nichts ausgeben.
        with contextlib.redirect_stdout(io.StringIO()):
            scout.scan()
    except BaseException as f:
        fehler = type(f).__name__
    alt = {n: scout.laden(n, None) for n in DATEIEN}
    ZUSTAND.write_bytes(openssl(json.dumps({n: i for n, i in alt.items() if i is not None}).encode()))
    if fehler:
        sys.exit(f"Durchlauf fehlgeschlagen: {fehler}")
    SEITE.mkdir(exist_ok=True)
    html = web.SEITE.read_text("utf-8")
    assert "const CLOUD = false;" in html
    (SEITE / "index.html").write_text(html.replace("const CLOUD = false;", "const CLOUD = true;"), "utf-8")
    (SEITE / "symbol.png").write_bytes(web.symbolbild())
    (SEITE / "daten.enc").write_bytes(openssl(json.dumps(web.dashboard_daten()).encode()))
    print("Durchlauf ok.")


if __name__ == "__main__":
    main()
