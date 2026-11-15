"""Build data/processed/hyperscaler_funding.csv: Big-5 uses of cash vs cash flow.

Per fiscal year: capex, share buybacks and dividends (the main uses of cash)
against operating cash flow. When uses exceed operating cash flow, the gap is
met with debt, equity or cash reserves.

2020-2025 are reported (10-K cash-flow statements). 2026E: capex and operating
cash flow on the same basis as the FCF-transfer chart; buybacks and dividends
are actual where the fiscal year has closed (Microsoft, Oracle), otherwise the
latest year-to-date 10-Q figure annualized.

Run from the project root:  python model/build_hyperscaler_funding.py
"""
from __future__ import annotations

import csv
import datetime as dt
import json
from pathlib import Path

import pandas as pd

from edgar import annual, company_facts

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "edgar"
PROC = ROOT / "data" / "processed"
CACHE = RAW / "hyperscaler_payouts.json"
OUT = PROC / "hyperscaler_funding.csv"

CIK = {"Alphabet": 1652044, "Microsoft": 789019, "Amazon": 1018724,
       "Meta": 1326801, "Oracle": 1341439}
BUYBACK = ["PaymentsForRepurchaseOfCommonStock"]
DIVIDEND = ["PaymentsOfDividendsCommonStock", "PaymentsOfDividends"]
YEARS = range(2022, 2026)      # payout data for all five starts in FY2022
FC_YEAR = 2026
YTD_END = "09-30"


def ytd(facts: dict, tags: list[str], start: str, end: str) -> float | None:
    for tag in tags:
        try:
            units = facts["facts"]["us-gaap"][tag]["units"]["USD"]
        except KeyError:
            continue
        for u in units:
            if u.get("start") == start and u.get("end") == end:
                return u["val"] / 1e9
    return None


def payouts() -> dict:
    """{company: {"buyback": {year: $B}, "dividend": {...}, "ytd": {...}}}"""
    if CACHE.exists():
        return json.loads(CACHE.read_text())
    out = {}
    for co, cik in CIK.items():
        f = company_facts(cik)
        start, end = f"{FC_YEAR}-01-01", f"{FC_YEAR}-{YTD_END}"
        out[co] = {
            "buyback": annual(f, BUYBACK),
            "dividend": annual(f, DIVIDEND),
            "ytd": {"buyback": ytd(f, BUYBACK, start, end) or 0.0,
                    "dividend": ytd(f, DIVIDEND, start, end) or 0.0},
        }
    CACHE.write_text(json.dumps(out, indent=1))
    return out


def main() -> None:
    cap = pd.read_csv(PROC / "hyperscaler_capex.csv")
    ocf = pd.read_csv(PROC / "hyperscaler_ocf.csv")
    fcf = pd.read_csv(PROC / "fcf_transfer.csv")
    guide = pd.read_csv(PROC / "capex_guidance_2026.csv")
    p = payouts()
    get = lambda d, y: float(d.get(str(y), d.get(y, 0.0)) or 0.0)

    rows = [("year", "capex_b", "buybacks_b", "dividends_b", "ocf_b",
             "source_type")]
    for y in YEARS:
        rows.append((y,
                     round(cap[cap.fiscal_year == y].capex_usd_m.sum() / 1000, 1),
                     round(sum(get(p[c]["buyback"], y) for c in CIK), 1),
                     round(sum(get(p[c]["dividend"], y) for c in CIK), 1),
                     round(ocf[ocf.fiscal_year == y].ocf_usd_m.sum() / 1000, 1),
                     "reported"))

    closed = set(cap[cap.fiscal_year == FC_YEAR].company)
    closed_cap = cap[cap.fiscal_year == FC_YEAR].set_index("company").capex_usd_m / 1000
    capex26 = sum(closed_cap.get(c, m) for c, m
                  in zip(guide["company"], guide["capex_mid_b"]))
    hyp_fcf26 = float(fcf[(fcf.group == "Hyperscalers")
                          & (fcf.year == FC_YEAR)].fcf_b.iloc[0])
    ann = 12 / int(YTD_END[:2])

    def est(c: str, kind: str) -> float:
        """Closed fiscal year: actual. Otherwise trailing twelve months if
        cached, else the year-to-date figure annualized."""
        if c in closed:
            return get(p[c][kind], FC_YEAR)
        if "ttm" in p[c]:
            return p[c]["ttm"][kind]
        return p[c]["ytd"][kind] * ann

    bb26 = sum(est(c, "buyback") for c in CIK)
    dv26 = sum(est(c, "dividend") for c in CIK)
    rows.append((FC_YEAR, round(capex26, 1), round(bb26, 1), round(dv26, 1),
                 round(hyp_fcf26 + capex26, 1), "forecast"))

    with OUT.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)
    for r in rows:
        print(*r, sep="\t")


if __name__ == "__main__":
    main()
