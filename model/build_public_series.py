"""Build the public-statistics series used across several tabs.

Outputs (data/processed):
  dc_construction.csv        US private construction by building type, $B
                             (Census C30): data centers, general office,
                             warehouses, retail. Calendar-year totals plus the
                             latest month's seasonally adjusted annual rate.
  semis_monthly.csv          Worldwide semiconductor billings, monthly (WSTS
                             Historical Billings Report), 3-month moving
                             average and year-on-year growth.
  cloud_ai_adoption.csv      Share of EU enterprises (10+ employees) using paid
                             cloud services, sophisticated cloud services, and
                             AI (Eurostat ICT usage survey).
  lab_revenue_history.csv    Anthropic and OpenAI annualized revenue over time
                             (Epoch AI, AI companies revenue reports).
  anthropic_unit_economics.csv  Operating expenses by function and revenue
                             from Anthropic's final prospectus (424B4,
                             Nov-2026), supplemental operating expense note.
  cve_counts.csv             CVEs published per year (NVD API, rejected
                             records excluded), from a cached JSON.

Raw inputs live in data/raw/{census,wsts,eurostat,epoch,edgar,nvd}. The 424B4
(14 MB) is not committed; when absent, the existing CSV is kept.

Run from the project root:  python model/build_public_series.py
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

import openpyxl
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"


# --------------------------------------------------------------------------- #
# Census construction spending
# --------------------------------------------------------------------------- #
def _census(path: Path) -> pd.DataFrame:
    ws = openpyxl.load_workbook(path, read_only=True, data_only=True).worksheets[0]
    rows = list(ws.iter_rows(values_only=True))
    hdr = [str(h).split("\n")[0].replace("_x000D_", "").strip() if h else ""
           for h in rows[3]]
    data = [r for r in rows[4:]
            if r[0] and re.match(r"^[A-Z][a-z]{2}-\d\d", str(r[0]))]
    df = pd.DataFrame(data, columns=hdr)
    df["date"] = pd.to_datetime(df["Date"].str[:6], format="%b-%y")
    keep = {"Data center": "datacenter", "General": "office",
            "Warehouse": "warehouse", "Automotive": "auto",
            "Food/beverage": "food", "Multi-retail": "multi",
            "Other commercial": "other"}
    out = df[["date"]].copy()
    for src, dst in keep.items():
        out[dst] = pd.to_numeric(df[src], errors="coerce") / 1000
    # Retail = commercial excluding warehouses and farms
    out["retail"] = out[["auto", "food", "multi", "other"]].sum(axis=1)
    return out[["date", "datacenter", "office", "warehouse", "retail"]]


def build_construction() -> None:
    nsa = _census(RAW / "census" / "privtime.xlsx")
    sa = _census(RAW / "census" / "privsatime.xlsx")
    nsa["year"] = nsa["date"].dt.year
    full = nsa.groupby("year").filter(lambda g: len(g) == 12)
    ann = full.groupby("year")[["datacenter", "office", "warehouse",
                                "retail"]].sum()
    ann = ann[ann.index >= 2014]          # data-center category starts 2014
    rows = [(y, *[round(v, 1) for v in r], "reported", "")
            for y, r in ann.iterrows()]
    last = sa.sort_values("date").iloc[-1]
    rows.append((int(last["date"].year),
                 *[round(last[c], 1) for c in
                   ("datacenter", "office", "warehouse", "retail")],
                 "run-rate",
                 f"Seasonally adjusted annual rate, {last['date']:%b-%Y}"))
    df = pd.DataFrame(rows, columns=["year", "datacenter_b", "office_b",
                                     "warehouse_b", "retail_b", "source_type",
                                     "note"])
    df.to_csv(PROC / "dc_construction.csv", index=False)
    print(df.to_string(index=False))


# --------------------------------------------------------------------------- #
# WSTS monthly billings
# --------------------------------------------------------------------------- #
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


def build_semis_monthly() -> None:
    wb = openpyxl.load_workbook(RAW / "wsts" / "wsts_historical_billings.xlsx",
                                read_only=True, data_only=True)

    def worldwide(sheet: str) -> pd.Series:
        year, out = None, {}
        for r in wb[sheet].iter_rows(values_only=True):
            if isinstance(r[0], (int, float)) and r[0] and 1980 < r[0] < 2100:
                year = int(r[0])
            elif r[0] == "Worldwide" and year:
                for m, v in enumerate(r[1:13], start=1):
                    if isinstance(v, (int, float)) and v > 0:   # future = 0
                        out[pd.Timestamp(year, m, 1)] = v / 1e6   # $1000 -> $B
        return pd.Series(out).sort_index()

    raw, mma = worldwide("Monthly Data"), worldwide("3MMA")
    df = pd.DataFrame({"billings_b": raw, "billings_3mma_b": mma})
    df["yoy_pct"] = (df["billings_3mma_b"] / df["billings_3mma_b"].shift(12)
                     - 1) * 100
    df = df.round(2).rename_axis("month").reset_index()
    df["month"] = df["month"].dt.strftime("%Y-%m")
    df.to_csv(PROC / "semis_monthly.csv", index=False)
    print(df.tail(3).to_string(index=False), len(df))
    build_semis_annual(raw)


# WSTS Spring 2026 forecast release (2 Jun 2026), $B. "Other" = total less
# logic and memory (microprocessors, analog, discretes, opto, sensors).
WSTS_FC = {2025: {"total": 795.640, "logic": 299.547, "memory": 230.042},
           2026: {"total": 1511.248, "logic": 411.371, "memory": 803.941},
           2027: {"total": 1913.683, "logic": 522.820, "memory": 1062.085}}


def build_semis_annual(monthly: pd.Series) -> None:
    """Annual totals: WSTS monthly sums for full years, then the forecast."""
    yr = monthly.groupby(monthly.index.year)
    tot = yr.sum()[yr.count() == 12]
    rows = [(int(y), round(v, 1), "reported", "") for y, v in tot.items()
            if y >= 1990]
    for y in sorted(WSTS_FC):
        if y not in tot.index:
            rows.append((y, round(WSTS_FC[y]["total"], 1), "forecast",
                         "WSTS Spring 2026 forecast (Jun-2026)"))
    pd.DataFrame(rows, columns=["year", "sales_b", "source_type", "note"]
                 ).to_csv(PROC / "semis_billings.csv", index=False)
    print("annual:", rows[-4:])

    # Segment split: keep the earlier years, replace 2025 onward with WSTS.
    seg = pd.read_csv(PROC / "semis_segments.csv")
    seg = seg[seg["year"] < min(WSTS_FC)]
    add = []
    for y, d in WSTS_FC.items():
        st = "reported" if y in tot.index else "forecast"
        note = "WSTS Spring 2026 release" if y == min(WSTS_FC) else ""
        add += [(y, "Logic (compute)", round(d["logic"], 1), st, note),
                (y, "Memory (storage)", round(d["memory"], 1), st, ""),
                (y, "Other (analog/micro/discrete)",
                 round(d["total"] - d["logic"] - d["memory"], 1), st, "")]
    seg = pd.concat([seg, pd.DataFrame(add, columns=seg.columns)])
    seg.to_csv(PROC / "semis_segments.csv", index=False)


# --------------------------------------------------------------------------- #
# Eurostat: cloud and AI adoption
# --------------------------------------------------------------------------- #
def _eurostat(path: Path, indic: str, size: str = "GE10") -> dict[int, float]:
    d = json.loads(path.read_text())
    dims, sizes = d["id"], d["size"]
    strides, s = [], 1
    for n in reversed(sizes):
        strides.insert(0, s)
        s *= n
    inv = {k: {i: c for c, i in d["dimension"][k]["category"]["index"].items()}
           for k in dims}
    out = {}
    for k, v in d["value"].items():
        idx = [(int(k) // st) % n for st, n in zip(strides, sizes)]
        lab = {dims[j]: inv[dims[j]][idx[j]] for j in range(len(dims))}
        if lab["indic_is"] == indic and lab["size_emp"] == size:
            out[int(lab["time"])] = round(v, 1)
    return dict(sorted(out.items()))


def build_adoption() -> None:
    e = RAW / "eurostat"
    series = {
        "Cloud: any paid service": _eurostat(e / "cloud_any.json", "E_CC"),
        "Cloud: sophisticated services": _eurostat(
            e / "cloud_sophisticated.json", "E_CC1_S"),
        "AI: any AI technology": _eurostat(e / "ai_use.json", "E_AI_TANY"),
    }
    rows = [(s, y, v, "reported") for s, d in series.items()
            for y, v in d.items()]
    df = pd.DataFrame(rows, columns=["series", "year", "share_pct",
                                     "source_type"])
    df.to_csv(PROC / "cloud_ai_adoption.csv", index=False)
    print(df.pivot(index="year", columns="series", values="share_pct"))


# --------------------------------------------------------------------------- #
# Epoch AI: lab revenue history
# --------------------------------------------------------------------------- #
def build_lab_history() -> None:
    d = pd.read_csv(RAW / "epoch" / "ai_companies_revenue_reports.csv")
    d = d[d["Company"].isin(["Anthropic", "OpenAI"])
          & (d["Scope"] == "Full company")
          & d["Annualized revenue (USD)"].notna()].copy()
    d["date"] = pd.to_datetime(d["Date"])
    d["rank"] = (d["Confidence"] == "Confident").astype(int)
    # one point per company and month: prefer company-confident, then latest
    d["ym"] = d["date"].dt.to_period("M")
    d = (d.sort_values(["Company", "ym", "rank", "date"])
         .groupby(["Company", "ym"]).tail(1))
    out = pd.DataFrame({
        "company": d["Company"], "date": d["date"].dt.strftime("%Y-%m-%d"),
        "run_rate_b": (d["Annualized revenue (USD)"] / 1e9).round(2),
        "confidence": d["Confidence"], "source_type": d["Source type"]})
    out.sort_values(["company", "date"]).to_csv(
        PROC / "lab_revenue_history.csv", index=False)
    print(out.groupby("company").tail(2).to_string(index=False))


# --------------------------------------------------------------------------- #
# Anthropic prospectus: operating expenses by function
# --------------------------------------------------------------------------- #
def build_anthropic() -> None:
    src = RAW / "edgar" / "anthropic_424b4.htm"
    if not src.exists():
        print("424B4 not cached; keeping anthropic_unit_economics.csv")
        return
    t = re.sub(r"<[^>]+>", " ", src.read_text(encoding="utf-8",
                                              errors="ignore"))
    t = re.sub(r"\s+", " ", html.unescape(t))
    num = r"\$?\s?([\d,]+|[^\w\s$(),.]+)"   # a dash renders as a symbol
    blk = t[t.index("operating expenses grouped by function"):][:1500]

    def line(label: str) -> list[float]:
        m = re.search(re.escape(label) + r"(?: \(\d\))?" + (" " + num) * 5, blk)
        return [float(x.replace(",", "")) if x[0].isdigit() else 0.0
                for x in m.groups()]

    periods = ["FY2023", "FY2024", "FY2025", "9M 2025", "9M 2026"]
    cor = line("Cost of revenue")
    rnd = line("Research and development")
    snm = line("Sales and marketing")
    bartz = line("Bartz settlement")
    gna = line("General and administrative")
    rev_m = re.search(r"Revenue" + (" " + num) * 5 + r" Operating margin", t)
    rev = [float(x.replace(",", "")) for x in rev_m.groups()]
    df = pd.DataFrame({
        "period": periods, "revenue_m": rev, "inference_m": cor,
        "training_research_m": rnd, "distribution_m": snm,
        "other_m": [g + b for g, b in zip(gna, bartz)],
        "bartz_settlement_m": bartz, "source_type": "reported"})
    df.to_csv(PROC / "anthropic_unit_economics.csv", index=False)
    print(df.to_string(index=False))


# --------------------------------------------------------------------------- #
# NVD: CVEs published per year (cache built by a separate API pull)
# --------------------------------------------------------------------------- #
def build_cves() -> None:
    src = RAW / "nvd" / "cve_counts.json"
    if not src.exists():
        print("NVD cache missing; keeping cve_counts.csv")
        return
    d = {int(k): v for k, v in json.loads(src.read_text()).items()}
    last = max(d)
    rows = [(y, n, "ytd" if y == last else "reported",
             "Jan-Sep (published to 30 Sep)" if y == last else "")
            for y, n in sorted(d.items())]
    df = pd.DataFrame(rows, columns=["year", "cves", "source_type", "note"])
    df.to_csv(PROC / "cve_counts.csv", index=False)
    print(df.to_string(index=False))


if __name__ == "__main__":
    build_construction()
    build_semis_monthly()
    build_adoption()
    build_lab_history()
    build_anthropic()
    build_cves()
