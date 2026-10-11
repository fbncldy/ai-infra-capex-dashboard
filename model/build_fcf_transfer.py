"""Build data/processed/fcf_transfer.csv.

Free cash flow (operating cash flow minus capex) for two baskets, reported
through 2025 and estimated for 2026-27:
  Hyperscalers:   Alphabet, Microsoft, Amazon, Meta, Oracle
  Semiconductors: NVIDIA, Micron, Broadcom, Applied Materials

Year conventions match the rest of the dashboard:
  - Hyperscalers by fiscal year, as in the capex charts (Microsoft FY ends Jun,
    Oracle May), and 2026 capex on the same basis as the annual capex chart.
  - Semiconductors by the calendar year each fiscal year mostly covers. NVIDIA's
    fiscal year ends in late January, so its FY ending Jan Y+1 counts as year Y,
    as in the Silicon tab and the accelerator-revenue chart.

Run from the project root:  python model/build_fcf_transfer.py
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "edgar"
PROC = ROOT / "data" / "processed"
OUT = PROC / "fcf_transfer.csv"

# --- Estimate inputs (each traceable to a filing or a stated assumption) ------
# NVIDIA FY2027 (Feb-26..Jan-27): H1 from the Q2 FY27 10-Q (ended 2026-07-26).
NV_H1_FCF = 74.4 - 4.4                 # OCF minus capex, $B
NV_H1_REV = 81.6 + 96.2                # Q1 + Q2 revenue, $B
NV_FY27_REV = 404.0                    # consensus range $396-412B
NV_FY28_GROWTH = 0.70                  # company guidance, Aug-2026
NV_CONV = NV_H1_FCF / NV_H1_REV        # H1 FY27 FCF conversion, ~39%
# Micron FY2027 at twice its H2 FY2026 FCF (Q3 17.57 + Q4 32.86).
MU_FY27 = 2 * (17.57 + 32.86)
# Broadcom (FY ends Nov) and AMAT (Oct): nine months reported, Q4 at Q3's rate.
AVGO_FY26 = 31.94 + 13.67
AMAT_FY26 = 3.58 + 2.33
AVGO_FY27 = 65.0                       # line of sight to $115B AI revenue
AMAT_FY27 = 8.0
# Hyperscalers 2027: FY2026E operating cash flow +20%, capex at ~$1T consensus.
HYP_OCF_GROWTH_27 = 0.20
HYP_CAPEX_27 = 1000.0
NV_EARLY_CAPEX = 0.6e9                 # FY2019-21 capex not tagged; immaterial


def load_annual(name: str) -> dict[int, float]:
    return {int(k): v / 1e9 for k, v in
            json.loads((RAW / "fcf" / f"{name}.json").read_text()).items()}


def ytd_ocf(company: str, start: str, end: str) -> float:
    data = json.loads((RAW / f"{company.lower()}_ocf.json").read_text())
    for u in data["units"]["USD"]:
        if u.get("start") == start and u.get("end") == end:
            return u["val"] / 1e9
    raise KeyError(f"{company} OCF {start}..{end} not in cache")


def semis() -> dict[int, tuple[float, str]]:
    fcf = {}
    for n in ("nvidia", "micron", "broadcom", "appliedmaterials"):
        ocf, cap = load_annual(f"{n}_ocf"), load_annual(f"{n}_capex")
        shift = 1 if n == "nvidia" else 0          # FY ending Jan Y+1 -> year Y
        for y_end, o in ocf.items():
            c = cap.get(y_end, NV_EARLY_CAPEX / 1e9 if n == "nvidia" else None)
            if c is None:
                continue
            fcf.setdefault(n, {})[y_end - shift] = o - c
    out = {}
    for y in range(2018, 2026):
        out[y] = (sum(fcf[n][y] for n in fcf), "reported")
    nv27 = NV_H1_FCF + NV_CONV * (NV_FY27_REV - NV_H1_REV)
    nv28 = NV_CONV * NV_FY27_REV * (1 + NV_FY28_GROWTH)
    out[2026] = (nv27 + fcf["micron"][2026] + AVGO_FY26 + AMAT_FY26, "forecast")
    out[2027] = (nv28 + MU_FY27 + AVGO_FY27 + AMAT_FY27, "forecast")
    return out


def hyperscalers() -> dict[int, tuple[float, str]]:
    ocf = pd.read_csv(PROC / "hyperscaler_ocf.csv")
    cap = pd.read_csv(PROC / "hyperscaler_capex.csv")
    guide = pd.read_csv(PROC / "capex_guidance_2026.csv").set_index("company")
    m = ocf.merge(cap, on=["company", "fiscal_year"])
    m["fcf"] = (m["ocf_usd_m"] - m["capex_usd_m"]) / 1000
    out = {y: (float(m.loc[m.fiscal_year == y, "fcf"].sum()), "reported")
           for y in range(2018, 2026)}
    fcf26, ocf26 = 0.0, 0.0
    for co in guide.index:
        closed = m[(m.company == co) & (m.fiscal_year == 2026)]
        if len(closed):                      # Microsoft, Oracle: year has closed
            fcf26 += float(closed["fcf"].iloc[0])
            ocf26 += float(closed["ocf_usd_m"].iloc[0]) / 1000
        else:                                # grow FY2025 OCF at its H1-2026 pace
            g = (ytd_ocf(co, "2026-01-01", "2026-06-30")
                 / ytd_ocf(co, "2025-01-01", "2025-06-30"))
            o25 = float(m.loc[(m.company == co) & (m.fiscal_year == 2025),
                              "ocf_usd_m"].iloc[0]) / 1000
            fcf26 += o25 * g - float(guide.loc[co, "capex_mid_b"])
            ocf26 += o25 * g
    out[2026] = (fcf26, "forecast")
    out[2027] = (ocf26 * (1 + HYP_OCF_GROWTH_27) - HYP_CAPEX_27, "forecast")
    return out


def main() -> None:
    rows = [("group", "year", "fcf_b", "source_type")]
    for group, series in (("Hyperscalers", hyperscalers()),
                          ("Semiconductors", semis())):
        for y, (v, src) in sorted(series.items()):
            rows.append((group, y, round(v, 1), src))
    with OUT.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)
    for r in rows[1:]:
        print(*r, sep="\t")


if __name__ == "__main__":
    main()
