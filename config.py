from pathlib import Path
import json

INFO_FILE = Path(__file__).parent / "info.json"

with open(INFO_FILE) as f:
    info = json.load(f)

CLIENTS = info.get("clients", {})


def get_client(client_id: str):
    if client_id not in CLIENTS:
        raise ValueError(f"Client '{client_id}' not found in config.")
    return CLIENTS[client_id]


BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
INVOICE_DIR = BASE_DIR / "invoices"

DB_PATH = DATA_DIR / "time.db"


DATA_DIR.mkdir(exist_ok=True)
INVOICE_DIR.mkdir(exist_ok=True)

CONSULTANT_NAME = info["CONSULTANT_NAME"]
CONSULTANT_EMAIL = info["CONSULTANT_EMAIL"]
CONSULTANT_ADDR = info["CONSULTANT_ADDR"]
CONSULTANT_PHONE = info.get("CONSULTANT_PHONE", "")

COMPANY_NAME = info.get("COMPANY_NAME", "")
COMPANY_ADDR = info.get("COMPANY_ADDR", "")
COMPANY_EMAIL = info.get("COMPANY_EMAIL", "")
