import sys
from pathlib import Path

# Modules shared by name across data pipelines — must be cleared on every page load
PIPELINE_MODULES = ['get', 'post', 'pre', 'utils', 'helpers']

for mod in PIPELINE_MODULES:
    if mod in sys.modules:
        del sys.modules[mod]

BLS_DIR = Path(__file__).parent.parent / "BLS" / "config"
CENSUS_DIR = Path(__file__).parent.parent / "Census"

# Remove other pipeline dirs from sys.path to avoid wrong module being picked up
for path in [str(CENSUS_DIR)]:
    if path in sys.path:
        sys.path.remove(path)

# Insert BLS dir at front
if str(BLS_DIR) not in sys.path:
    sys.path.insert(0, str(BLS_DIR))
else:
    sys.path.remove(str(BLS_DIR))
    sys.path.insert(0, str(BLS_DIR))

exec(
    open(BLS_DIR / "bls_app.py", encoding="utf-8").read(),
    {"__file__": str(BLS_DIR / "bls_app.py")}
)