"""
run_hpms.py — Caltrans HPMS extractor + batch driver (2001–2024).

All extraction logic is self-contained in this file; no separate
hpms_pre2012.py import is needed.

CONFIG
------
Set BASE_DIR and OUTPUT below, then run:
    python run_hpms.py

Handles three source formats transparently:
  * ZIP archives  — <page>.txt / <page>.jpeg per page (early Caltrans exports)
  * Real PDFs     — standard Caltrans PDFs processed with poppler + tesseract
  * Text dumps    — plain-text exports (rare; county totals only, no jurisdiction detail)

For PDF files, the script detects whether the text layer is reliably encoded
(WinAnsi / clean Identity-H) or garbled (spacing artifacts from some Identity-H
fonts). Clean years use the text layer as the primary source for Table 6 county
TOTAL rows (more accurate than OCR for those rows) and OCR as a fallback.
Garbled years (currently 2004 and 2010) use OCR as primary and the text layer
as a fallback after preprocessing.

Requires: pillow, pytesseract-free (shells out to tesseract), pandas, numpy,
          openpyxl.  System deps: tesseract-ocr, poppler-utils.

TODO
Libraries poppler and tesseract don't need specific steps to setup properly:
1) Open windows powershell (or similar conda terminal)
2) conda create -n hpms python=3.11 -y
3) conda activate hpms
4) conda install -c conda-forge numpy pandas openpyxl pillow poppler tesseract
5) Now in your IDE, make sure to connect to this specific conda environment
6) Run python file in terminal

You may need to run "conda init powershell" and "conda activate base" before as a step (0)
"""

# ============================================================================
# stdlib / third-party imports
# ============================================================================
import glob
import io
import os
import re
import subprocess
import shutil
import sys
import tempfile
from dataclasses import dataclass

from pathlib import Path
import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from PIL import Image

os.environ.setdefault("TESSDATA_PREFIX", os.path.join(sys.prefix, "share/tessdata"))

# ============================================================================
# CONFIG  ← edit these
# ============================================================================
BASE_DIR = r"I:\Projects\Josh\Regional Monitoring\Task 9. Collect new data\HPMS"
YEAR_MIN = 2001          # earliest year to process (inclusive)
YEAR_MAX = 2024          # latest year to process (inclusive)
OUTPUT   = "VMT_HPMS2024.xlsx"

# Which tables to extract.  Remove entries to skip them entirely (no OCR / parsing).
# Useful for targeted debugging, e.g. TABLES = {"T1"} to sweep all years for T1 only.
TABLES = {"T1", "T6", "MPO"}

FILE_GLOBS = [
    "hpms-*-prd-a11y.pdf",
    "hpms*prd*a11y.pdf",
    "hpms*prd*.pdf",
    "hpms*.pdf",
]

# ============================================================================
# DOMAIN CONSTANTS
# ============================================================================
SACOG = ["EL DORADO", "PLACER", "SACRAMENTO", "SUTTER", "YOLO", "YUBA"]

CA_COUNTIES = {
    "ALAMEDA", "ALPINE", "AMADOR", "BUTTE", "CALAVERAS", "COLUSA",
    "CONTRA COSTA", "DEL NORTE", "EL DORADO", "FRESNO", "GLENN", "HUMBOLDT",
    "IMPERIAL", "INYO", "KERN", "KINGS", "LAKE", "LASSEN", "LOS ANGELES",
    "MADERA", "MARIN", "MARIPOSA", "MENDOCINO", "MERCED", "MODOC", "MONO",
    "MONTEREY", "NAPA", "NEVADA", "ORANGE", "PLACER", "PLUMAS", "RIVERSIDE",
    "SACRAMENTO", "SAN BENITO", "SAN BERNARDINO", "SAN DIEGO", "SAN FRANCISCO",
    "SAN JOAQUIN", "SAN LUIS OBISPO", "SAN MATEO", "SANTA BARBARA",
    "SANTA CLARA", "SANTA CRUZ", "SHASTA", "SIERRA", "SISKIYOU", "SOLANO",
    "SONOMA", "STANISLAUS", "SUTTER", "TEHAMA", "TRINITY", "TULARE",
    "TUOLUMNE", "VENTURA", "YOLO", "YUBA",
}

NUM_RE    = re.compile(r"^-?\d[\d,]*\.\d{2}$")           # e.g. 1,055.63
TABLE_HDR = re.compile(r"^\s*table\s+(\d+(?:-\d+)?)\s*(\(continued\))?\s*$", re.I)

T1_COLS  = ["MAINT_MILES", "LANE_MILES", "AVMT_MILLIONS"]
MPO_COLS = ["MILES", "LANE_MILES", "DVMT_1000"]
COLS     = ["MM_RURAL", "MM_URBAN", "MM_TOTAL", "DVMT_RURAL", "DVMT_URBAN", "DVMT_TOTAL"]

# ============================================================================
# NAME NORMALIZATION
# ============================================================================
# Labels drift across years: Style changes ("Us Forest Service" vs "U.S. Forest Service")
# ,singular/plural ("State Highway"/"State Highways"), and renamings of the same row. The maps
# below collapse every variant to one canonical label so a metric trends as a
# single line. Applied after extraction; rows that collide onto the same
# (year, geography, label) after mapping are summed (handles the rare case of
# two source variants in one year — e.g. a split sub-row).

# Generic agency/style fixes, applied to both T1 facility types and T6
# jurisdictions. Keys are post-.title() forms as they appear in the extracted data.
_GENERIC_NAME_MAP = {
    "Us Forest Service":             "U.S. Forest Service",
    "Us Forest Ser Vice":            "U.S. Forest Service",
    "Us Bureau Of Reclamation":      "U.S. Bureau Of Reclamation",
    "Us Bureau Of Reclaimation":     "U.S. Bureau Of Reclamation",
    "Us Fish & Wildlife Service":    "U.S. Fish & Wildlife Service",
    "U.S. Fish And Wildlife":        "U.S. Fish & Wildlife Service",
    "U.S. Bureau Of Fish & Wildlife":"U.S. Fish & Wildlife Service",
    "State Highway":                 "State Highways",
    "Citru.S. Heights":              "Citrus Heights",   # OCR: "Citrus" → "Citru.S."
    "Cimies: Davis":                 "Davis",            # OCR garble
    "County (Onincorporated)":       "County (Unincorporated)",  # OCR: O→U
    "Loomis Town":                   "Loomis",           # 2015-2019 label drift
}

# T1-only facility-type fixes (layered on top of the generic map).
_T1_NAME_MAP = {
    "Other St Ate Agencies": "Other State Agencies",   # OCR: "State" → "St Ate"
    "Other State Agency":    "Other State Agencies",
    "County Road":           "County Roads",
    "Corps Of Engineers":    "Army Corps Of Engineers",
}


def check_pdfinfo():
    pdfinfo = shutil.which("pdfinfo")
    if pdfinfo is None:
        raise RuntimeError("pdfinfo was not found. Install Poppler or add it to PATH.")

def _canon_t1(label):
    """Canonical Table-1 facility-type label."""
    return _T1_NAME_MAP.get(label, _GENERIC_NAME_MAP.get(label, label))


def _canon_juris(county, juris):
    """Canonical Table-6 jurisdiction label within a county.

    The unincorporated-county balance is labeled three ways over time
    ("County (Unincorporated)" → "County" → "<Name> County"); all collapse to
    "<Name> County" so it trends as one row.

    County-specific label drift:
      SUTTER / "Yuba" (2015-2019) → "Yuba City"  (Yuba City was relabeled
      without the "City" suffix in some reports; collapse to the correct name).
    """
    j        = _GENERIC_NAME_MAP.get(juris, juris)
    canonical = f"{county.title()} County"
    if j in ("County (Unincorporated)", "County", canonical):
        return canonical
    # Sutter-specific: "Yuba" is a label-drift alias for "Yuba City"
    if county == "SUTTER" and j == "Yuba":
        return "Yuba City"
    return j


