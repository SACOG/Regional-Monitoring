"""
hpms_pre2012.py — Table 6 extractor for the PRE-2012 Caltrans HPMS reports.

Why this exists
---------------
Warren's parser targets the clean text-layer reports (2019-2024). The pre-2012
files supplied for this project are ZIP archives (one <n>.txt + one <n>.jpeg per
page) whose embedded TEXT LAYER silently drops the two right-hand columns
(DVMT Urbanized / DVMT Total) — the numbers we most need. The page IMAGES are
complete and clean, so we read numbers from the image via OCR.

Approach
--------
1. Navigate with the text layer (reliable for structure): find Table 6's page
   span and the page(s) for each requested county.
2. OCR each county page to word boxes (tesseract TSV on a 2x upscaled image).
3. Assign every numeric token to one of the 6 columns by clustering on its
   RIGHT edge (columns are right-aligned). Blank cells = no token in that band,
   so nothing is guessed.
4. Reconstruct rows by y, classify County header / Cities: / Other: / TOTAL.
5. VALIDATE arithmetically: rural+urban==total per group per row, and the sum
   of a county's detail rows == its TOTAL row. Anything that fails is flagged,
   which is how we trust OCR output.

Requires: pillow, pytesseract-free (shells out to `tesseract`), pandas, numpy.
System: tesseract-ocr, and Python zipfile (stdlib).
"""

from importlib.metadata import files
import io
import re
import zipfile
import subprocess
from dataclasses import dataclass, field
import glob
import tempfile
import os
import sys

os.environ.setdefault("TESSDATA_PREFIX", os.path.join(sys.prefix, "share/tessdata"))

import numpy as np
import pandas as pd
from PIL import Image

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

NUM_RE = re.compile(r"^-?\d[\d,]*\.\d{2}$")          # 0.66 / 1,055.63
TABLE_HDR = re.compile(r"^\s*table\s+(\d+(?:-\d+)?)\s*(\(continued\))?\s*$", re.I)


# --------------------------------------------------------------------------- #
# Format-agnostic report loader
# --------------------------------------------------------------------------- #
class Report:
    """Uniform access to a year's report regardless of underlying format.

    Two backends are supported transparently:
      * ARCHIVE  — the zip-of-<n>.txt/<n>.jpeg files supplied in this project.
      * PDF      — a real Caltrans PDF (uses poppler: pdftotext + pdftoppm).
    Both expose .texts {page->text} for navigation and .image(page) for OCR.
    """
    def __init__(self, texts, image_fn, kind):
        self.texts = texts
        self._image_fn = image_fn
        self.kind = kind

    def image(self, page):
        return self._image_fn(page)


def open_report(path):
    # ARCHIVE backend: zip containing <n>.txt / <n>.jpeg
    if zipfile.is_zipfile(path):
        z = zipfile.ZipFile(path)
        names = z.namelist()
        if any(re.fullmatch(r"\d+\.txt", n) for n in names):
            texts = {int(m.group(1)): z.read(n).decode("utf-8", "replace")
                     for n in names for m in [re.fullmatch(r"(\d+)\.txt", n)] if m}

            def _img(p):
                return Image.open(io.BytesIO(z.read(f"{p}.jpeg"))).convert("L")

            return Report(texts, _img, "archive")

    # TEXT-DUMP backend: plain-text extraction (no images, no zip).
    # Guard: real PDFs always start with "%PDF-"; skip this check for them.
    try:
        with open(path, "rb") as _f:
            _magic = _f.read(5)
        if not _magic.startswith(b"%PDF-"):
            raw = open(path, encoding="utf-8", errors="replace").read()
            if "Public Road Data" in raw or "HIGHWAY PERFORMANCE MONITORING" in raw.upper():
                # Store whole blob as a single synthetic page so navigation still works
                texts = {0: raw}
                def _img_text(p):
                    raise RuntimeError("Text-dump backend has no images — OCR unavailable")
                return Report(texts, _img_text, "text")
    except OSError:
        pass

    # PDF backend (poppler)
    info = subprocess.run(["pdfinfo", path],capture_output=True,text=True,encoding="utf-8",errors="replace").stdout
    m = re.search(r"Pages:\s+(\d+)", info)
    if not m:
        raise ValueError(f"Unrecognized report format: {path}")
    npages = int(m.group(1))
    texts = {}
    for p in range(1, npages + 1):
        texts[p] = subprocess.run(["pdftotext", "-layout", "-f", str(p), "-l", str(p), path, "-"],capture_output=True,text=True,encoding="utf-8",errors="replace").stdout
        

    def _img(p, _path=path):
        import glob
        import tempfile
        import os

        tmpdir = tempfile.gettempdir()
        # Fix 1: Include the year or a unique identifier in the prefix so files don't collide
        # Extracting year from path or string to keep it clean
        yr_match = re.search(r"(19|20)\d{2}", os.path.basename(_path))
        yr_str = yr_match.group() if yr_match else "data"
        prefix = os.path.join(tmpdir, f"hpms_{yr_str}_pg{p}_")

        # Clean up any leftover matching files from a prior broken run first
        for old_f in glob.glob(prefix + "*.png"):
            try: os.remove(old_f)
            except: pass

        res = subprocess.run(
            [
                "pdftoppm",
                "-png",
                "-r", "200",
                "-f", str(p),
                "-l", str(p),
                _path,
                prefix,
            ],
            capture_output=True,
            text=True,
        )

        files = sorted(glob.glob(prefix + "*.png"))

        if not files:
            raise RuntimeError(
                f"pdftoppm produced no PNGs\nSTDERR:\n{res.stderr}"
            )
        
        img = Image.open(files[-1]).convert("L")

        img.load()  # Ensure the file is fully read before we delete it

        for f in files:
            try: os.remove(f)
            except: pass

        return img

    return Report(texts, _img, "pdf")

