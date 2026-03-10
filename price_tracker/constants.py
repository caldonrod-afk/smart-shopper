import os
from pathlib import Path

# Use the smart-shopper directory for config files
BASE_DIR = Path(__file__).resolve().parent.parent
SAVE_PATH = str(BASE_DIR)
CONFIG_PATH = str(BASE_DIR / 'config.json')
PRODUCTS_PATH = str(BASE_DIR / 'products.json')