def normalize_names(T1, T6):
    """Apply canonical labels to the T1 and T6 frames, summing any rows that
    collide onto the same key after mapping. Returns (T1, T6)."""
    if not T1.empty:
        T1 = T1.copy()
        T1["FACILITY_TYPE"] = T1["FACILITY_TYPE"].map(_canon_t1)
        keys = ["YEAR", "ROWTYPE", "FACILITY_TYPE"]
        if T1.duplicated(keys).any():
            T1 = (T1.groupby(keys, as_index=False, sort=False)[T1_COLS]
                    .sum(min_count=1))
    if not T6.empty:
        T6 = T6.copy()
        T6["JURISDICTION"] = [
            _canon_juris(c, j) for c, j in zip(T6["COUNTY"], T6["JURISDICTION"])
        ]
        keys = ["YEAR", "COUNTY", "ROWTYPE", "JURISDICTION"]
        if T6.duplicated(keys).any():
            T6 = (T6.groupby(keys, as_index=False, sort=False)[COLS]
                    .sum(min_count=1))
    return T1, T6


# Verified manual corrections for cells the OCR path dropped, keyed by
# (YEAR, COUNTY, JURISDICTION) → {column: value}. Each value below was read
# directly from the source report and reconciles against the row's own total.
#   2004 Placer State Highways: the rural/urban maintained-mileage split was
#   dropped (total 155.98 and all DVMT came through fine). Source shows
#   RURAL 132.41 + URBAN 23.57 = 155.98, consistent with 2003 (132.44/23.57).
_T6_CELL_CORRECTIONS = {
    (2004, "PLACER", "State Highways"): {"MM_RURAL": 132.41, "MM_URBAN": 23.57},
}


def apply_known_corrections(T6):
    """Fill verified values for specific cells the extractor missed. Only writes
    a cell when it is currently null, so a correct re-extraction is never
    overwritten. Returns T6."""
    if T6.empty:
        return T6
    T6 = T6.copy()
    for (yr, county, juris), fixes in _T6_CELL_CORRECTIONS.items():
        mask = ((T6["YEAR"] == yr) & (T6["COUNTY"] == county)
                & (T6["JURISDICTION"] == juris))
        for col, val in fixes.items():
            cell = T6.loc[mask, col]
            if cell.isna().all():
                T6.loc[mask, col] = val
    return T6

# ============================================================================
# TEXT-LAYER ENCODING DETECTION
# ============================================================================
_NUM_CLEAN = re.compile(r"\d{2,3},\d{3}\.\d{2}")   # e.g. 73,703.16

def _text_layer_clean(path):
    """Return True if this PDF's text layer produces reliable numbers.

    The check rasterises nothing — it reads the City Streets row on the Table 1
    page via pdftotext and verifies that the FIRST token after the label is a
    single, properly-formatted maintained-miles value (e.g. '73,703.16').

    If the encoding is garbled (Identity-H spacing artifacts), that token will
    be split or missing and the function returns False.

    Known garbled years in the HPMS archive: 2004, 2010.
    """
    try:
        info = subprocess.run(
            ["pdfinfo", path], capture_output=True, text=True
        ).stdout
        m = re.search(r"Pages:\s+(\d+)", info)
        n_pages = int(m.group(1)) if m else 20

        for p in range(8, min(15, n_pages + 1)):
            text = subprocess.run(
                ["pdftotext", "-layout", "-f", str(p), "-l", str(p), path, "-"],
                capture_output=True, text=True,
                encoding="utf-8", errors="replace",
            ).stdout
            for line in text.splitlines():
                if "CITY STREETS" in line.upper():
                    toks = line.upper().replace("CITY STREETS", "").split()
                    return bool(toks and _NUM_CLEAN.fullmatch(toks[0]))
    except Exception:
        pass
    return True   # assume clean if detection fails


# ============================================================================
# REPORT LOADER  (format-agnostic)
# ============================================================================
class Report:
    """Uniform access to a year's report regardless of source format.

    Attributes
    ----------
    texts : dict[int, str]   page → full text (used for navigation)
    kind  : str              'archive' | 'pdf' | 'text'
    text_layer_clean : bool  True when pdftotext numbers are reliable
                             (always True for archive / text-dump kinds)
    """
    def __init__(self, texts, image_fn, kind, text_layer_clean=True):
        self.texts            = texts
        self._image_fn        = image_fn
        self.kind             = kind
        self.text_layer_clean = text_layer_clean

    def image(self, page):
        return self._image_fn(page)