# --------------------------------------------------------------------------- #
# Archive access
# --------------------------------------------------------------------------- #
def load_texts(path):
    """{page:int -> text} from the zip archive's *.txt members."""
    out = {}
    with zipfile.ZipFile(path) as z:
        for n in z.namelist():
            m = re.fullmatch(r"(\d+)\.txt", n)
            if m:
                out[int(m.group(1))] = z.read(n).decode("utf-8", "replace")
    return out


def load_image(path, page):
    with zipfile.ZipFile(path) as z:
        return Image.open(io.BytesIO(z.read(f"{page}.jpeg"))).convert("L")


# --------------------------------------------------------------------------- #
# Navigation (text layer)
# --------------------------------------------------------------------------- #
def table_spans(texts):
    """{table_id -> first_page} from standalone 'TABLE n' header lines."""
    starts = {}
    for p in sorted(texts):
        nonempty = [ln.replace("\r", "") for ln in texts[p].splitlines() if ln.strip()]
        for ln in nonempty[:3]:                 # header may sit below a page-number line
            m = TABLE_HDR.match(ln)
            if m:
                starts.setdefault(m.group(1), p)
                break
    return starts


def table6_range(texts):
    """(start, end_exclusive) page span of Table 6."""
    starts = table_spans(texts)
    if "6" not in starts:
        raise ValueError("Table 6 header not found")
    f6 = starts["6"]
    after = [p for t, p in starts.items() if p > f6]
    return f6, (min(after) if after else max(texts) + 1)


def county_pages(texts, county, span):
    """Pages within Table 6 where `county` heads a row (anchored to line start)."""
    lo, hi = span
    pages = []
    pat = re.compile(rf"^\s*{re.escape(county)}\b")
    anti = re.compile(rf"^\s*{re.escape(county)}[A-Z]")     # PLACER vs PLACERVILLE
    for p in range(lo, hi):
        if p not in texts:
            continue
        for raw in texts[p].splitlines():
            ln = raw.replace("\r", "")
            if pat.match(ln) and not anti.match(ln):
                pages.append(p)
                break
    return pages


# --------------------------------------------------------------------------- #
# OCR + column reconstruction
# --------------------------------------------------------------------------- #
@dataclass
class Tok:
    text: str
    x0: int
    x1: int          # right edge
    yc: float        # vertical center


def ocr_tokens(img, scale=2):
    # Auto-orient: table pages should be landscape (W > H).
    # Some archive years store images rotated 90° — correct before OCR.
    if img.height > img.width:
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
    """Cluster numeric tokens' right edges into k column centers (gap split)."""
    edges = sorted(t.x1 for t in num_toks)
    if len(edges) < k:
        return None
    gaps = sorted(((edges[i + 1] - edges[i], i) for i in range(len(edges) - 1)),
                  reverse=True)[: k - 1]
    cuts = sorted(i for _, i in gaps)
    bands, start = [], 0
    for cut in cuts + [len(edges) - 1]:
        seg = edges[start:cut + 1]
        bands.append(sum(seg) / len(seg))
        start = cut + 1
    return bands


def group_rows(toks, ytol=14):
    """Group tokens into visual rows by vertical center."""
    rows, cur, last = [], [], None
    for t in sorted(toks, key=lambda t: t.yc):
        if last is not None and t.yc - last > ytol:
            rows.append(cur); cur = []
        cur.append(t); last = t.yc
    if cur:
        rows.append(cur)
    return rows


def assign_six(num_toks, bands):
    """Place numeric tokens into 6 column slots by nearest band (right edge)."""
    vals = [np.nan] * 6
    for t in num_toks:
        j = int(np.argmin([abs(t.x1 - b) for b in bands]))
        v = float(t.text.replace(",", ""))
        vals[j] = v if np.isnan(vals[j]) else vals[j]   # keep first if collision
    return vals


