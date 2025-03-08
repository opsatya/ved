# stock_chatbot/api_clients.py
import os
import sys
import importlib

VENV_5PAISA = "/home/ubuntu/env_5paisa"
VENV_KOTAKNEO = "/home/ubuntu/env_kotakneo"

def activate_venv(venv_path):
    site_packages = os.path.join(venv_path, "lib", "python3.10", "site-packages")
    if os.path.exists(site_packages):
        sys.path.insert(0, site_packages)
    else:
        print(f"[ERROR] Virtual environment not found: {venv_path}")
        sys.exit(1)

# Activate and import 5Paisa API
activate_venv(VENV_5PAISA)
try:
    py5paisa = importlib.import_module("py5paisa")
    FivePaisaClient = py5paisa.FivePaisaClient
except ModuleNotFoundError:
    print("[ERROR] py5paisa module not found. Install it inside env_5paisa.")
    sys.exit(1)

# Activate and import Kotak Neo API
activate_venv(VENV_KOTAKNEO)
try:
    neo_api_client = importlib.import_module("neo_api_client")
    NeoAPI = neo_api_client.NeoAPI
except ModuleNotFoundError:
    print("[ERROR] neo_api_client module not found. Install it inside env_kotakneo.")
    sys.exit(1)