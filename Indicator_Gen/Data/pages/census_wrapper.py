import sys
import os
from pathlib import Path

CENSUS_DIR = Path(__file__).parent.parent / "Census"

sys.path.insert(0, str(CENSUS_DIR))
os.chdir(CENSUS_DIR)

exec(
    open(CENSUS_DIR / "census_gui.py", encoding="utf-8").read(),
    {"__file__": str(CENSUS_DIR / "census_gui.py")}
)