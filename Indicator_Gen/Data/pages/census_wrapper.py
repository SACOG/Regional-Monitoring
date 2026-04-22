import sys
from pathlib import Path

CENSUS_DIR = Path(__file__).parent.parent / "Census"

sys.path.insert(0, str(CENSUS_DIR))
# NO os.chdir() here

exec(
    open(CENSUS_DIR / "census_gui.py", encoding="utf-8").read(),
    {"__file__": str(CENSUS_DIR / "census_gui.py")}
)