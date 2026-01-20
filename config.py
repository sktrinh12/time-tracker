from pathlib import Path
import json

INFO_FILE = Path(__file__).parent / "info.json"

with open(INFO_FILE) as f:
    info = json.load(f)

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
INVOICE_DIR = BASE_DIR / "invoices"

DB_PATH = DATA_DIR / "time.db"

HOURLY_RATE = 105.00

DATA_DIR.mkdir(exist_ok=True)
INVOICE_DIR.mkdir(exist_ok=True)

CONSULTANT_NAME = info["CONSULTANT_NAME"]
CONSULTANT_EMAIL = info["CONSULTANT_EMAIL"]
CONSULTANT_ADDR = info["CONSULTANT_ADDR"]
CONSULTANT_PHONE = info.get("CONSULTANT_PHONE", "")

COMPANY_NAME = info["COMPANY_NAME"]
COMPANY_ADDR = info["COMPANY_ADDR"]
COMPANY_EMAIL = info["COMPANY_EMAIL"]
