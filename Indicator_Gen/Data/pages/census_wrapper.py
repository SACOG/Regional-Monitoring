import sys
from pathlib import Path

# Modules shared by name across data pipelines — must be cleared on every page load
PIPELINE_MODULES = ['get', 'post', 'pre', 'utils', 'helpers']

for mod in PIPELINE_MODULES:
    if mod in sys.modules:
        del sys.modules[mod]

CENSUS_DIR = Path(__file__).parent.parent / "Census"
BLS_DIR = Path(__file__).parent.parent / "BLS" / "config"

# Remove other pipeline dirs from sys.path to avoid wrong module being picked up
for path in [str(BLS_DIR)]:
    if path in sys.path:
        sys.path.remove(path)

# Insert Census dir at front
if str(CENSUS_DIR) not in sys.path:
    sys.path.insert(0, str(CENSUS_DIR))
else:
    sys.path.remove(str(CENSUS_DIR))
    sys.path.insert(0, str(CENSUS_DIR))

exec(
    open(CENSUS_DIR / "census_gui.py", encoding="utf-8").read(),
    {"__file__": str(CENSUS_DIR / "census_gui.py")}
)