import sys
from pathlib import Path

BLS_DIR = Path(__file__).parent.parent / "BLS" / "config"

sys.path.insert(0, str(BLS_DIR))
# NO os.chdir() here

exec(
    open(BLS_DIR / "bls_app.py", encoding="utf-8").read(),
    {"__file__": str(BLS_DIR / "bls_app.py")}
)