# --------------------------------------------------------------------------- #
# Page parsing
# --------------------------------------------------------------------------- #
COLS = ["MM_RURAL", "MM_URBAN", "MM_TOTAL", "DVMT_RURAL", "DVMT_URBAN", "DVMT_TOTAL"]


def parse_page(img, year, seed_county=None):
    """Parse one page. County is tracked from in-page headers; `seed_county`
    is used only for a continuation page that opens mid-county (no header)."""
    toks = ocr_tokens(img)
    num = [t for t in toks if NUM_RE.match(t.text)]
    bands = learn_columns(num)
    if not bands:
        return pd.DataFrame(columns=["YEAR", "COUNTY", "JURISDICTION", "ROWTYPE", *COLS])
    first_band = min(bands) - 60          # label tokens sit left of column 1
    rows_out, county, section = [], seed_county, None

    for row in group_rows(toks):
        nums = [t for t in row if NUM_RE.match(t.text)]
        labels = [t for t in row if t.x1 < first_band and not NUM_RE.match(t.text)]
        label = " ".join(t.text for t in sorted(labels, key=lambda t: t.x0)).strip()
        U = label.upper()

        # Statewide grand-total row — never a county detail row.
        # Use search (not match) to catch OCR noise prefixes like "3! Ny Statewide Total".
        if re.search(r"\bSTATEWIDE\b", U):
            county = None
            continue

        # County total, e.g. "EL DORADO Total"
        mtot = re.match(r"^(.*?)\s+TOTAL\b", U)
        if mtot and mtot.group(1).strip() in CA_COUNTIES and nums:
            c = mtot.group(1).strip()
            rows_out.append([year, c, f"{c} TOTAL", "TOTAL", *assign_six(nums, bands)])
            continue

        # County header (no numbers)
        base = U.replace("(CONTINUED)", "").strip()
        if base in CA_COUNTIES and not nums:
            county, section = base, None
            continue

        # Section labels can prefix the first jurisdiction on the same line
        msec = re.match(r"^(CITIES|OTHER)\s*:?\s*(.*)$", U)
        if msec:
            section = "CITY" if msec.group(1) == "CITIES" else "OTHER"
            label = msec.group(2).strip()
            if not label:
                continue

        if nums and label:
            rows_out.append([year, county, label.title(),
                             section or "OTHER", *assign_six(nums, bands)])

    df = pd.DataFrame(rows_out,
                      columns=["YEAR", "COUNTY", "JURISDICTION", "ROWTYPE", *COLS])
    return df


# --------------------------------------------------------------------------- #
# Text-layer parsers (for plain-text-dump backend and archive MPO pages)
# --------------------------------------------------------------------------- #
_LOOSE_NUM = re.compile(r"^-?\d[\d,]*(?:\.\d*)?$")   # allows 0, 1 or 2+ decimal places
_TRAILING_COMMA = re.compile(r",$")  # used to reject "31," as a number token


def _split_row(line):
    """Return (label_str, [float, ...]) splitting trailing run of numeric tokens."""
    toks = line.split()
    # Rejoin split decimals: pdftotext -layout sometimes emits "73,703." and "16.00"
    # as separate tokens when the decimal straddles a column boundary.
    merged = []
    i = 0
    while i < len(toks):
        t = toks[i]
        if t.endswith(".") and re.match(r"^\d[\d,]*\.$", t) and i + 1 < len(toks):
            nxt = toks[i + 1]
            if re.match(r"^\d+$", nxt):          # bare digits follow: "73,703." + "16" → "73,703.16"
                merged.append(t + nxt)
                i += 2
                continue
        merged.append(t)
        i += 1
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
    label = " ".join(rest).strip()
    return label, vals


def _fix_number_spaces(text):
    """Collapse spurious single spaces within numbers from Identity-H encoding artifacts.

    Some PDFs using Identity-H font encoding produce garbled number text like
    '73,703. 16' (space after decimal) or '65,324.2 1' (space mid-digits).
    In pdftotext -layout output, legitimate column separators use multiple spaces,
    so collapsing only SINGLE spaces between digit characters is safe.
    """
    text = text.replace('_', '')   # remove underline-formatting underscores (e.g. YOLO Total row)
    for _ in range(6):   # iterate until stable (handles chains like '3 1, 113.05')
        prev = text
        text = re.sub(r'(\d[\d,]*)\. (\d)', r'\1.\2', text)   # space after decimal point
        text = re.sub(r'(\d) (\d[\d,]*)',    r'\1\2',  text)   # space between digit groups
        text = re.sub(r'(\d), (\d)',         r'\1,\2', text)   # space after comma in number
        if text == prev:
            break
    # Fix common character substitutions (e.g. lowercase 'l' → '1' between digits)
    text = re.sub(r'(?<=\d)l(?=\d)', '1', text)
    return text


