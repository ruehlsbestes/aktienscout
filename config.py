"""Einstellungen: hier darfst du Werte ändern."""

EINSATZ_EURO = 500.0        # Geld pro Kauf-Idee (für die Gebührenrechnung)
GEBUEHR_PRO_ORDER = 1.0     # Trade Republic: 1 € beim Kauf, 1 € beim Verkauf
SPREAD_PROZENT = 0.15       # geschätzter Kursaufschlag für Kauf + Verkauf zusammen
KRYPTO_SPREAD_PROZENT = 1.5  # Krypto: vorsichtig geschätzter Aufschlag (höher als bei Aktien)
NEWS_JE_DURCHLAUF = 60      # so viele Werte bekommen pro Durchlauf frische Nachrichten
STEUERSATZ = 0.26375        # Abgeltungsteuer + Soli, nur über dem Sparerpauschbetrag

MIN_FAELLE = 200            # so viele alte Fälle braucht eine Wahrscheinlichkeit
MIN_GEWINN_PROZENT = 0.30   # erwarteter Schnitt nach Gebühren, sonst keine Meldung
MIN_VORSPRUNG_PROZENT = 0.20  # so viel besser als "irgendwann kaufen"
MAX_IDEEN_PRO_TAG = 3
TEST_JE_MUSTER_PRO_TAG = 1  # Test-Depot: neue Test-Trades je Muster und Tag (ohne Handy-Meldung)
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
    # Weitere deutsche
    "ZAL.DE": "Zalando", "CON.DE": "Continental", "DB1.DE": "Deutsche Börse", "MRK.DE": "Merck",
    "BEI.DE": "Beiersdorf", "FRE.DE": "Fresenius", "HEI.DE": "Heidelberg Materials", "SY1.DE": "Symrise",
    "MTX.DE": "MTU", "PAH3.DE": "Porsche", "VNA.DE": "Vonovia", "CBK.DE": "Commerzbank",
    "ENR.DE": "Siemens Energy", "SHL.DE": "Siemens Healthineers", "HNR1.DE": "Hannover Rück",
    "QIA.DE": "Qiagen", "BNR.DE": "Brenntag", "PUM.DE": "Puma", "LHA.DE": "Lufthansa",
    "TKA.DE": "Thyssenkrupp", "HAG.DE": "Hensoldt", "EVK.DE": "Evonik",
    "FME.DE": "Fresenius Medical Care", "DTG.DE": "Daimler Truck",
    # Europa (in Euro)
    "MC.PA": "LVMH", "OR.PA": "L'Oréal", "TTE.PA": "TotalEnergies", "SAN.PA": "Sanofi",
    "AIR.PA": "Airbus", "SU.PA": "Schneider Electric", "AI.PA": "Air Liquide", "BNP.PA": "BNP Paribas",
    "CS.PA": "AXA", "RMS.PA": "Hermès", "SAF.PA": "Safran", "DG.PA": "Vinci", "KER.PA": "Kering",
    "ASML.AS": "ASML", "INGA.AS": "ING", "ADYEN.AS": "Adyen", "PHIA.AS": "Philips",
    "HEIA.AS": "Heineken", "PRX.AS": "Prosus", "ENEL.MI": "Enel", "ENI.MI": "Eni",
    "ISP.MI": "Intesa Sanpaolo", "UCG.MI": "UniCredit", "RACE.MI": "Ferrari", "ITX.MC": "Inditex",
    "IBE.MC": "Iberdrola", "SAN.MC": "Santander", "BBVA.MC": "BBVA", "NOKIA.HE": "Nokia",
    "ABI.BR": "Anheuser-Busch",
    # Weitere USA und große Auslandswerte
    "ORCL": "Oracle", "CRM": "Salesforce", "ADBE": "Adobe", "INTC": "Intel", "QCOM": "Qualcomm",
    "TXN": "Texas Instruments", "MU": "Micron", "AMAT": "Applied Materials", "LRCX": "Lam Research",
    "ARM": "Arm", "PLTR": "Palantir", "SNOW": "Snowflake", "CRWD": "CrowdStrike",
    "PANW": "Palo Alto Networks", "NOW": "ServiceNow", "IBM": "IBM", "CSCO": "Cisco", "UBER": "Uber",
    "ABNB": "Airbnb", "SHOP": "Shopify", "PYPL": "PayPal", "COIN": "Coinbase", "HOOD": "Robinhood",
    "MSTR": "MicroStrategy", "SPOT": "Spotify", "RBLX": "Roblox", "SNAP": "Snap", "PINS": "Pinterest",
    "BAC": "Bank of America", "WFC": "Wells Fargo", "GS": "Goldman Sachs", "MS": "Morgan Stanley",
    "MA": "Mastercard", "AXP": "American Express", "BLK": "BlackRock", "LLY": "Eli Lilly",
    "PFE": "Pfizer", "MRNA": "Moderna", "ABBV": "AbbVie", "UNH": "UnitedHealth", "MRK": "Merck & Co",
    "TMO": "Thermo Fisher", "HD": "Home Depot", "LOW": "Lowe's", "TGT": "Target", "SBUX": "Starbucks",
    "CMG": "Chipotle", "F": "Ford", "GM": "General Motors", "BA": "Boeing", "LMT": "Lockheed Martin",
    "RTX": "RTX", "CAT": "Caterpillar", "DE": "Deere", "GE": "GE Aerospace", "HON": "Honeywell",
    "UPS": "UPS", "FDX": "FedEx", "CVX": "Chevron", "COP": "ConocoPhillips", "NEE": "NextEra",
    "T": "AT&T", "VZ": "Verizon", "TMUS": "T-Mobile", "CMCSA": "Comcast", "SMCI": "Super Micro",
    "DELL": "Dell", "NVO": "Novo Nordisk", "TSM": "TSMC", "BABA": "Alibaba", "SONY": "Sony",
    "TM": "Toyota",
}

KRYPTO = {
    # Kryptowährungen in Euro
    "BTC-EUR": "Bitcoin", "ETH-EUR": "Ethereum", "XRP-EUR": "XRP", "SOL-EUR": "Solana", "BNB-EUR": "BNB",
    "ADA-EUR": "Cardano", "DOGE-EUR": "Dogecoin", "TRX-EUR": "Tron", "LINK-EUR": "Chainlink",
    "AVAX-EUR": "Avalanche", "DOT-EUR": "Polkadot", "LTC-EUR": "Litecoin", "BCH-EUR": "Bitcoin Cash",
    "XLM-EUR": "Stellar", "ATOM-EUR": "Cosmos", "AAVE-EUR": "Aave", "HBAR-EUR": "Hedera",
    "ETC-EUR": "Ethereum Classic",
}
AKTIEN.update(KRYPTO)

# Mehrdeutige Namen: so wird in Nachrichten gesucht (sonst träfe z. B. "Target" jedes "price target").
SUCHNAMEN = {"TGT": "Target Corp", "ARM": "Arm Holdings", "SNAP": "Snap Inc", "V": "Visa Inc", "F": "Ford Motor",
             "CON.DE": "Continental AG", "XLM-EUR": "Stellar XLM", "ATOM-EUR": "Cosmos ATOM", "TRX-EUR": "Tron TRX"}
