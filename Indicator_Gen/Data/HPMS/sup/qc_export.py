"""
qc_export.py — turn the extracted HPMS tables into QC-friendly outputs.

Two outputs, both designed to be eyeballed against the source report PDF open
on a second monitor:

  * build_qc_dashboard(results, path)  -> one self-contained .html file
  * export_csvs(results, outdir)       -> tidy .csv per table (+ per year/table)

`results` is a dict keyed by year. Each value is a dict with at least:
    t1, t6, mpo          : the tidy DataFrames from hpms_pre2012
    t1_page, mpo_page    : int PDF page each table sits on   (for QC navigation)
    t6_span              : (start, end_exclusive) page span of Table 6
    t6_loc               : {COUNTY: [pages]}  (optional, per-county pages)
    kind                 : "archive" | "pdf"  (optional, shown as a badge)

The dashboard recomputes cell-level flags itself (blank / split-mismatch /
total-mismatch) so problems are highlighted exactly where they live, and shows
the PDF page for every table so you know which page to flip to.
"""
import os
import json
import html
import datetime as _dt

import numpy as np
import pandas as pd

# ---- table schemas -------------------------------------------------------- #
# (column key, header label, decimals).  Decimals chosen to match how the
# report itself prints each table, so columns line up visually for QC.
T6_MM   = [("MM_RURAL", "Rural", 1), ("MM_URBAN", "Urban", 1), ("MM_TOTAL", "Total", 1)]
T6_DVMT = [("DVMT_RURAL", "Rural", 1), ("DVMT_URBAN", "Urban", 1), ("DVMT_TOTAL", "Total", 1)]
T1_COLS  = [("MAINT_MILES", "Maintained Miles", 2), ("LANE_MILES", "Lane Miles", 2),
            ("AVMT_MILLIONS", "AVMT (millions)", 2)]
MPO_COLS = [("MILES", "Miles", 2), ("LANE_MILES", "Lane Miles", 2),
            ("DVMT_1000", "Daily VMT (1000s)", 2)]

_TOL = 0.02


def _num(v, dec):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    try:
        return f"{float(v):,.{dec}f}"
    except (TypeError, ValueError):
        return None


def _mismatch(a, b, tol=_TOL):
    if pd.isna(a) or pd.isna(b):
        return False
    return abs(float(a) - float(b)) > max(0.05, tol * abs(float(b)))


# --------------------------------------------------------------------------- #
# Build per-table row models with cell-level flags
# --------------------------------------------------------------------------- #
def _cell(value, dec, flag=None, expect=None):
    """flag in {None,'blank','warn','crit'}. expect = reconciled value to show."""
    txt = _num(value, dec)
    if txt is None:
        flag = flag or "blank"
    return {"t": txt, "f": flag, "e": _num(expect, dec) if expect is not None else None}


def _t6_model(df):
    """Group Table 6 by county; rows carry section + per-cell flags."""
    cols = T6_MM + T6_DVMT
    out = []
    if df is None or not len(df):
        return out
    order = {}
    for c in df["COUNTY"]:
        order.setdefault(c, len(order))
    for county in sorted(order, key=order.get):
        g = df[df["COUNTY"] == county]
        det = g[g.ROWTYPE != "TOTAL"]
        tot = g[g.ROWTYPE == "TOTAL"]
        rows = []
        for _, r in g.iterrows():
            cells = []
            for grp in (T6_MM, T6_DVMT):
                ru = np.nan_to_num(r[grp[0][0]]) + np.nan_to_num(r[grp[1][0]])
                t = r[grp[2][0]]
                split_bad = pd.notna(t) and (pd.notna(r[grp[0][0]]) or pd.notna(r[grp[1][0]])) \
                    and _mismatch(ru, t)
                for j, (key, _lab, dec) in enumerate(grp):
                    flag = "warn" if (split_bad and j < 3) else None
                    cells.append(_cell(r[key], dec, flag))
            # county-total reconciliation
            if r.ROWTYPE == "TOTAL" and len(det):
                for gi, grp in enumerate((T6_MM, T6_DVMT)):
                    tkey = grp[2][0]
                    s = det[tkey].sum()
                    rep = r[tkey]
                    if _mismatch(s, rep):
                        cells[gi * 3 + 2] = _cell(rep, grp[2][2], "crit", expect=s)
            rows.append({"label": r["JURISDICTION"], "type": r["ROWTYPE"], "cells": cells})
        out.append({"county": county, "rows": rows})
    return out