def _slice_table(blob, start_re, stop_re):
    """Return the substring of blob between the first match of start_re
    and the first match of stop_re that follows it (or end of blob)."""
    m = re.search(start_re, blob, re.I)
    if not m:
        return ""
    tail = blob[m.start():]
    s = re.search(stop_re, tail, re.I)
    return tail[:s.start()] if s else tail


def parse_table1_from_text(blob, year):
    """Parse Table 1 (statewide) from a plain-text dump.

    Marks flat items as TOP and known sub-items (under FEDERAL AGENCIES /
    OTHER STATE AGENCIES) as SUB so validate_simple reconciles correctly.
    """
    # Anchor on "CITY STREETS" — the first data row, always present,
    # unique to Table 1 (not in any other table), and format-stable across years.
    # Pre-process to collapse spurious spaces within numbers (Identity-H encoding artifact).
    seg = _slice_table(_fix_number_spaces(blob), r"CITY STREETS\s+\d", r"\bTABLE 2\b")
    # Prepend a synthetic "TOTAL" sentinel so the parser stops correctly —
    # the TOTAL row itself is included in the slice because it precedes TABLE 2.
    if not seg:
        return pd.DataFrame(columns=["YEAR","FACILITY_TYPE","ROWTYPE",
                                     "MAINT_MILES","LANE_MILES","AVMT_MILLIONS"])
    # Known parent categories whose immediate children are SUB
    PARENT_RE = re.compile(
        r"^(FEDERAL AGENCIES|OTHER STATE AGENCIES|OTHER LOCAL AGENCIES|OTHER AGENCIES)", re.I)
    TOTAL_RE = re.compile(r"^(STATEWIDE\s+)?TOTAL\b", re.I)

    recs, in_sub, pending_label, pending_rowtype = [], False, None, None
    for ln in seg.splitlines():
        ln = ln.replace("\r", "").strip()
        label, vals = _split_row(ln)
        label = re.sub(r"\s*\*+\s*$", "", label).strip()  # strip trailing asterisks

        # Bare-number line (no label) → apply to pending parent if available
        if not label and len(vals) >= 3:
            if pending_label:
                vals3 = vals[-3:]
                recs.append({"YEAR": year, "FACILITY_TYPE": pending_label.title(),
                             "ROWTYPE": pending_rowtype,
                             "MAINT_MILES": vals3[0], "LANE_MILES": vals3[1],
                             "AVMT_MILLIONS": vals3[2]})
                pending_label, pending_rowtype = None, None
            in_sub = False   # numbers consumed; next rows are peers again
            continue

        if not vals and not label:
            continue

        is_total = bool(TOTAL_RE.match(label))
        if is_total and len(vals) >= 3:
            vals3 = vals[-3:]
            recs.append({"YEAR": year, "FACILITY_TYPE": "Total",
                         "ROWTYPE": "TOTAL",
                         "MAINT_MILES": vals3[0], "LANE_MILES": vals3[1],
                         "AVMT_MILLIONS": vals3[2]})
            break

        if len(vals) >= 3:
            vals3 = vals[-3:]
            if PARENT_RE.match(label):
                rowtype, in_sub = "TOP", True
            elif in_sub:
                rowtype = "SUB"
            else:
                rowtype = "TOP"
            recs.append({"YEAR": year, "FACILITY_TYPE": label.title(),
                         "ROWTYPE": rowtype,
                         "MAINT_MILES": vals3[0], "LANE_MILES": vals3[1],
                         "AVMT_MILLIONS": vals3[2]})
            if PARENT_RE.match(label):
                in_sub = True   # next rows are sub
            pending_label, pending_rowtype = None, None
        elif label and not vals:
            # Label with no numbers — could be a parent or a sub-label
            if PARENT_RE.match(label):
                # Parent group: numbers will appear on next bare-number line
                pending_label, pending_rowtype = label, "TOP"
                in_sub = True
            # else: sub-label (e.g. "U.S FOREST SERVICE") — skip, we want the aggregate
    return pd.DataFrame(recs)


def _find_mpo_text_blob(rep):
    """Return (text_blob, page_or_None) for the MPO table.

    For text-dump: slice blob around the MPO table using the unique
    'MPO  Miles  Lane Miles' column-header line (avoids TOC/intro matches).
    For archive/pdf: find the right page and return its text.
    """
    if rep.kind == "text":
        blob = rep.texts[0]
        # 'MPO Miles Lane Miles' is the column-header row immediately above the
        # data rows — it only appears once, in the actual MPO table.
        seg = _slice_table(
            blob,
            r"MPO\s+Miles\s+Lane\s+Miles",
            r"California.{0,5}s\s+MPOs|TABLE 12|AMBAG\s+Association",
        )
        return seg, None

    # archive or pdf: scan every page for the MPO table header
    for p in sorted(rep.texts, reverse=True):   # MPO is near the end
        head = " ".join(rep.texts[p].splitlines()[:8]).upper()
        if "MPO" in head and ("LANE MILES" in head or "DVMT" in head):
            return rep.texts[p], p
    return "", None