def open_report(path):

    # ── PDF backend (poppler) ────────────────────────────────────────────────

    info = subprocess.run(
        ["pdfinfo", path],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    ).stdout
    m = re.search(r"Pages:\s+(\d+)", info)
    if not m:
        raise ValueError(f"Unrecognized report format: {path}")
    npages = int(m.group(1))

    texts = {}
    for p in range(1, npages + 1):
        texts[p] = subprocess.run(
            ["pdftotext", "-layout", "-f", str(p), "-l", str(p), path, "-"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        ).stdout

    def _img_pdf(p, _path=path):
        yr_match = re.search(r"(19|20)\d{2}", os.path.basename(_path))
        yr_str   = yr_match.group() if yr_match else "data"
        prefix   = os.path.join(tempfile.gettempdir(), f"hpms_{yr_str}_pg{p}_")
        for old in glob.glob(prefix + "*.png"):
            try: os.remove(old)
            except: pass
        res   = subprocess.run(
            ["pdftoppm", "-png", "-r", "200", "-f", str(p), "-l", str(p), _path, prefix],
            capture_output=True,
        )
        files = sorted(glob.glob(prefix + "*.png"))
        if not files:
            raise RuntimeError(f"pdftoppm produced no PNGs\n{res.stderr}")
        img = Image.open(files[-1]).convert("L")
        img.load()
        for f in files:
            try: os.remove(f)
            except: pass
        return img

    clean = _text_layer_clean(path)
    return Report(texts, _img_pdf, "pdf", text_layer_clean=clean)


# ============================================================================
# NAVIGATION  (text layer)
# ============================================================================
def table_spans(texts):
    """{table_id -> first_page} from standalone 'TABLE n' header lines."""
    starts = {}
    for p in sorted(texts):
        nonempty = [ln.replace("\r", "") for ln in texts[p].splitlines() if ln.strip()]
        for ln in nonempty[:3]:
            mm = TABLE_HDR.match(ln)
            if mm:
                starts.setdefault(mm.group(1), p)
                break
    return starts


def table6_range(texts):
    """(start, end_exclusive) page span of Table 6."""
    starts = table_spans(texts)
    if "6" not in starts:
        raise ValueError("Table 6 header not found")
    f6    = starts["6"]
    after = [p for t, p in starts.items() if p > f6]
    return f6, (min(after) if after else max(texts) + 1)


def county_pages(texts, county, span):
    """Pages within Table 6 where `county` heads a row."""
    lo, hi = span
    pages  = []
    pat    = re.compile(rf"^\s*{re.escape(county)}\b")
    anti   = re.compile(rf"^\s*{re.escape(county)}[A-Z]")
    for p in range(lo, hi):
        if p not in texts:
            continue
        for raw in texts[p].splitlines():
            ln = raw.replace("\r", "")
            if pat.match(ln) and not anti.match(ln):
                pages.append(p)
                break
    return pages


def find_table_page(texts, *, number=None, title_keywords=None):
    """Locate a table page by number and/or title keywords."""
    if number is not None:
        starts = table_spans(texts)
        if number in starts:
            return starts[number]
    if title_keywords:
        for p in sorted(texts):
            head = " ".join(ln for ln in texts[p].splitlines()[:5]).upper()
            if all(k.upper() in head for k in title_keywords):
                return p
    return None


# ============================================================================
# OCR + COLUMN RECONSTRUCTION
# ============================================================================
@dataclass
class Tok:
    text: str
    x0: int
    x1: int
    yc: float


def ocr_tokens(img, scale=2):
    """Run tesseract on `img` and return word-box tokens."""
    if img.height > img.width:                       # some archives store pages rotated
        img = img.transpose(Image.Transpose.ROTATE_90)
    big = img.resize((img.width * scale, img.height * scale), Image.LANCZOS)
    buf = io.BytesIO(); big.save(buf, format="PNG"); buf.seek(0)
    res = subprocess.run(
        ["tesseract", "stdin", "stdout", "--psm", "6", "-c", "tessedit_create_tsv=1"],
        input=buf.read(), capture_output=True,
    )
    toks = []
    for line in res.stdout.decode("utf-8", "replace").splitlines()[1:]:
        c = line.split("\t")
        if len(c) < 12 or not c[11].strip():
            continue
        left, top, w, h = map(int, (c[6], c[7], c[8], c[9]))
        toks.append(Tok(c[11].strip(), left, left + w, top + h / 2))
    return toks


def learn_columns(num_toks, k=6):
    """Cluster numeric token right-edges into k column centres (gap split)."""
    edges = sorted(t.x1 for t in num_toks)
    if len(edges) < k:
        return None
    gaps  = sorted(((edges[i+1] - edges[i], i) for i in range(len(edges)-1)),
                   reverse=True)[:k-1]
    cuts  = sorted(i for _, i in gaps)
    bands, start = [], 0
    for cut in cuts + [len(edges) - 1]:
        seg = edges[start:cut+1]
        bands.append(sum(seg) / len(seg))
        start = cut + 1
    return bands


def group_rows(toks, ytol=14):
    """Group tokens into visual rows by vertical centre."""
    rows, cur, last = [], [], None
    for t in sorted(toks, key=lambda t: t.yc):
        if last is not None and t.yc - last > ytol:
            rows.append(cur); cur = []
        cur.append(t); last = t.yc
    if cur:
        rows.append(cur)
    return rows


def assign_six(num_toks, bands):
    """Place tokens into 6 column slots by nearest band (right edge)."""
    vals = [np.nan] * 6
    for t in num_toks:
        j    = int(np.argmin([abs(t.x1 - b) for b in bands]))
        v    = float(t.text.replace(",", ""))
        vals[j] = v if np.isnan(vals[j]) else vals[j]
    return vals


# ============================================================================
# PAGE PARSING  (OCR path — Table 6)
# ============================================================================
def parse_page(img, year, seed_county=None):
    """Parse one Table 6 page via OCR."""
    toks  = ocr_tokens(img)
    num   = [t for t in toks if NUM_RE.match(t.text)]
    bands = learn_columns(num)
    if not bands:
        return pd.DataFrame(columns=["YEAR", "COUNTY", "JURISDICTION", "ROWTYPE", *COLS])
    first_band     = min(bands) - 60
    rows_out, county, section = [], seed_county, None

    for row in group_rows(toks):
        nums   = [t for t in row if NUM_RE.match(t.text)]
        labels = [t for t in row if t.x1 < first_band and not NUM_RE.match(t.text)]
        label  = " ".join(t.text for t in sorted(labels, key=lambda t: t.x0)).strip()
        U      = label.upper()

        if re.search(r"\bSTATEWIDE\b", U):
            county = None; continue

        mtot = re.match(r"^(.*?)\s+TOTAL\b", U)
        if mtot and mtot.group(1).strip() in CA_COUNTIES and nums:
            c = mtot.group(1).strip()
            rows_out.append([year, c, f"{c} TOTAL", "TOTAL", *assign_six(nums, bands)])
            continue

        base = U.replace("(CONTINUED)", "").strip()
        if base in CA_COUNTIES and not nums:
            county, section = base, None; continue

        msec = re.match(r"^(CITIES|OTHER)\s*:?\s*(.*)$", U)
        if msec:
            section = "CITY" if msec.group(1) == "CITIES" else "OTHER"
            label   = msec.group(2).strip()
            if not label: continue

        if nums and label:
            rows_out.append([year, county, label.title(),
                             section or "OTHER", *assign_six(nums, bands)])

    return pd.DataFrame(
        rows_out, columns=["YEAR", "COUNTY", "JURISDICTION", "ROWTYPE", *COLS]
    )


# ============================================================================
# TEXT-LAYER NUMBER PREPROCESSING
# ============================================================================
_LOOSE_NUM      = re.compile(r"^-?\d[\d,]*(?:\.\d*)?$")
_TRAILING_COMMA = re.compile(r",$")


def _fix_number_spaces(text):
    """Collapse spacing artifacts from Identity-H PDF encoding.

    Some fonts insert single spaces within numbers, e.g. '73,703. 16' or
    '65,324.2 1'.  In pdftotext -layout output legitimate column gaps use
    multiple spaces, so collapsing only single spaces is safe.
    Also strips underline-formatting underscores and fixes l→1 substitutions.
    """
    text = text.replace("_", "")
    for _ in range(6):
        prev = text
        text = re.sub(r"(\d[\d,]*)\. (\d)", r"\1.\2", text)   # space after decimal
        text = re.sub(r"(\d) (\d[\d,]*)",   r"\1\2",  text)   # space mid-digits
        text = re.sub(r"(\d), (\d)",        r"\1,\2", text)   # space after comma
        if text == prev:
            break
    text = re.sub(r"(?<=\d)l(?=\d)", "1", text)               # l → 1 between digits
    return text


def _split_row(line):
    """(label, [float, ...]) — splits trailing numeric tokens from a text line."""
    toks = line.split()
    # Rejoin split decimals: "73,703." + "16" → "73,703.16"
    merged, i = [], 0
    while i < len(toks):
        t = toks[i]
        if (t.endswith(".") and re.match(r"^\d[\d,]*\.$", t)
                and i + 1 < len(toks) and re.match(r"^\d+$", toks[i+1])):
            merged.append(t + toks[i+1]); i += 2; continue
        merged.append(t); i += 1
    toks = merged

    vals, rest = [], []
    for t in reversed(toks):
        if _LOOSE_NUM.match(t) and not _TRAILING_COMMA.search(t):
            vals.insert(0, float(t.replace(",", "")))
        else:
            rest = toks[:toks.index(t) + 1]
            break
    else:
        rest = []
    return " ".join(rest).strip(), vals


# ============================================================================
# TEXT-LAYER TABLE PARSERS
# ============================================================================
def _slice_table(blob, start_re, stop_re):
    m = re.search(start_re, blob, re.I)
    if not m:
        return ""
    tail = blob[m.start():]
    s    = re.search(stop_re, tail, re.I)
    return tail[:s.start()] if s else tail


def parse_table1_from_text(blob, year):
    """Parse Table 1 from a text blob (text-dump or pdftotext page).

    Row classification (TOP vs SUB) feeds the Statewide tab, which sums TOP rows
    to the statewide total. The hierarchy is not stable across years: a label
    like STATE PARK SERVICE is a standalone top-level category in some years and
    a child of OTHER STATE AGENCIES in others, and indentation is present only in
    the clean pdftotext format. Neither position nor name is reliable on its own.

    The one invariant that always holds is arithmetic: a parent row's value equals
    the sum of the child rows printed beneath it, and the top-level rows sum to the
    printed TOTAL. So we parse every row flat, then resolve TOP/SUB by reconciling
    against that structure: a row is a parent when a contiguous run of the rows
    that follow sums (within tolerance) to its value; those summed rows are its
    children (SUB). Everything else is TOP. This is format-agnostic and
    self-correcting — it produced the right answer whether the source indents
    children or not, and whether a category appears once or twice.
    """
    fixed = _fix_number_spaces(blob)
    seg   = _slice_table(fixed, r"CITY STREETS\s+\d", r"\bTABLE 2\b")
    if not seg:
        return pd.DataFrame(columns=["YEAR", "FACILITY_TYPE", "ROWTYPE", *T1_COLS])

    TOTAL_RE = re.compile(r"^(STATEWIDE\s+)?TOTAL\b", re.I)

    # ── pass 1: flat parse of every data row, in order ────────────────────────
    raw_rows, total_row = [], None
    for raw in seg.splitlines():
        label, vals = _split_row(raw.replace("\r", "").strip())
        label = re.sub(r"\s*\*+\s*$", "", label).strip()
        if not label or len(vals) < 3:
            continue
        v3 = vals[-3:]
        if TOTAL_RE.match(label):
            total_row = (label, v3)
            break
        raw_rows.append([label, v3])           # [label, [mm, lane, avmt]]

    # ── pass 2: mark children via the parent = sum-of-following-run invariant ──
    # A row is a parent if the immediately following contiguous rows sum to it on
    # MAINT_MILES (the column least affected by rounding). Those rows are SUB.
    rowtype = ["TOP"] * len(raw_rows)
    TOL = 0.5
    i = 0
    while i < len(raw_rows):
        parent_mm = raw_rows[i][1][0]
        run, j = 0.0, i + 1
        consumed = 0
        # accumulate following rows until we hit the parent's value (a child run)
        while j < len(raw_rows) and run < parent_mm - TOL:
            run += raw_rows[j][1][0]
            consumed += 1
            j += 1
        if consumed and abs(run - parent_mm) <= TOL:
            for k in range(i + 1, i + 1 + consumed):
                rowtype[k] = "SUB"
            i = j                              # skip past the consumed children
        else:
            i += 1

    recs = [{"YEAR": year, "FACILITY_TYPE": lab.title(), "ROWTYPE": rt,
             "MAINT_MILES": v[0], "LANE_MILES": v[1], "AVMT_MILLIONS": v[2]}
            for (lab, v), rt in zip(raw_rows, rowtype)]
    if total_row:
        lab, v = total_row
        recs.append({"YEAR": year, "FACILITY_TYPE": "Total", "ROWTYPE": "TOTAL",
                     "MAINT_MILES": v[0], "LANE_MILES": v[1], "AVMT_MILLIONS": v[2]})

    return pd.DataFrame(recs)


def _find_mpo_text_blob(rep):
    """Return (text_blob, page_or_None) for the MPO table."""
    if rep.kind == "text":
        blob = rep.texts[0]
        seg  = _slice_table(
            blob,
            r"MPO\s+Miles\s+Lane\s+Miles",
            r"California.{0,5}s\s+MPOs|TABLE 12|AMBAG\s+Association",
        )
        return seg, None
    for p in sorted(rep.texts, reverse=True):
        head = " ".join(rep.texts[p].splitlines()[:8]).upper()
        if "MPO" in head and ("LANE MILES" in head or "DVMT" in head):
            return rep.texts[p], p
    return "", None


def parse_mpo_from_text(text, year):
    """Parse the MPO table from a text blob."""
    TOTAL_RE = re.compile(r"\bTotals?\b|\bSTATEWIDE\b|\bGrand\s+Total\b", re.I)
    STOP_RE  = re.compile(r"California.{0,5}s\s+MPOs|^AMBAG\s+Association|TABLE 12", re.I)
    recs     = []

    for ln in text.splitlines():
        ln = ln.replace("\r", "").strip()
        if STOP_RE.search(ln):
            break
        label, vals = _split_row(ln)
        if len(vals) < 3:
            continue
        v3       = vals[-3:]
        is_total = bool(TOTAL_RE.search(label)) or (not label and len(vals) >= 3)
        if not label and not is_total:
            continue
        recs.append({"YEAR": year, "MPO": label or "TOTAL",
                     "ROWTYPE": "TOTAL" if is_total else "DETAIL",
                     "MILES": v3[0], "LANE_MILES": v3[1], "DVMT_1000": v3[2]})
        if is_total:
            break

    if not recs:
        return pd.DataFrame(columns=["YEAR", "MPO", "ROWTYPE", *MPO_COLS])

    df          = pd.DataFrame(recs)
    detail_mask = df.ROWTYPE == "DETAIL"
    detail_dvmt = df.loc[detail_mask, "DVMT_1000"]
    if len(detail_dvmt) and detail_dvmt.max() > 1_000_000:
        df.loc[detail_mask, "DVMT_1000"] /= 1000.0
    return df


def parse_table6_totals_from_text(blob, year, counties=SACOG):
    """Extract Table 6 county TOTAL rows from a plain-text dump."""
    TOT_RE = re.compile(
        r"^({c})\s+TOTAL\b(.*)$".format(c="|".join(re.escape(c) for c in counties)),
        re.I | re.MULTILINE,
    )
    rows = []
    for mm in TOT_RE.finditer(blob):
        county = mm.group(1).upper()
        _, vals = _split_row(mm.group(0))
        if len(vals) >= 6:
            mm_r, mm_u, mm_t, dv_r, dv_u, dv_t = vals[:6]
        elif len(vals) == 3:
            mm_r = mm_u = dv_r = dv_u = float("nan")
            mm_t, dv_r, dv_t = vals; dv_u = float("nan")
        else:
            continue
        rows.append({"YEAR": year, "COUNTY": county, "JURISDICTION": f"{county} TOTAL",
                     "ROWTYPE": "TOTAL",
                     "MM_RURAL": mm_r, "MM_URBAN": mm_u, "MM_TOTAL": mm_t,
                     "DVMT_RURAL": dv_r, "DVMT_URBAN": dv_u, "DVMT_TOTAL": dv_t})
    return pd.DataFrame(rows)


def _parse_t6_totals_from_pdf_text(rep, year, counties=SACOG):
    """Thin wrapper kept for backward compatibility — delegates to full parser."""
    df = _parse_t6_full_from_pdf_text(rep, year, counties)
    return df[df.ROWTYPE == "TOTAL"].copy() if len(df) else df


def _parse_t6_full_from_pdf_text(rep, year, counties=SACOG, span=None):
    """Parse the complete Table 6 (jurisdiction detail + county TOTAL rows)
    from the pdftotext text layer for real PDFs with clean encoding.

    The text layer preserves column alignment so all 6 values are present
    on every row.  This is more reliable than OCR for clean PDFs.

    When `span` is provided (start, end_exclusive page numbers), only pages
    within that range are scanned.  This prevents pre-Table-6 sections from
    matching county headers and absorbing statewide summary data into SACOG
    county rows (observed in 2008 urbanised-area tables).

    Row assignment for variable column counts
    -----------------------------------------
    6 values → [MM_R, MM_U, MM_T, DV_R, DV_U, DV_T]
    4 values → rural columns blank (zero); [MM_U, MM_T, DV_U, DV_T]
    2 values → only TOTAL columns; [MM_T, DV_T]
    other    → skip (header / page-number line)
    """
    NAN = float("nan")

    COUNTY_RE = re.compile(
        r"^({c})\s*$".format(c="|".join(re.escape(c) for c in counties)),
        re.I,
    )
    TOT_RE = re.compile(
        r"^(?:\d+\s+)?({c})\s+TOTAL\b".format(c="|".join(re.escape(c) for c in counties)),
        re.I,
    )
    SEC_RE = re.compile(r"^(Cities|Other)\s*:\s*(.*)", re.I)

    def _assign(vals):
        """Map a list of 2 / 4 / 6 numeric values to the 6 column slots."""
        if len(vals) >= 6:
            return list(vals[:6])
        if len(vals) == 4:                        # rural columns were blank
            mm_u, mm_t, dv_u, dv_t = vals
            return [NAN, mm_u, mm_t, NAN, dv_u, dv_t]
        if len(vals) == 2:                        # only TOTAL columns
            mm_t, dv_t = vals
            return [NAN, NAN, mm_t, NAN, NAN, dv_t]
        return None

    rows     = []
    county   = None
    section  = None
    seen_tot = set()

    pages = sorted(rep.texts)
    if span is not None:
        lo, hi = span
        pages = [p for p in pages if lo <= p < hi]

    for p in pages:
        for raw in rep.texts[p].splitlines():
            ln = raw.replace("\r", "").strip()
            if not ln:
                continue

            # ── county TOTAL row ────────────────────────────────────────────
            m = TOT_RE.match(ln)
            if m:
                cty = m.group(1).upper()
                if cty in seen_tot:
                    # Duplicate total (map-page label or continuation header):
                    # reset boundary without emitting a second row.
                    county = None; section = None
                    continue
                fixed = _fix_number_spaces(ln[m.end():])   # slice past "…TOTAL" to skip the leading page-number token
                vals  = [float(t.replace(",", ""))
                         for t in fixed.split()
                         if _LOOSE_NUM.match(t) and not _TRAILING_COMMA.search(t)]
                assigned = _assign(vals)
                if assigned and len(vals) >= 5:
                    seen_tot.add(cty)
                    rows.append({
                        "YEAR": year, "COUNTY": cty,
                        "JURISDICTION": f"{cty} TOTAL", "ROWTYPE": "TOTAL",
                        "MM_RURAL": assigned[0], "MM_URBAN": assigned[1],
                        "MM_TOTAL": assigned[2], "DVMT_RURAL": assigned[3],
                        "DVMT_URBAN": assigned[4], "DVMT_TOTAL": assigned[5],
                    })
                county = None; section = None
                continue

            # ── county header (bare name, no numbers) ────────────────────────
            # If this county's total has already been emitted, this line is a
            # map-page title or stale running header — close boundary, don't
            # reopen the county (that would absorb the next county's data).
            m = COUNTY_RE.match(ln)
            if m:
                cty_hdr = m.group(1).upper()
                if cty_hdr in seen_tot:
                    county = None; section = None   # map-page title: close, don't reopen
                else:
                    county = cty_hdr
                    section = None
                continue

            if county is None:
                continue

            # ── section label (Cities: / Other:) ────────────────────────────
            m = SEC_RE.match(ln)
            if m:
                section = "CITY" if m.group(1).upper() == "CITIES" else "OTHER"
                ln = m.group(2).strip()
                if not ln:
                    continue

            # ── jurisdiction detail row ──────────────────────────────────────
            fixed = _fix_number_spaces(ln)
            label, vals = _split_row(fixed)
            label = label.title()
            label = re.sub(r"^\d+\s+", "", label)   # strip stray page-number prefix
            if not label or not vals:
                continue
            assigned = _assign(vals)
            if assigned is None:
                continue
            rows.append({
                "YEAR": year, "COUNTY": county,
                "JURISDICTION": label, "ROWTYPE": section or "OTHER",
                "MM_RURAL": assigned[0], "MM_URBAN": assigned[1],
                "MM_TOTAL": assigned[2], "DVMT_RURAL": assigned[3],
                "DVMT_URBAN": assigned[4], "DVMT_TOTAL": assigned[5],
            })

    return pd.DataFrame(rows) if rows else pd.DataFrame(
        columns=["YEAR", "COUNTY", "JURISDICTION", "ROWTYPE", *COLS]
    )


# ============================================================================
# ARITHMETIC REPAIR
# ============================================================================
def repair_totals(df):
    """Repair MM/DVMT rural-urban-total arithmetic inconsistencies.

    Cases handled
    -------------
    1. TOTAL is NaN and both splits present      → TOTAL = RURAL + URBAN
    2. TOTAL < max(RURAL, URBAN)  (clear misread) → TOTAL = RURAL + URBAN
    3. RURAL is NaN, URBAN + TOTAL present        → RURAL = TOTAL - URBAN
    4. URBAN is NaN, RURAL + TOTAL present        → URBAN = TOTAL - RURAL
    """
    if df is None or len(df) == 0:
        return df
    df = df.copy()
    for grp in ("MM", "DVMT"):
        r_col, u_col, t_col = f"{grp}_RURAL", f"{grp}_URBAN", f"{grp}_TOTAL"
        if not all(c in df.columns for c in [r_col, u_col, t_col]):
            continue
        r, u, t = df[r_col], df[u_col], df[t_col]

        bad = (t.isna()
               | (t.notna() & r.notna() & u.notna() & (t < r.fillna(0).clip(lower=0)))
               | (t.notna() & r.notna() & u.notna() & (t < u.fillna(0).clip(lower=0))))
        mask = bad & r.notna() & u.notna()
        df.loc[mask, t_col] = df.loc[mask, r_col] + df.loc[mask, u_col]

        r, u, t = df[r_col], df[u_col], df[t_col]          # refresh
        mask_r = r.isna() & u.notna() & t.notna() & (t >= u)
        df.loc[mask_r, r_col] = df.loc[mask_r, t_col] - df.loc[mask_r, u_col]

        r = df[r_col]
        mask_u = u.isna() & r.notna() & t.notna() & (t >= r)
        df.loc[mask_u, u_col] = df.loc[mask_u, t_col] - df.loc[mask_u, r_col]

    return df


# ============================================================================
# VALIDATION
# ============================================================================
def validate(df, tol=0.02):
    """Return (critical_list, warning_list).

    critical → county detail sum ≠ reported TOTAL  (must be zero to ship)
    warning  → single-row rural+urban ≠ total  (split may be wrong, total can still be right)
    """
    if df is None or len(df) == 0 or "YEAR" not in df.columns:
        return [], []
    critical, warnings = [], []
    for _, r in df.iterrows():
        for grp in ("MM", "DVMT"):
            ru  = np.nan_to_num(r[f"{grp}_RURAL"]) + np.nan_to_num(r[f"{grp}_URBAN"])
            tot = r[f"{grp}_TOTAL"]
            if pd.notna(tot) and abs(ru - tot) > max(tol, tol * abs(tot)):
                warnings.append(
                    f"{r['YEAR']} {r['COUNTY']}/{r['JURISDICTION']}: "
                    f"{grp} rural+urban {ru:.2f} != total {tot:.2f}")
    for (yr, cty), g in df.groupby(["YEAR", "COUNTY"]):
        tot = g[g.ROWTYPE == "TOTAL"]
        det = g[g.ROWTYPE != "TOTAL"]
        if len(tot) and len(det):
            for col in ("MM_TOTAL", "DVMT_TOTAL"):
                s, rep_val = det[col].sum(), tot[col].iloc[0]
                if pd.notna(rep_val) and abs(s - rep_val) > max(0.05, tol * abs(rep_val)):
                    critical.append(
                        f"{yr} {cty}: detail {col} {s:,.2f} != reported {rep_val:,.2f}")
    return critical, warnings


def validate_simple(df, value_cols, total_rowtype="TOTAL", detail_rowtypes=None):
    """Validate a flat table (Table 1 or MPO): detail rows must sum to total."""
    if df is None or len(df) == 0 or "ROWTYPE" not in df.columns:
        return ["empty or missing ROWTYPE column"]
    crit = []
    tot  = df[df.ROWTYPE == total_rowtype]
    if not len(tot):
        return [f"no '{total_rowtype}' row detected"]
    det  = (df[df.ROWTYPE.isin(detail_rowtypes)] if detail_rowtypes
            else df[df.ROWTYPE != total_rowtype])
    for col in value_cols:
        s, rep_val = det[col].sum(), tot[col].iloc[0]
        if pd.notna(rep_val) and abs(s - rep_val) > max(0.05, 0.02 * abs(rep_val)):
            crit.append(f"{col}: detail {s:,.2f} != reported total {rep_val:,.2f}")
    return crit


# ============================================================================
# EXTRACTION FUNCTIONS
# ============================================================================
def extract_table1(rep, year):
    """Extract Table 1 (statewide maintained miles + AVMT by jurisdiction type)."""

    # Text-dump backend
    if rep.kind == "text":
        df = parse_table1_from_text(rep.texts[0], year)
        print(f"\n[TEXT] --- Table 1 for {year} ({len(df)} rows) ---")
        for _, r in df.iterrows():
            print(f"  {r['ROWTYPE']:<6} {r['FACILITY_TYPE']:<40} {r['MAINT_MILES']:>12,.2f}")
        return df

    p         = find_table_page(rep.texts, number="1")
    page_blob = rep.texts.get(p, "") if p else ""
    print(f"TABLE 1 PAGE = {p}")

    # Try text layer first (reliable for most years; _fix_number_spaces handles garbled ones)
    df = parse_table1_from_text(_fix_number_spaces(page_blob), year)
    if len(df) and (df.ROWTYPE == "TOTAL").any():
        print(f"\n[TEXT] --- Table 1 for {year} ({len(df)} rows, via text layer) ---")
        for _, r in df.iterrows():
            print(f"  {r['ROWTYPE']:<6} {r['FACILITY_TYPE']:<40} {r['MAINT_MILES']:>12,.2f}")
        return df

    # OCR fallback
    rows = parse_simple(rep.image(p), 3, r"^TOTAL$")
    if not rows:
        print(f"[WARN] T1 {year}: text layer garbled and OCR returned nothing.")
        return pd.DataFrame(columns=["YEAR", "FACILITY_TYPE", "ROWTYPE", *T1_COLS])
    levels = _indent_levels(rows)
    recs   = [{"YEAR": year, "FACILITY_TYPE": lab.title(), "ROWTYPE": lvl,
               **dict(zip(T1_COLS, vals))}
              for (lab, vals, _, _), lvl in zip(rows, levels)]
    return pd.DataFrame(recs)


def extract_table6(rep, year, counties=SACOG):
    """Extract Table 6 (maintained miles + DVMT by county/jurisdiction).

    Strategy depends on source format and encoding quality:

    text-dump → text parser (county totals only; detail rows are column-major)
    archive   → OCR (text layer drops DVMT columns in these zip exports)
    pdf clean → text layer primary for TOTAL rows (accurate digit values);
                OCR for jurisdiction detail rows
    pdf garbled → OCR primary; text-layer TOTAL rows used only as supplement
                  when OCR produces no result
    """
    # ── text-dump ────────────────────────────────────────────────────────────
    if rep.kind == "text":
        df = parse_table6_totals_from_text(rep.texts[0], year, counties)
        if len(df):
            print(f"\n[TEXT] --- Table 6 county totals for {year} (text-dump) ---")
            for _, r in df.iterrows():
                print(f"  {r['COUNTY']}: MM={r['MM_TOTAL']:,.2f}  DVMT={r['DVMT_TOTAL']:,.2f}")
            print("  NOTE: jurisdiction detail not available from text-dump format.")
        return repair_totals(df), None, {}

    # ── archive or pdf: OCR jurisdiction detail ───────────────────────────────
    texts = rep.texts
    span  = table6_range(texts)
    loc   = {c: county_pages(texts, c, span) for c in counties}
    pages = sorted({p for ps in loc.values() for p in ps})
    frames = [parse_page(rep.image(p), year, seed_county=None) for p in pages]
    df     = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    # ── PDF: for clean encoding, parse the full T6 from the text layer ──────
    # pdftotext -layout preserves all 6 columns cleanly; OCR can misread digits.
    # For garbled encoding, OCR is primary and text-layer fills gaps only.
    if rep.kind == "pdf":
        if rep.text_layer_clean:
            # Parse detail + TOTAL from text layer — replaces OCR entirely
            df = _parse_t6_full_from_pdf_text(rep, year, counties, span=span)
        else:
            # Garbled encoding: OCR detail rows + text-layer as fallback for TOTAL
            text_totals = _parse_t6_totals_from_pdf_text(rep, year, counties)
            if not len(df) and len(text_totals):
                df = text_totals

    if len(df):
        df = df[df["COUNTY"].isin(counties)].reset_index(drop=True)
        print(f"\n[DEBUG] --- Table 6 for {year} ---")
        print(f"{'County':<15} | {'Jurisdiction':<30} | {'Type':<8} | "
              f"[MM_RUR, MM_URB, MM_TOT, DVMT_RUR, DVMT_URB, DVMT_TOT]")
        print("-" * 115)
        for _, r in df.iterrows():
            m = [r[c] for c in COLS]
            fmt = [f"{v:,.2f}" if pd.notna(v) else "NaN" for v in m]
            print(f"{r['COUNTY']:<15} | {r['JURISDICTION']:<30} | {r['ROWTYPE']:<8} | {fmt}")
        print("-" * 115)

    return repair_totals(df), span, loc


def extract_mpo(rep, year):
    """Extract the MPO / by-region table."""
    text_blob, p = _find_mpo_text_blob(rep)
    if not text_blob.strip():
        print(f"TABLE MPO PAGE DETECTED = None — not found in {year}")
        return pd.DataFrame(columns=["YEAR", "MPO", "ROWTYPE", *MPO_COLS]), None

    print(f"TABLE MPO PAGE DETECTED = {p}")
    df = parse_mpo_from_text(text_blob, year)
    print(f"\n[TEXT] --- Table 9 (MPO) for {year} ---")
    print(f"{'Row Type':<10} | {'MPO Region':<35} | ['Miles', 'Lane Miles', 'DVMT (1000s)']")
    print("-" * 90)
    for _, r in df.iterrows():
        print(f"{r['ROWTYPE']:<10} | {r['MPO']:<35} | "
              f"[{r['MILES']:,.2f}, {r['LANE_MILES']:,.2f}, {r['DVMT_1000']:,.2f}]")
    print("-" * 90)
    return df, p


# ============================================================================
# SIMPLE TABLE PARSING (Table 1 OCR fallback)
# ============================================================================
def parse_simple(img, ncols, total_re):
    """Parse a flat 'label + ncols numbers' table via OCR."""
    toks  = ocr_tokens(img)
    num   = [t for t in toks if NUM_RE.match(t.text)]
    bands = learn_columns(num, k=ncols)
    if not bands:
        return []
    first_band = min(bands) - 70
    rows = []
    for row in group_rows(toks):
        nums   = [t for t in row if NUM_RE.match(t.text)]
        labels = [t for t in row if t.x1 < first_band and not NUM_RE.match(t.text)]
        if not nums or not labels:
            continue
        labels.sort(key=lambda t: t.x0)
        label = " ".join(t.text for t in labels).strip()
        x0    = labels[0].x0
        vals  = [np.nan] * ncols
        for t in nums:
            j = int(np.argmin([abs(t.x1 - b) for b in bands]))
            if np.isnan(vals[j]):
                vals[j] = float(t.text.replace(",", ""))
        is_total = bool(re.search(total_re, label, re.I))
        rows.append((label, vals, is_total, x0))
        if is_total:
            break
    return rows


def _indent_levels(rows, tol=12):
    xs   = [x0 for _, _, tot, x0 in rows if not tot]
    base = min(xs) if xs else 0
    return [("TOTAL" if tot else ("TOP" if x0 <= base + tol else "SUB"))
            for _, _, tot, x0 in rows]


# ============================================================================
# WORKBOOK WRITER
# ============================================================================
HDR  = Font(bold=True, name="Arial", size=10)
BASE = Font(name="Arial", size=10)
FILL = PatternFill("solid", fgColor="D9E1F2")
CT   = Alignment(horizontal="center")


def write_jurisdiction_tab(ws, t6_detail, years, metrics, note):
    """Write the Jurisdiction (Table 6) sheet with a main section and an
    'Other Agencies' section below a labeled break row.

    Section assignment follows Josh's explicit instructions:
      Main section — all cities (ever ROWTYPE=CITY) and all standard
        recurring per-county OTHER-type agencies (county unincorporated,
        State Highways, State Park Service, U.S. Forest Service, Bureau of
        Indian Affairs, U.S. Bureau of Reclamation, University of CA).
        Label-drift aliases (Loomis Town → Loomis, Sutter/Yuba → Yuba City)
        are already collapsed by normalize_names() before this point, so
        they do not appear as separate rows.
      Other Agencies — the sparse tail: military, federal land agencies,
        and any one-off entries "listed every now and then with very little
        VMT" (per Josh's instructions). The 2012 cross-county misparsings
        listed by Josh are excluded from the output entirely (filtered in
        BAD_2012 before this function is called).

    The lookup sums across ROWTYPE for the same (COUNTY, JURISDICTION, YEAR)
    so stray single-year OTHER tags on real cities are absorbed correctly.
    """
    # Standard OTHER-type jurisdiction names that belong in the main section.
    # These are the regular recurring per-county entries present across most years.
    _MAIN_OTHER_NAMES = {
        "State Highways",
        "State Park Service",
        "U.S. Forest Service",
        "Bureau Of Indian Affairs",
        "U.S. Bureau Of Reclamation",
        "University Of California",
    }

    def _is_main(county, juris):
        """True if this OTHER-type jurisdiction belongs in the main section."""
        if juris.endswith(" County"):        # county unincorporated rows
            return True
        return juris in _MAIN_OTHER_NAMES

    # City pairs — ever tagged ROWTYPE=CITY across any year.
    # Stray single-year OTHER tags (2003 SUTTER/YOLO cities, 2007 YUBA cities)
    # are absorbed via the summing lookup below, not excluded here.
    ever_city = set(
        zip(t6_detail.loc[t6_detail.ROWTYPE == "CITY", "COUNTY"],
            t6_detail.loc[t6_detail.ROWTYPE == "CITY", "JURISDICTION"])
    )

    # ── build a lookup that sums across ROWTYPE for the same key ─────────────
    index_cols = ["COUNTY", "JURISDICTION"]
    key_cols   = index_cols + ["YEAR"]
    agg = (t6_detail
           .groupby(key_cols, as_index=False, sort=False)
           [[col for col, _ in metrics]]
           .sum(min_count=1))
    lookup = {k: g for k, g in agg.groupby(key_cols, sort=False)}

    # ── assign rows to main or Other Agencies ────────────────────────────────
    seen_main  = {}
    seen_other = {}
    for _, row in t6_detail.iterrows():
        pair    = (row["COUNTY"], row["JURISDICTION"])
        in_main = (pair in ever_city) or _is_main(row["COUNTY"], row["JURISDICTION"])
        if in_main:
            if pair not in seen_main:
                seen_main[pair] = len(seen_main)
        else:
            if pair not in seen_other:
                seen_other[pair] = len(seen_other)

    # ── post-filter: demote main-section pairs with < 5 years of data to Other ──
    # Runs after the primary rules so it doesn't disturb well-established entries,
    # but catches future one-off or sparse rows automatically.
    year_counts = (t6_detail.groupby(["COUNTY", "JURISDICTION"])["YEAR"]
                   .nunique())
    for pair in [p for p in list(seen_main) if year_counts.get(p, 0) < 5]:
        seen_other[pair] = len(seen_other)
        del seen_main[pair]

    # ── sort main_idx: SACOG county order, cities before OTHER-type within county ─
    county_order = {c: i for i, c in enumerate(
        ["EL DORADO", "PLACER", "SACRAMENTO", "SUTTER", "YOLO", "YUBA"]
    )}

    def _main_sort_key(pair):
        county, juris = pair
        co = county_order.get(county, 99)
        # Cities (ever_city) before OTHER-type agencies within the same county,
        # then alphabetical within each group.
        is_city = pair in ever_city
        return (co, 0 if is_city else 1, juris)

    main_idx  = sorted(seen_main,  key=_main_sort_key)
    other_idx = sorted(seen_other, key=lambda p: (county_order.get(p[0], 99), p[1]))

    # ── write header rows ─────────────────────────────────────────────────────
    ws.cell(1, 1, note).font = BASE
    head  = 3
    first = len(index_cols) + 1
    span  = len(metrics)
    for j, ic in enumerate(index_cols, 1):
        ws.cell(head, j, ic).font = HDR
    for yi, yr in enumerate(years):
        c = first + yi * span
        ws.cell(head, c, yr).font = HDR
        ws.cell(head, c).alignment = CT
        ws.merge_cells(start_row=head, start_column=c,
                       end_row=head, end_column=c + span - 1)
        for mi, (_, lab) in enumerate(metrics):
            ws.cell(head + 1, c + mi, lab).font = BASE
            ws.cell(head + 1, c + mi).alignment = CT

    if t6_detail.empty:
        return

    # ── write main section ────────────────────────────────────────────────────
    r = head + 2
    for county, juris in main_idx:
        ws.cell(r, 1, county).font = BASE
        ws.cell(r, 2, juris).font  = BASE
        for yi, yr in enumerate(years):
            sub = lookup.get((county, juris, yr))
            c   = first + yi * span
            if sub is not None and len(sub):
                for mi, (col, _) in enumerate(metrics):
                    val = sub.iloc[0][col]
                    try:
                        out = None if pd.isna(val) else round(float(val), 2)
                    except (ValueError, TypeError):
                        out = val
                    ws.cell(r, c + mi, out).font = BASE
        r += 1

    # ── section break ─────────────────────────────────────────────────────────
    ws.cell(r, 1, "Other Agencies").font = HDR
    r += 1

    # ── write Other Agencies section ─────────────────────────────────────────
    for county, juris in other_idx:
        ws.cell(r, 1, county).font = BASE
        ws.cell(r, 2, juris).font  = BASE
        for yi, yr in enumerate(years):
            sub = lookup.get((county, juris, yr))
            c   = first + yi * span
            if sub is not None and len(sub):
                for mi, (col, _) in enumerate(metrics):
                    val = sub.iloc[0][col]
                    try:
                        out = None if pd.isna(val) else round(float(val), 2)
                    except (ValueError, TypeError):
                        out = val
                    ws.cell(r, c + mi, out).font = BASE
        r += 1

    # ── column widths + freeze ────────────────────────────────────────────────
    ws.column_dimensions["A"].width = 16
    ws.column_dimensions["B"].width = 28
    for j in range(span * len(years)):
        ws.column_dimensions[get_column_letter(first + j)].width = 16
    ws.freeze_panes = ws.cell(head + 2, first).coordinate


def write_wide(ws, long_df, index_cols, years, metrics, note):
    """Grouped-column sheet: index_cols | year₁ metric₁ metric₂ | year₂ … """
    ws.cell(1, 1, note).font = BASE
    head  = 3
    for j, ic in enumerate(index_cols, 1):
        ws.cell(head, j, ic).font = HDR
    first = len(index_cols) + 1
    span  = len(metrics)
    for yi, yr in enumerate(years):
        c = first + yi * span
        ws.cell(head, c, yr).font = HDR
        ws.cell(head, c).alignment = CT
        ws.merge_cells(start_row=head, start_column=c,
                       end_row=head, end_column=c + span - 1)
        for mi, (_, lab) in enumerate(metrics):
            ws.cell(head + 1, c + mi, lab).font = BASE
            ws.cell(head + 1, c + mi).alignment = CT

    if long_df.empty:
        return

    key_cols = index_cols + ["YEAR"]
    lookup   = {k: g for k, g in long_df.groupby(key_cols, sort=False)}
    idx      = long_df[index_cols].drop_duplicates().values.tolist()
    row0     = head + 2
    for ri, keyvals in enumerate(idx):
        r = row0 + ri
        for j, v in enumerate(keyvals, 1):
            ws.cell(r, j, v).font = BASE
        for yi, yr in enumerate(years):
            sub = lookup.get((*keyvals, yr))
            c   = first + yi * span
            if sub is not None and len(sub):
                for mi, (col, _) in enumerate(metrics):
                    val = sub.iloc[0][col]
                    try:
                        out = None if pd.isna(val) else round(float(val), 2)
                    except (ValueError, TypeError):
                        out = val
                    ws.cell(r, c + mi, out).font = BASE

    ws.column_dimensions["A"].width = 16
    if len(index_cols) > 1:
        ws.column_dimensions["B"].width = 28
    for j in range(span * len(years)):
        ws.column_dimensions[get_column_letter(first + j)].width = 16
    ws.freeze_panes = ws.cell(row0, first).coordinate


# ============================================================================
# BATCH DRIVER
# ============================================================================
def discover(base_dir, year_min, year_max):
    """{year: filepath} for every report discovered under base_dir whose year
    falls within [year_min, year_max] (inclusive)."""
    found = {}
    for pat in FILE_GLOBS:
        for f in glob.glob(os.path.join(base_dir, pat)):
            m = re.search(r"(19|20)\d{2}", os.path.basename(f))
            if not m:
                continue
            y = int(m.group())
            if year_min <= y <= year_max and y not in found:
                found[y] = f
    return dict(sorted(found.items()))


def main(year_min=YEAR_MIN, year_max=YEAR_MAX):
    files = discover(BASE_DIR, year_min, year_max)
    if not files:
        print(f"No reports found under {BASE_DIR!r}.")
        return
    print("Discovered:", {y: os.path.basename(f) for y, f in files.items()})

    t1_all, t6_all, mpo_all = [], [], []
    for yr, path in files.items():
        rep = open_report(path) # TODO: Not working with a zip folder?

        # ── extraction (only run what TABLES requests) ────────────────────────
        t1 = extract_table1(rep, yr) if "T1" in TABLES else pd.DataFrame(
            columns=["YEAR", "FACILITY_TYPE", "ROWTYPE", *T1_COLS])

        if "T6" in TABLES:
            t6, _, _ = extract_table6(rep, yr)
        else:
            t6 = pd.DataFrame(columns=["YEAR", "COUNTY", "JURISDICTION", "ROWTYPE", *COLS])

        if "MPO" in TABLES:
            mpo, _ = extract_mpo(rep, yr)
        else:
            mpo = pd.DataFrame(columns=["YEAR", "MPO", "ROWTYPE", *MPO_COLS])

        if not t1.empty:  t1_all.append(t1)
        if not t6.empty:  t6_all.append(t6)
        if not mpo.empty: mpo_all.append(mpo)

        # ── validation ────────────────────────────────────────────────────────
        c1     = validate_simple(t1, T1_COLS, detail_rowtypes=["TOP"]) if "T1"  in TABLES else []
        c6, w6 = validate(t6)                                           if "T6"  in TABLES else ([], [])
        cm     = ((validate_simple(mpo, MPO_COLS)
                   if not mpo.empty and "ROWTYPE" in mpo.columns else ["empty"])
                  if "MPO" in TABLES else [])
        # ── status line ───────────────────────────────────────────────────────
        enc = ("clean" if rep.kind != "pdf"
               else ("clean" if rep.text_layer_clean else "garbled"))
        parts = []
        if "T1"  in TABLES: parts.append(f"T1:{'OK' if not c1 else 'FAIL'}")
        if "T6"  in TABLES: parts.append(f"T6:{'OK' if not c6 else 'FAIL'}")
        if "MPO" in TABLES: parts.append(f"MPO:{'OK' if not cm else 'FAIL'}")
        print(f"{yr} [{rep.kind}/{enc}]  " + "  ".join(parts))

    years = sorted(files)
    T1  = (pd.concat(t1_all,  ignore_index=True) if t1_all
           else pd.DataFrame(columns=["YEAR", "FACILITY_TYPE", "ROWTYPE", *T1_COLS]))
    T6  = (pd.concat(t6_all,  ignore_index=True) if t6_all
           else pd.DataFrame(columns=["YEAR", "COUNTY", "JURISDICTION", "ROWTYPE", *COLS]))
    MPO = (pd.concat(mpo_all, ignore_index=True) if mpo_all
           else pd.DataFrame(columns=["YEAR", "MPO", "ROWTYPE", *MPO_COLS]))

    # Canonicalize drifting labels (OCR garbles, style/plural variants, and the
    # unincorporated-county relabels) before any sheet is built, so the wide
    # tabs and the tidy masters share one consistent naming.
    T1, T6 = normalize_names(T1, T6)
    # Fill verified cells the OCR path dropped (keyed to canonical labels).
    T6 = apply_known_corrections(T6)

    # Remove 2012 cross-county misparsings: the 2012 report erroneously
    # assigned a small amount of VMT to cities under the wrong county.
    # Josh explicitly flagged these five pairs to exclude from output entirely.
    _BAD_2012 = {
        ("EL DORADO",  "Folsom"),
        ("PLACER",     "West Sacramento"),
        ("SACRAMENTO", "Roseville"),
        ("YOLO",       "Rocklin"),
        ("YOLO",       "Roseville"),
    }
    bad_mask = (
        (T6.YEAR == 2012) &
        T6.apply(lambda r: (r["COUNTY"], r["JURISDICTION"]) in _BAD_2012, axis=1)
    )
    if bad_mask.any():
        T6 = T6[~bad_mask].reset_index(drop=True)

    wb = Workbook(); wb.remove(wb.active)

    # Jurisdictions (t6) — tab 1, with main/Other Agencies section split
    write_jurisdiction_tab(
        wb.create_sheet("Jurisdiction (Table 6)"),
        T6[T6.ROWTYPE != "TOTAL"].copy(), years,
        [("MM_TOTAL", "Maintained Miles"), ("DVMT_TOTAL", "Daily VMT (1000s)")],
        "Jurisdictions in the six-county Sacramento region. Blank = not listed that year. "
        "Labels are normalized to canonical names for trending.")

    # County (t6) — tab 2
    cty = T6[T6.ROWTYPE == "TOTAL"].copy()
    if not cty.empty:
        cty["_o"] = cty["COUNTY"].map({c: i for i, c in enumerate(SACOG)})
        cty = cty.sort_values("_o")
    write_wide(wb.create_sheet("County (Table 6)"), cty, ["COUNTY"], years,
               [("MM_TOTAL", "Maintained Miles"), ("DVMT_TOTAL", "Daily VMT (1000s)")],
               "SACOG county totals from HPMS Table 6. Daily VMT in thousands. Includes Tahoe Basin for El Dorado and Placer Counties.")

    # By Region (MPO) — tab 3
    write_wide(wb.create_sheet("Region (Table 9)"),
               MPO[MPO.ROWTYPE == "DETAIL"], ["MPO"], years,
               [("LANE_MILES", "Lane Miles"), ("DVMT_1000", "Daily VMT (1000s)")],
               "By MPO/region from the 'Miles, Lane Miles and DVMT by MPO' table in HPMS. Some regional designations have changed through time.")

    # Statewide (t1) — tab 4
    write_wide(wb.create_sheet("Statewide (Table 1)"),
               T1[T1.ROWTYPE == "TOP"], ["FACILITY_TYPE"], years,
               [("MAINT_MILES", "Maintained Miles"), ("LANE_MILES", "Lane Miles"),
                ("AVMT_MILLIONS", "AVMT (millions)")],
               "Statewide by facility type (HPMS Table 1 top-level rows; sums to statewide total).")

    wb.save(OUTPUT)
    print("Saved", OUTPUT)


if __name__ == "__main__":
    # Optional year-range overrides:
    #   python run_hpms.py              → full range (YEAR_MIN..YEAR_MAX)
    #   python run_hpms.py 2012         → only 2012
    #   python run_hpms.py 2012 2014    → 2012 through 2014
    check_pdfinfo()
    import sys as _sys
    _args = _sys.argv[1:]
    if len(_args) == 1:
        _y = int(_args[0]); main(year_min=_y, year_max=_y)
    elif len(_args) >= 2:
        main(year_min=int(_args[0]), year_max=int(_args[1]))
    else:
        main()