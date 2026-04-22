# points to bls_app.py in BLS folder
import sys
import os
from pathlib import Path

BLS_DIR = Path(__file__).parent.parent / "BLS" / "config"

# Fix 1: let Python find pre, get, post
sys.path.insert(0, str(BLS_DIR))

# Fix 2: make relative paths inside bls_app.py resolve correctly
os.chdir(BLS_DIR)

exec(open(BLS_DIR / "bls_app.py", encoding="utf-8").read())