def parse_mpo_from_text(text, year):
    """Parse MPO table rows from a text blob (clean for all known formats).

    Handles:
    * DVMT in thousands (most years) — values have decimals ~ tens of thousands
    * DVMT raw (2008)               — integer millions; scaled ÷ 1000
    """
    recs = []
    TOTAL_RE = re.compile(r"\bTotals?\b|\bSTATEWIDE\b|\bGrand\s+Total\b", re.I)
    STOP_RE  = re.compile(r"California.{0,5}s\s+MPOs|^AMBAG\s+Association|TABLE 12", re.I)

    for ln in text.splitlines():
        ln = ln.replace("\r", "").strip()
        if STOP_RE.search(ln):
            break
        label, vals = _split_row(ln)
        if len(vals) < 3:
            continue
        vals3 = vals[-3:]
        is_total = bool(TOTAL_RE.search(label)) or (not label and len(vals) >= 3)
        if not label and not is_total:
            continue  # bare number line that's not a total — skip
        recs.append({
            "YEAR": year,
            "MPO": label or "TOTAL",
            "ROWTYPE": "TOTAL" if is_total else "DETAIL",
            "MILES": vals3[0], "LANE_MILES": vals3[1], "DVMT_1000": vals3[2],
        })
        if is_total:
            break

    if not recs:
        return pd.DataFrame(columns=["YEAR","MPO","ROWTYPE","MILES","LANE_MILES","DVMT_1000"])

    df = pd.DataFrame(recs)
    # Scale normalisation: 2008 detail rows are raw vehicle-miles; total is already
    # in thousands. Scale ONLY detail rows when their max DVMT > 1,000,000.
    detail_mask = df.ROWTYPE == "DETAIL"
    detail_dvmt = df.loc[detail_mask, "DVMT_1000"]
    if len(detail_dvmt) and detail_dvmt.max() > 1_000_000:
        df.loc[detail_mask, "DVMT_1000"] = df.loc[detail_mask, "DVMT_1000"] / 1000.0
    return df


def parse_table6_totals_from_text(blob, year, counties=SACOG):
    """Extract Table 6 COUNTY TOTAL rows from a plain-text dump.

    The county-total line is always inline and well-formed:
      '<COUNTY NAME> TOTAL  mm_r  mm_u  mm_t  dv_r  dv_u  dv_t'
    Per-jurisdiction detail rows are column-major in these text dumps and
    are NOT extracted here (see inline note below).
    """
    # Search the ENTIRE blob for county TOTAL lines — the "COUNTY Total"
    # pattern only appears in Table 6, so slicing is unnecessary and slicing
    # would miss counties alphabetically before any mid-table continuation header.
    TOT_RE = re.compile(
        r"^({cties})\s+TOTAL\b(.*)$".format(cties="|".join(re.escape(c) for c in counties)),
        re.I | re.MULTILINE
    )

    rows = []
    for m in TOT_RE.finditer(blob):
        county = m.group(1).upper()
        _, vals = _split_row(m.group(0))
        if len(vals) >= 6:
            mm_r, mm_u, mm_t, dv_r, dv_u, dv_t = vals[:6]
        elif len(vals) == 3:          # some years only print the 3 total columns
            mm_r = mm_u = dv_r = dv_u = float("nan")
            mm_t, dv_r, dv_t = vals; dv_u = float("nan")
        else:
            continue
        rows.append({
            "YEAR": year, "COUNTY": county, "JURISDICTION": f"{county} TOTAL",
            "ROWTYPE": "TOTAL",
            "MM_RURAL": mm_r, "MM_URBAN": mm_u, "MM_TOTAL": mm_t,
            "DVMT_RURAL": dv_r, "DVMT_URBAN": dv_u, "DVMT_TOTAL": dv_t,
        })
    return pd.DataFrame(rows)


