"""Dashboard fürs Handy im Heim-WLAN (nur lesen).

  python3 web.py        Server starten
  python3 web.py link   Adresse anzeigen und aufs Handy schicken
"""
import json
import secrets
import struct
import subprocess
import sys
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import lernen
import scout

PORT = 8766
SEITE = Path(__file__).resolve().parent / "dashboard.html"


def token():
    k = scout.laden("web.json", None)
    if not k:
        k = {"token": secrets.token_urlsafe(12)}
        scout.speichern("web.json", k)
    return k["token"]


def adresse():
    name = subprocess.run(["scutil", "--get", "LocalHostName"], capture_output=True, text=True).stdout.strip()
    return f"http://{name}.local:{PORT}/{token()}/"


def symbolbild(n=180):
    """App-Symbol: steigende Balken, ohne Zusatzpakete als PNG erzeugt."""
    zeilen = bytearray()
    balken = [(35, 60, 115), (75, 100, 85), (115, 140, 50)]  # links, rechts, oben
    for y in range(n):
        zeilen.append(0)
        for x in range(n):
            an = any(l <= x < r and o <= y < 145 for l, r, o in balken)
            zeilen += bytes((57, 135, 229) if an else (26, 26, 25))
    def block(art, inhalt):
        return struct.pack(">I", len(inhalt)) + art + inhalt + struct.pack(">I", zlib.crc32(art + inhalt))
    return (b"\x89PNG\r\n\x1a\n" + block(b"IHDR", struct.pack(">IIBBBBB", n, n, 8, 2, 0, 0, 0))
            + block(b"IDAT", zlib.compress(bytes(zeilen))) + block(b"IEND", b""))


def dashboard_daten():
    journal = scout.laden("journal.json", [])
    return {
        "stand": scout.laden("stand.json", None),
        "journal": journal,
        "modell": scout.laden("modell.json", None),
        "lernen": {n: {**lernen.eigene_bilanz(journal, n), "pausiert": lernen.pausiert(journal, n)}
                   for n in (scout.laden("modell.json", None) or {"muster": {}})["muster"]},
        "news": scout.laden("news.json", {"liste": []})["liste"][:250],
    }


class Anfrage(BaseHTTPRequestHandler):
    def do_GET(self):
        basis = f"/{token()}/"
        pfad = self.path.split("?")[0]
        if pfad == basis:
            self.antwort(SEITE.read_bytes(), "text/html; charset=utf-8")
        elif pfad == basis + "daten":
            self.antwort(json.dumps(dashboard_daten()).encode(), "application/json")
        elif pfad == basis + "symbol.png":
            self.antwort(symbolbild(), "image/png")
        else:
            self.send_error(404)

    def antwort(self, inhalt, art):
        self.send_response(200)
        self.send_header("Content-Type", art)
        self.send_header("Content-Length", str(len(inhalt)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(inhalt)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    if sys.argv[1:] == ["link"]:
        scout.senden("Dein Aktien-Dashboard", f"Im Heim-WLAN antippen:\n{adresse()}", link=adresse())
        print(adresse())
    else:
        ThreadingHTTPServer(("0.0.0.0", PORT), Anfrage).serve_forever()