def _flat_model(df, schema, detail_types, total_type="TOTAL"):
    """Generic flat table (T1 / MPO) with total-reconciliation flags."""
    out = []
    if df is None or not len(df):
        return out, []
    label_col = "FACILITY_TYPE" if "FACILITY_TYPE" in df.columns else "MPO"
    det = df[df.ROWTYPE.isin(detail_types)] if detail_types else df[df.ROWTYPE != total_type]
    tot = df[df.ROWTYPE == total_type]
    bad_cols = set()
    if len(tot):
        for key, _lab, _dec in schema:
            if _mismatch(det[key].sum(), tot.iloc[0][key]):
                bad_cols.add(key)
    for _, r in df.iterrows():
        cells = []
        for key, _lab, dec in schema:
            flag = None
            if r.ROWTYPE == total_type and key in bad_cols:
                flag = "crit"
                cells.append(_cell(r[key], dec, flag, expect=det[key].sum()))
                continue
            cells.append(_cell(r[key], dec, flag))
        out.append({"label": r[label_col], "type": r["ROWTYPE"], "cells": cells})
    return out, list(bad_cols)


def _status(model_rows, has_crit, has_warn):
    if has_crit:
        return "crit"
    if has_warn:
        return "warn"
    return "ok"


# --------------------------------------------------------------------------- #
# Assemble the JSON payload the page renders
# --------------------------------------------------------------------------- #
def _payload(results):
    years = sorted(results)
    data = {"years": [], "generated": _dt.datetime.now().strftime("%Y-%m-%d %H:%M")}
    for yr in years:
        R = results[yr]
        t6m = _t6_model(R.get("t6"))
        t6_warn = any(c["f"] == "warn" for cty in t6m for row in cty["rows"] for c in row["cells"])
        t6_crit = any(c["f"] == "crit" for cty in t6m for row in cty["rows"] for c in row["cells"])
        t6_blank = any(c["f"] == "blank" for cty in t6m for row in cty["rows"] for c in row["cells"])

        t1m, t1bad = _flat_model(R.get("t1"), T1_COLS, ["TOP"])
        mpom, mpobad = _flat_model(R.get("mpo"), MPO_COLS, ["DETAIL"])

        span = R.get("t6_span")
        t6_pages = f"{span[0]}–{span[1]-1}" if span else "?"
        data["years"].append({
            "year": yr,
            "kind": R.get("kind", ""),
            "tables": [
                {"id": "t1", "name": "Statewide — Table 1", "page": R.get("t1_page"),
                 "groups": [{"name": "", "cols": [l for _, l, _ in T1_COLS]}],
                 "rows": t1m, "status": _status(t1m, bool(t1bad), False),
                 "note": "Top-level facility types sum to the TOTAL row. AVMT in millions."},
                {"id": "t6", "name": "Jurisdictions / County — Table 6", "page": t6_pages,
                 "groups": [{"name": "Maintained Miles", "cols": [l for _, l, _ in T6_MM]},
                            {"name": "Daily VMT (×1000)", "cols": [l for _, l, _ in T6_DVMT]}],
                 "counties": t6m, "status": _status(t6m, t6_crit, t6_warn or t6_blank),
                 "note": "Detail rows sum to each county TOTAL. DVMT in thousands."},
                {"id": "mpo", "name": "By Region — MPO table", "page": R.get("mpo_page"),
                 "groups": [{"name": "", "cols": [l for _, l, _ in MPO_COLS]}],
                 "rows": mpom, "status": _status(mpom, bool(mpobad), False),
                 "note": "Detail MPOs sum to Grand Total. DVMT in thousands."},
            ],
        })
    return data


# --------------------------------------------------------------------------- #
# HTML
# --------------------------------------------------------------------------- #
_HTML = r"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>HPMS QC — VMT_3</title>
<style>
:root{
  --paper:#f6f4ee; --panel:#fffdf7; --ink:#1d1c18; --muted:#7c776c;
  --line:#ddd7c9; --rule:#e7e2d6;
  --ok:#3f7d52; --ok-bg:#eaf2ec;
  --warn:#9a6700; --warn-bg:#fbf2dc;
  --crit:#a4291f; --crit-bg:#f8e4e0;
  --blank:#b9b3a6; --accent:#1f4e46;
  --mono:ui-monospace,"SF Mono","Cascadia Mono","JetBrains Mono",Menlo,Consolas,monospace;
  --sans:"Iowan Old Style","Palatino Linotype",ui-rounded,"Segoe UI",system-ui,sans-serif;
}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);
  font-size:15px;line-height:1.4}