def _parse_t6_totals_from_pdf_text(rep, year, counties=SACOG):
    """Extract county TOTAL rows from the pdftotext text layer for real PDF files.

    For real PDFs, pdftotext -layout preserves all 6 columns of Table 6 cleanly.
    This is more reliable than OCR for the TOTAL rows that feed the County tab.
    The text layer is scanned across the full Table 6 span rather than per-county
    so nothing is missed regardless of page ordering.
    """
    try:
        span = table6_range(rep.texts)
    except ValueError:
        return pd.DataFrame()

    TOT_RE = re.compile(
        r"^({cties})\s+TOTAL\b(.*)$".format(cties="|".join(re.escape(c) for c in counties)),
        re.I
    )
    rows = []
    seen = set()
    for p in range(span[0], span[1]):
        if p not in rep.texts:
            continue
        page = _fix_number_spaces(rep.texts[p])
        for ln in page.splitlines():
            m = TOT_RE.match(ln.replace("\r", "").strip())
            if not m:
                continue
            county = m.group(1).upper()
            if county in seen:
                continue   # keep first occurrence only
            # Extract all numeric tokens from the line — safer than trailing-only
            # _split_row for TOTAL rows where the last token may be garbled.
            fixed_ln = _fix_number_spaces(ln.replace("\r", "").strip())
            num_toks = [t for t in fixed_ln.split()
                        if _LOOSE_NUM.match(t) and not _TRAILING_COMMA.search(t)]
            vals = [float(t.replace(",", "")) for t in num_toks]
            if len(vals) >= 5:   # accept partial rows; repair_totals fills any gap
                seen.add(county)
                v = vals + [float('nan')] * (6 - len(vals))   # pad to 6
                mm_r, mm_u, mm_t, dv_r, dv_u, dv_t = v[:6]
                rows.append({
                    "YEAR": year, "COUNTY": county,
                    "JURISDICTION": f"{county} TOTAL", "ROWTYPE": "TOTAL",
                    "MM_RURAL": mm_r, "MM_URBAN": mm_u, "MM_TOTAL": mm_t,
                    "DVMT_RURAL": dv_r, "DVMT_URBAN": dv_u, "DVMT_TOTAL": dv_t,
                })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# Arithmetic repair
# --------------------------------------------------------------------------- #
def repair_totals(df):
    """Repair arithmetic inconsistencies in MM/DVMT rural-urban-total triplets.

    Three cases handled:
    1. TOTAL is NaN but both splits present  → TOTAL = RURAL + URBAN
    2. TOTAL < max(RURAL, URBAN)             → TOTAL clearly misread; override with RURAL+URBAN
       (e.g. 2002 El Dorado State Highway DVMT: 299.07 when RURAL=1658 and URBAN=941)
    3. RURAL is NaN but URBAN+TOTAL present  → RURAL = TOTAL - URBAN
    4. URBAN is NaN but RURAL+TOTAL present  → URBAN = TOTAL - RURAL
    """
    if df is None or len(df) == 0:
        return df
    df = df.copy()
    for grp in ("MM", "DVMT"):
        r_col, u_col, t_col = f"{grp}_RURAL", f"{grp}_URBAN", f"{grp}_TOTAL"
        if not all(c in df.columns for c in [r_col, u_col, t_col]):
            continue
        r, u, t = df[r_col], df[u_col], df[t_col]

        # Case 1 & 2: TOTAL is NaN or clearly too small → compute from splits
        bad_total = t.isna() | (t.notna() & r.notna() & u.notna() & (t < r.fillna(0).clip(lower=0)) ) | \
                    (t.notna() & r.notna() & u.notna() & (t < u.fillna(0).clip(lower=0)))
        can_compute = r.notna() & u.notna()
        mask = bad_total & can_compute
        df.loc[mask, t_col] = df.loc[mask, r_col] + df.loc[mask, u_col]

        # Refresh references after potential TOTAL update
        r, u, t = df[r_col], df[u_col], df[t_col]

        # Case 3: RURAL is NaN but URBAN and TOTAL are present
        mask_r = r.isna() & u.notna() & t.notna() & (t >= u)
        df.loc[mask_r, r_col] = df.loc[mask_r, t_col] - df.loc[mask_r, u_col]

        # Case 4: URBAN is NaN but RURAL and TOTAL are present
        r = df[r_col]   # re-read after potential RURAL fill
        mask_u = u.isna() & r.notna() & t.notna() & (t >= r)
        df.loc[mask_u, u_col] = df.loc[mask_u, t_col] - df.loc[mask_u, r_col]

    return df


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #
def validate(df, tol=0.02):
    """Return (critical, warnings).

    critical  -> county detail sum != reported county TOTAL (the numbers you
                 actually ship). These must be zero to trust the output.
    warnings  -> a single row's rural+urban != its own total (a split-only OCR
                 slip; the TOTAL column — all you need — can still be right).
    """
    if df is None or len(df) == 0 or "YEAR" not in df.columns:
        return [], []
    critical, warnings = [], []
    for i, r in df.iterrows():
        for grp in ("MM", "DVMT"):
            ru = np.nan_to_num(r[f"{grp}_RURAL"]) + np.nan_to_num(r[f"{grp}_URBAN"])
            tot = r[f"{grp}_TOTAL"]
            if pd.notna(tot) and abs(ru - tot) > max(tol, tol * abs(tot)):
                warnings.append(f"{r['YEAR']} {r['COUNTY']}/{r['JURISDICTION']}: "
                                f"{grp} rural+urban {ru:.2f} != total {tot:.2f}")
    for (yr, cty), g in df.groupby(["YEAR", "COUNTY"]):
        tot = g[g.ROWTYPE == "TOTAL"]
        det = g[g.ROWTYPE != "TOTAL"]
        if len(tot) and len(det):
            for col in ("MM_TOTAL", "DVMT_TOTAL"):
                s, rep = det[col].sum(), tot[col].iloc[0]
                if pd.notna(rep) and abs(s - rep) > max(0.05, tol * abs(rep)):
                    critical.append(f"{yr} {cty}: detail {col} {s:,.2f} "
                                    f"!= reported {rep:,.2f}")
    return critical, warnings


# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #
def extract_table6(source, year, counties=SACOG):
    rep = source if isinstance(source, Report) else open_report(source)

    # Text-dump backend: county totals from text (jurisdiction detail is
    # column-major in these dumps and cannot be reliably reconstructed).
    if rep.kind == "text":
        blob = rep.texts[0]
        df = parse_table6_totals_from_text(blob, year, counties)
        if len(df):
            print(f"\n[TEXT] --- Table 6 county totals for {year} ---")
            for _, r in df.iterrows():
                print(f"  {r['COUNTY']}: MM_TOTAL={r['MM_TOTAL']:,.2f}  DVMT_TOTAL={r['DVMT_TOTAL']:,.2f}")
            print(f"  NOTE: per-jurisdiction detail not extracted from text-dump format.")
        return repair_totals(df), None, {}

    texts = rep.texts
    span = table6_range(texts)
    loc = {c: county_pages(texts, c, span) for c in counties}
    pages = sorted({p for ps in loc.values() for p in ps})
    frames = [parse_page(rep.image(p), year, seed_county=None) for p in pages]
    df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    # For real PDFs, override OCR county TOTAL rows with text-layer values —
    # pdftotext -layout preserves all 6 columns correctly while OCR can misread digits.
    if rep.kind == "pdf":
        text_totals = _parse_t6_totals_from_pdf_text(rep, year, counties)
        if len(text_totals):
            df = df[df["ROWTYPE"] != "TOTAL"].copy() if len(df) else pd.DataFrame()
            df = pd.concat([df, text_totals], ignore_index=True)
    
    if len(df):
        df = df[df["COUNTY"].isin(counties)].reset_index(drop=True)
        
        # === Table 6 Visual Debugger ===
        print(f"\n[DEBUG] --- Table 6 Extracted Rows for Year {year} ---")
        print(f"{'County':<15} | {'Jurisdiction':<30} | {'Type':<8} | [MM_RUR, MM_URB, MM_TOT, DVMT_RUR, DVMT_URB, DVMT_TOT]")
        print("-" * 115)
        for _, r in df.iterrows():
            metrics = [r['MM_RURAL'], r['MM_URBAN'], r['MM_TOTAL'], r['DVMT_RURAL'], r['DVMT_URBAN'], r['DVMT_TOTAL']]
            formatted_metrics = [f"{v:,.2f}" if pd.notna(v) else "NaN" for v in metrics]
            print(f"{r['COUNTY']:<15} | {r['JURISDICTION']:<30} | {r['ROWTYPE']:<8} | {formatted_metrics}")
        print("-" * 115 + "\n")

    return repair_totals(df), span, loc


# --------------------------------------------------------------------------- #
# Simple single-page tables: Table 1 (statewide) and the MPO/region table
# --------------------------------------------------------------------------- #
def find_table_page(texts, *, number=None, title_keywords=None):
    """Locate a table page by number and/or title keywords (handles drift)."""
    if number is not None:
        starts = table_spans(texts)
        if number in starts:
            return starts[number]
    if title_keywords:
        for p in sorted(texts):
            head = " ".join(l for l in texts[p].splitlines()[:5]).upper()
            if all(k.upper() in head for k in title_keywords):
                return p
    return None


def parse_simple(img, ncols, total_re):
    """Parse a flat 'label + ncols numbers' table.
    Returns [(label, vals, is_total, label_x0)] — label_x0 enables indent detection."""
    toks = ocr_tokens(img)
    num = [t for t in toks if NUM_RE.match(t.text)]
    bands = learn_columns(num, k=ncols)
    if not bands:
        return []
    first_band = min(bands) - 70
    rows = []
    for row in group_rows(toks):
        nums = [t for t in row if NUM_RE.match(t.text)]
        labels = [t for t in row if t.x1 < first_band and not NUM_RE.match(t.text)]
        if not nums or not labels:
            continue
        labels.sort(key=lambda t: t.x0)
        label = " ".join(t.text for t in labels).strip()
        x0 = labels[0].x0
        vals = [np.nan] * ncols
        for t in nums:
            j = int(np.argmin([abs(t.x1 - b) for b in bands]))
            if np.isnan(vals[j]):
                vals[j] = float(t.text.replace(",", ""))
        is_total = bool(re.search(total_re, label, re.I))
        rows.append((label, vals, is_total, x0))
        if is_total:           # stop before any legend/footnotes below the total
            break
    return rows


T1_COLS = ["MAINT_MILES", "LANE_MILES", "AVMT_MILLIONS"]
MPO_COLS = ["MILES", "LANE_MILES", "DVMT_1000"]


