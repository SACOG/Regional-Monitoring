"""
check_encodings.py
------------------
Run pdffonts on each HPMS report and summarise the font encoding used.
Also does a quick spot-check: can pdftotext extract a recognisable number
from the Table 1 page?  That tells you whether the text layer is actually
usable regardless of what the encoding field says.

Usage:
    python check_encodings.py          # looks in current directory
    python check_encodings.py I:\path  # looks in specified directory
"""

import subprocess, re, sys, os
from pathlib import Path

# ── locate reports ──────────────────────────────────────────────────────────
folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
reports = sorted(folder.glob("hpms-*-prd*.pdf"))

if not reports:
    print(f"No hpms-*-prd*.pdf files found in {folder}")
    sys.exit(1)

YEAR_RE = re.compile(r"hpms-(\d{4})-")
NUM_RE  = re.compile(r"\d{2,3},\d{3}\.\d{2}")   # e.g. 73,703.16

print(f"{'Year':<6} {'Encoding':<14} {'identity-H':<12} {'T1 number found':<16} File")
print("-" * 75)

for path in reports:
    m = YEAR_RE.search(path.name)
    if not m:
        continue
    year = m.group(1)

    # ── pdffonts ────────────────────────────────────────────────────────────
    fonts_out = subprocess.run(
        ["pdffonts", str(path)], capture_output=True, text=True
    ).stdout

    has_identity_h = "Identity-H" in fonts_out

    # Summarise unique encoding types (skip header lines)
    encodings = set()
    for line in fonts_out.splitlines()[2:]:
        parts = line.split()
        if len(parts) >= 4:
            encodings.add(parts[3])   # 4th column is encoding
    enc_summary = ",".join(sorted(encodings)) if encodings else "?"

    # ── text-layer spot-check: find Table 1 page and look for a number ──────
    # Get page count
    info = subprocess.run(
        ["pdfinfo", str(path)], capture_output=True, text=True
    ).stdout
    page_m = re.search(r"Pages:\s+(\d+)", info)
    n_pages = int(page_m.group(1)) if page_m else 20

    # ── text-layer spot-check ──────────────────────────────────────────────
    # Look for the City Streets row and check whether the FIRST number on it
    # (maintained miles, ~70-80k) is a single clean token.  If it's split into
    # two tokens by a space (e.g. "73,703. 16"), the text layer is unreliable.
    t1_clean = False
    for p in range(8, min(15, n_pages + 1)):
        text = subprocess.run(
            ["pdftotext", "-layout", "-f", str(p), "-l", str(p), str(path), "-"],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        ).stdout
        for line in text.splitlines():
            if "CITY STREETS" in line.upper():
                # Extract tokens after the label
                toks = line.upper().replace("CITY STREETS", "").split()
                # First numeric token should be a clean maintained-miles value
                # (no trailing period, no lone digits)
                if toks and NUM_RE.fullmatch(toks[0]):
                    t1_clean = True
                break
        if t1_clean:
            break

    flag = "YES - clean" if t1_clean else "NO  - garbled"

    hi   = "YES" if has_identity_h else "no"

    print(f"{year:<6} {enc_summary:<14} {hi:<12} {flag:<16} {path.name}")