header{position:sticky;top:0;z-index:20;background:var(--accent);color:#f4efe2;
  padding:10px 18px;box-shadow:0 1px 0 #00000022}
.h-row{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap}
.brand{font-weight:700;letter-spacing:.02em;font-size:17px}
.brand small{font-weight:400;opacity:.7;font-size:12px;letter-spacing:.04em}
.gen{margin-left:auto;font-size:11px;opacity:.7;font-variant-numeric:tabular-nums}
nav{display:flex;gap:6px;flex-wrap:wrap;margin-top:9px}
.tab{font:600 12.5px var(--sans);letter-spacing:.02em;color:#dfe9e3;
  background:#ffffff14;border:1px solid #ffffff22;border-radius:7px;
  padding:5px 11px;cursor:pointer;font-variant-numeric:tabular-nums}
.tab[data-on="1"]{background:#f6f4ee;color:var(--accent);border-color:#f6f4ee}
.tab .dot{display:inline-block;width:7px;height:7px;border-radius:50%;
  margin-left:6px;vertical-align:middle}
.dot.ok{background:#7fc795}.dot.warn{background:#e3b341}.dot.crit{background:#e86b5e}
.bar2{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px;align-items:center}
.seg{display:flex;border:1px solid #ffffff2e;border-radius:7px;overflow:hidden}
.seg button{font:600 12px var(--sans);color:#dfe9e3;background:transparent;border:0;
  padding:5px 12px;cursor:pointer}
.seg button[data-on="1"]{background:#f6f4ee;color:var(--accent)}
.filter{margin-left:auto;font-size:12px;color:#dfe9e3;display:flex;gap:6px;align-items:center}
.filter input{accent-color:#cde3da}
main{max-width:1080px;margin:0 auto;padding:20px 18px 80px}
.tablecard{background:var(--panel);border:1px solid var(--line);border-radius:12px;
  margin:0 0 22px;overflow:hidden;box-shadow:0 1px 2px #0000000a}
.tc-head{display:flex;align-items:center;gap:14px;padding:13px 16px;
  border-bottom:1px solid var(--rule);flex-wrap:wrap}
.tc-name{font-weight:700;font-size:16px}
.pageref{font:600 12px var(--mono);background:var(--accent);color:#f4efe2;
  padding:3px 9px;border-radius:6px;letter-spacing:.02em}
.pageref b{font-weight:700}
.badge{font:700 11px var(--sans);letter-spacing:.03em;padding:3px 9px;border-radius:20px;
  text-transform:uppercase}
.badge.ok{background:var(--ok-bg);color:var(--ok)}
.badge.warn{background:var(--warn-bg);color:var(--warn)}
.badge.crit{background:var(--crit-bg);color:var(--crit)}
.tc-note{color:var(--muted);font-size:12.5px;flex-basis:100%}
.kind{font:600 10px var(--sans);color:var(--muted);border:1px solid var(--line);
  border-radius:5px;padding:2px 6px;text-transform:uppercase;letter-spacing:.05em}
table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums}
thead th{position:sticky;top:0;background:var(--panel)}
th,td{padding:5px 12px;text-align:right;border-bottom:1px solid var(--rule);white-space:nowrap}
th.lab,td.lab{text-align:left;white-space:normal}
.grp th{font:700 11px var(--sans);letter-spacing:.04em;color:var(--accent);
  text-align:center;border-bottom:1px solid var(--line);padding-bottom:3px}
.sub th{font:600 11.5px var(--sans);color:var(--muted);border-bottom:1.5px solid var(--line)}
td.num{font:13.5px/1.3 var(--mono)}
tr.t-CITY td.lab{padding-left:26px}
tr.t-OTHER td.lab{padding-left:26px}
tr.t-SUB td.lab{padding-left:26px;color:var(--muted)}
tr.t-TOTAL td{font-weight:700;border-top:1.5px solid var(--line);background:#00000005}
tr.t-TOTAL td.lab{text-transform:uppercase;letter-spacing:.02em;font-size:13px}
.county-h td{background:var(--accent);color:#f4efe2;font:700 12px var(--sans);
  letter-spacing:.05em;text-transform:uppercase;padding:5px 12px}
.sect td{color:var(--muted);font:600 11px var(--sans);letter-spacing:.06em;
  text-transform:uppercase;padding:5px 12px 2px}
.cell-blank{color:var(--blank)}
.cell-warn{background:var(--warn-bg);color:var(--warn);font-weight:600;border-radius:4px}
.cell-crit{background:var(--crit-bg);color:var(--crit);font-weight:700}
.cell-crit .exp{display:block;font:10px var(--mono);color:#7a1e16;opacity:.85}
.exp::before{content:"≠ "}
.legend{display:flex;gap:16px;flex-wrap:wrap;font-size:11.5px;color:var(--muted);
  margin:0 0 16px;padding:9px 14px;background:var(--panel);border:1px solid var(--line);
  border-radius:9px}
.legend span{display:inline-flex;align-items:center;gap:6px}
.sw{width:13px;height:13px;border-radius:3px;display:inline-block;border:1px solid #0002}
.empty{padding:34px;text-align:center;color:var(--muted);font-style:italic}
.hide{display:none!important}
.count{font:600 11px var(--mono);color:var(--muted)}
</style></head><body>
<header>
  <div class="h-row">
    <div class="brand">HPMS&nbsp;QC&nbsp;Console <small>VMT_3 · extracted vs. report</small></div>
    <div class="gen" id="gen"></div>
  </div>
  <nav id="years"></nav>
  <div class="bar2">
    <div class="seg" id="tabsel"></div>
    <label class="filter"><input type="checkbox" id="flagonly">Flagged rows only</label>
  </div>
</header>
<main>
  <div class="legend">
    <span><i class="sw" style="background:var(--warn-bg);border-color:var(--warn)"></i>split ≠ total (total still trusted)</span>
    <span><i class="sw" style="background:var(--crit-bg);border-color:var(--crit)"></i>detail sum ≠ reported total (do not trust)</span>
    <span><i class="sw" style="background:#fff"></i><span class="cell-blank">—</span>&nbsp;blank / OCR miss</span>
    <span>📄 = page in the report PDF to compare against</span>
  </div>
  <div id="view"></div>
</main>
<script>
const DATA = __DATA__;
let curYear = DATA.years.length ? DATA.years[0].year : null;
let curTable = "t6";
let flagOnly = false;

document.getElementById("gen").textContent = "generated " + DATA.generated;

function rowHasFlag(cells){return cells.some(c=>c.f==="warn"||c.f==="crit"||c.f==="blank");}

function cellHTML(c){
  if(c.t===null) return '<td class="num cell-blank">—</td>';
  let cls="num"; if(c.f==="warn")cls+=" cell-warn"; if(c.f==="crit")cls+=" cell-crit";
  let exp = (c.f==="crit"&&c.e!==null)?('<span class="exp">'+c.e+'</span>'):"";
  return '<td class="'+cls+'">'+c.t+exp+'</td>';
}

function flatTable(tbl){
  let cols = tbl.groups[0].cols;
  let h = '<table><thead><tr><th class="lab">Item</th>';
  cols.forEach(c=>h+='<th>'+c+'</th>'); h+='</tr></thead><tbody>';
  let shown=0;
  tbl.rows.forEach(r=>{
    if(flagOnly && r.type!=="TOTAL" && !rowHasFlag(r.cells)) return;
    shown++;
    h+='<tr class="t-'+r.type+'"><td class="lab">'+r.label+'</td>';
    r.cells.forEach(c=>h+=cellHTML(c)); h+='</tr>';
  });
  h+='</tbody></table>';
  if(!shown) h='<div class="empty">No rows match the current filter.</div>';
  return h;
}

function t6Table(tbl){
  let span=tbl.groups.reduce((a,g)=>a+g.cols.length,0);
  let h='<table><thead><tr class="grp"><th class="lab" rowspan="2">Jurisdiction</th>';
  tbl.groups.forEach(g=>h+='<th colspan="'+g.cols.length+'">'+g.name+'</th>'); h+='</tr><tr class="sub">';
  tbl.groups.forEach(g=>g.cols.forEach(c=>h+='<th>'+c+'</th>')); h+='</tr></thead><tbody>';
  let shown=0;
  tbl.counties.forEach(cty=>{
    let body='', lastSect=null, any=false;
    cty.rows.forEach(r=>{
      if(flagOnly && r.type!=="TOTAL" && !rowHasFlag(r.cells)) return;
      if((r.type==="CITY"||r.type==="OTHER") && r.type!==lastSect){
        body+='<tr class="sect"><td colspan="'+(span+1)+'">'+(r.type==="CITY"?"Cities":"Other")+'</td></tr>';
        lastSect=r.type;
      }
      body+='<tr class="t-'+r.type+'"><td class="lab">'+r.label+'</td>';
      r.cells.forEach(c=>body+=cellHTML(c)); body+='</tr>';
      any=true; shown++;
    });
    if(any){
      h+='<tr class="county-h"><td colspan="'+(span+1)+'">'+cty.county+'</td></tr>'+body;
    }
  });
  h+='</tbody></table>';
  if(!shown) h='<div class="empty">No rows match the current filter.</div>';
  return h;
}

function render(){
  // year tabs
  document.getElementById("years").innerHTML = DATA.years.map(y=>{
    let worst="ok";
    y.tables.forEach(t=>{ if(t.status==="crit")worst="crit"; else if(t.status==="warn"&&worst!=="crit")worst="warn";});
    return '<button class="tab" data-y="'+y.year+'" data-on="'+(y.year===curYear?1:0)+'">'+
      y.year+'<span class="dot '+worst+'"></span></button>';
  }).join("");
  // table selector
  let yobj = DATA.years.find(y=>y.year===curYear);
  document.getElementById("tabsel").innerHTML = yobj.tables.map(t=>
    '<button data-t="'+t.id+'" data-on="'+(t.id===curTable?1:0)+'">'+
    t.name.split("—")[0].trim()+'</button>').join("");
  // view
  let tbl = yobj.tables.find(t=>t.id===curTable);
  let v='<div class="tablecard"><div class="tc-head">'+
    '<span class="tc-name">'+tbl.name+'</span>'+
    '<span class="pageref">📄 PDF&nbsp;p.&nbsp;<b>'+(tbl.page??"?")+'</b></span>'+
    '<span class="badge '+tbl.status+'">'+
      (tbl.status==="ok"?"reconciled":tbl.status==="warn"?"check flags":"critical")+'</span>'+
    (yobj.kind?'<span class="kind">'+yobj.kind+'</span>':'')+
    '<span class="tc-note">'+tbl.note+'</span></div>'+
    (tbl.id==="t6"?t6Table(tbl):flatTable(tbl))+'</div>';
  document.getElementById("view").innerHTML=v;
  // wire
  document.querySelectorAll("[data-y]").forEach(b=>b.onclick=()=>{curYear=+b.dataset.y;render();});
  document.querySelectorAll("[data-t]").forEach(b=>b.onclick=()=>{curTable=b.dataset.t;render();});
}
document.getElementById("flagonly").onchange=e=>{flagOnly=e.target.checked;render();};
render();
</script></body></html>"""


def build_qc_dashboard(results, path="VMT_HPMS_QC.html"):
    payload = _payload(results)
    htmltext = _HTML.replace("__DATA__", json.dumps(payload))
    with open(path, "w", encoding="utf-8") as f:
        f.write(htmltext)
    return path


# --------------------------------------------------------------------------- #
# CSV
# --------------------------------------------------------------------------- #
def export_csvs(results, outdir="qc_csv"):
    os.makedirs(outdir, exist_ok=True)
    written = []
    bundles = {"t1": [], "t6": [], "mpo": []}
    for yr in sorted(results):
        R = results[yr]
        for key in bundles:
            df = R.get(key)
            if df is not None and len(df):
                df = df.copy()
                if "YEAR" not in df.columns:
                    df.insert(0, "YEAR", yr)
                else:                       # move YEAR to the front
                    df = df[["YEAR"] + [c for c in df.columns if c != "YEAR"]]
                bundles[key].append(df)
    for key, frames in bundles.items():
        if frames:
            p = os.path.join(outdir, f"hpms_{key}_alltidy.csv")
            pd.concat(frames, ignore_index=True).to_csv(p, index=False)
            written.append(p)
    return written