def _indent_levels(rows, tol=12):
    """Mark each non-total row TOP (left margin) or SUB (indented) by x0."""
    xs = [x0 for _, _, tot, x0 in rows if not tot]
    base = min(xs) if xs else 0
    return [("TOTAL" if tot else ("TOP" if x0 <= base + tol else "SUB"))
            for _, _, tot, x0 in rows]


def extract_table1(source, year):
    rep = source if isinstance(source, Report) else open_report(source)

    # Text-dump backend
    if rep.kind == "text":
        df = parse_table1_from_text(rep.texts[0], year)
        print(f"\n[TEXT] --- Table 1 for {year} ({len(df)} rows) ---")
        for _, r in df.iterrows():
            print(f"  {r['ROWTYPE']:<6} {r['FACILITY_TYPE']:<40} {r['MAINT_MILES']:>12,.2f}")
        return df

    p = find_table_page(rep.texts, number="1")
    print("TABLE 1 PAGE =", p)
    # Table 1 text layer is clean for most years — parse it directly.
    page_blob = rep.texts.get(p, "") if p else ""
    df = parse_table1_from_text(_fix_number_spaces(page_blob), year)
    # Only use text result if a TOTAL row was found; otherwise fall through to OCR.
    if len(df) and (df.ROWTYPE == "TOTAL").any():
        print(f"\n[TEXT] --- Table 1 for {year} ({len(df)} rows, via text layer) ---")
        for _, r in df.iterrows():
            print(f"  {r['ROWTYPE']:<6} {r['FACILITY_TYPE']:<40} {r['MAINT_MILES']:>12,.2f}")
        return df

    # Fallback: OCR (only if text layer yielded nothing)
    rows = parse_simple(rep.image(p), 3, r"^TOTAL$")
    if not rows:
        print(f"[WARN] T1 year {year}: text layer has no numbers and OCR returned nothing.")
        return pd.DataFrame(columns=["YEAR","FACILITY_TYPE","ROWTYPE",
                                     "MAINT_MILES","LANE_MILES","AVMT_MILLIONS"])
    levels = _indent_levels(rows)
    
    # === VISUAL DEBUGGER ADDITION ===
    print(f"\n--- DEBUG: Table 1 Attempted Parsing for Year {year} ---")
    print(f"{'Row Type':<10} | {'Facility Type Label':<35} | Column Values")
    print("-" * 75)
    for (lab, vals, _, _), lvl in zip(rows, levels):
        print(f"{lvl:<10} | {lab:<35} | {vals}")
    print("-" * 75 + "\n")
    # =================================
    
    recs = [{"YEAR": year, "FACILITY_TYPE": lab.title(), "ROWTYPE": lvl,
             **dict(zip(T1_COLS, vals))}
            for (lab, vals, _, _), lvl in zip(rows, levels)]
    return pd.DataFrame(recs)


def extract_mpo(source, year):
    rep = source if isinstance(source, Report) else open_report(source)

    # Find the MPO text and page number
    text_blob, p = _find_mpo_text_blob(rep)

    if not text_blob.strip():
        print(f"TABLE MPO (T9) PAGE DETECTED = None — not found in {year}")
        return pd.DataFrame(columns=["YEAR","MPO","ROWTYPE","MILES","LANE_MILES","DVMT_1000"]), None

    print(f"TABLE MPO (T9) PAGE DETECTED = {p}")
    df = parse_mpo_from_text(text_blob, year)

    # === Table 9 (MPO) Visual Debugger ===
    print(f"\n[TEXT] --- Table 9 (MPO) for {year} ---")
    print(f"{'Row Type':<10} | {'MPO Region':<35} | ['Miles', 'Lane Miles', 'DVMT (1000s)']")
    print("-" * 90)
    for _, r in df.iterrows():
        print(f"{r['ROWTYPE']:<10} | {r['MPO']:<35} | [{r['MILES']:,.2f}, {r['LANE_MILES']:,.2f}, {r['DVMT_1000']:,.2f}]")
    print("-" * 90 + "\n")

    return df, p


def validate_simple(df, value_cols, total_rowtype="TOTAL", detail_rowtypes=None):
    """Detail rows must sum to the reported total. detail_rowtypes lets Table 1
    reconcile on TOP-level rows only (sub-items are breakdowns, not addends)."""
    crit = []
    tot = df[df.ROWTYPE == total_rowtype]
    if not len(tot):
        return [f"no '{total_rowtype}' row detected"]
    det = df[df.ROWTYPE.isin(detail_rowtypes)] if detail_rowtypes \
        else df[df.ROWTYPE != total_rowtype]
    for col in value_cols:
        s, rep = det[col].sum(), tot[col].iloc[0]
        if pd.notna(rep) and abs(s - rep) > max(0.05, 0.02 * abs(rep)):
            crit.append(f"{col}: detail {s:,.2f} != reported total {rep:,.2f}")
    return crit