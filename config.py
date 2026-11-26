"""Einstellungen: hier darfst du Werte ändern."""

EINSATZ_EURO = 500.0        # Geld pro Kauf-Idee (für die Gebührenrechnung)
GEBUEHR_PRO_ORDER = 1.0     # Trade Republic: 1 € beim Kauf, 1 € beim Verkauf
SPREAD_PROZENT = 0.15       # geschätzter Kursaufschlag für Kauf + Verkauf zusammen
STEUERSATZ = 0.26375        # Abgeltungsteuer + Soli, nur über dem Sparerpauschbetrag

MIN_FAELLE = 200            # so viele alte Fälle braucht eine Wahrscheinlichkeit
MIN_GEWINN_PROZENT = 0.30   # erwarteter Schnitt nach Gebühren, sonst keine Meldung
MIN_VORSPRUNG_PROZENT = 0.20  # so viel besser als "irgendwann kaufen"
MAX_IDEEN_PRO_TAG = 3
STARTKAPITAL = 5000.0       # virtuelles Konto im Dashboard
MIN_EIGENE_FAELLE = 15      # ab so vielen eigenen Ergebnissen darf ein Muster pausieren

# Kürzel (Yahoo) -> Name für Meldungen und Nachrichtensuche
AKTIEN = {
    # Deutschland
    "SAP.DE": "SAP", "SIE.DE": "Siemens", "ALV.DE": "Allianz", "DTE.DE": "Deutsche Telekom",
    "MBG.DE": "Mercedes-Benz", "BMW.DE": "BMW", "VOW3.DE": "Volkswagen", "BAS.DE": "BASF",
    "BAYN.DE": "Bayer", "MUV2.DE": "Münchener Rück", "IFX.DE": "Infineon", "ADS.DE": "Adidas",
    "DBK.DE": "Deutsche Bank", "RHM.DE": "Rheinmetall", "DHL.DE": "DHL", "EOAN.DE": "E.ON",
    "RWE.DE": "RWE", "HEN3.DE": "Henkel",
    # USA
    "AAPL": "Apple", "MSFT": "Microsoft", "NVDA": "Nvidia", "AMZN": "Amazon", "GOOGL": "Alphabet",
    "META": "Meta", "TSLA": "Tesla", "AVGO": "Broadcom", "JPM": "JPMorgan", "V": "Visa",
    "JNJ": "Johnson & Johnson", "WMT": "Walmart", "PG": "Procter & Gamble", "KO": "Coca-Cola",
    "PEP": "PepsiCo", "MCD": "McDonald's", "DIS": "Disney", "NFLX": "Netflix", "AMD": "AMD",
    "COST": "Costco", "NKE": "Nike", "XOM": "Exxon Mobil",
}
