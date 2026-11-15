"""Build data/processed/capex_by_layer.csv: capex by value-chain layer.

Layers (reported capex, $B):
  Hyperscalers  Big-5, fiscal years, same basis as the Hyperscalers tab; 2026E
                uses the actual where the fiscal year has closed, otherwise the
                guidance midpoint.
  Chipmakers    TSMC (calendar year) and Micron (fiscal year to Aug/Sep).
                SK Hynix and Samsung are excluded: both report in won, and
                Samsung's capex mixes memory, foundry, phones and displays.
  NeoClouds     CoreWeave and Nebius (Nebius from 2024; earlier years were
                Yandex).

AI labs' own builds (xAI, OpenAI's Stargate) are excluded: no filings.
Telecoms are excluded: their capex is not AI spending.

Run from the project root:  python model/build_capex_by_layer.py
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pandas as pd

from edgar import annual, company_facts

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "edgar"
PROC = ROOT / "data" / "processed"
CACHE = RAW / "neocloud_capex.json"
OUT = PROC / "capex_by_layer.csv"

YEARS = range(2020, 2026)
FC_YEAR = 2026
TSMC_2026_GUIDE = 62.0          # $60-64B, reiterated at Q3 2026 (Oct-2026)
COREWEAVE_2026_GUIDE = 38.0     # $37-39B, Q3 2026 results (Nov-2026)
CAPEX_TAGS = ["PaymentsToAcquirePropertyPlantAndEquipment",
              "PaymentsToAcquireProductiveAssets"]


def neocloud_capex() -> dict[str, dict[int, float]]:
    """CoreWeave and Nebius annual capex, cached after the first fetch."""
    if CACHE.exists():
        return {k: {int(y): v for y, v in d.items()}
                for k, d in json.loads(CACHE.read_text()).items()}
    out = {"CoreWeave": annual(company_facts(1769628), CAPEX_TAGS)}
    nb = company_facts(1513845)
    out["Nebius"] = (annual(nb, CAPEX_TAGS)
                     or annual(nb, ["PurchaseOfPropertyPlantAndEquipment"],
                               taxonomy="ifrs-full"))
    CACHE.write_text(json.dumps(out, indent=1))
    return out


def hyperscalers() -> dict[int, float]:
    cap = pd.read_csv(PROC / "hyperscaler_capex.csv")
    guide = pd.read_csv(PROC / "capex_guidance_2026.csv")
    tot = cap.groupby("fiscal_year")["capex_usd_m"].sum() / 1000
    out = {y: float(tot[y]) for y in YEARS}
    closed = (cap[cap.fiscal_year == FC_YEAR].set_index("company")
              ["capex_usd_m"] / 1000)
    out[FC_YEAR] = float(sum(closed.get(c, m) for c, m
                             in zip(guide["company"], guide["capex_mid_b"])))
    return out


def chipmakers() -> dict[int, float]:
    fp = pd.read_csv(PROC / "foundry_players.csv")
    tsmc = fp[fp.company == "TSMC"].set_index("year")["capex_b"]
    mu = {int(k): v / 1e9 for k, v in
          json.loads((RAW / "fcf" / "micron_capex.json").read_text()).items()}
    out = {y: float(tsmc[y]) + mu[y] for y in YEARS}
    out[FC_YEAR] = TSMC_2026_GUIDE + mu[FC_YEAR]      # Micron FY2026 is actual
    return out


def neoclouds() -> dict[int, float]:
    nc = neocloud_capex()
    neb_2026 = float(pd.read_csv(PROC / "neoclouds.csv")
                     .set_index("company").loc["Nebius", "capex_2026e_b"])
    out = {}
    for y in YEARS:
        out[y] = nc["CoreWeave"].get(y, 0.0) + (nc["Nebius"].get(y, 0.0)
                                                if y >= 2024 else 0.0)
    out[FC_YEAR] = COREWEAVE_2026_GUIDE + neb_2026
    return out


def main() -> None:
    rows = [("layer", "year", "capex_b", "source_type")]
    for layer, series in (("Hyperscalers", hyperscalers()),
                          ("Chipmakers", chipmakers()),
                          ("NeoClouds", neoclouds())):
        for y, v in sorted(series.items()):
            rows.append((layer, y, round(v, 1),
                         "forecast" if y == FC_YEAR else "reported"))
    with OUT.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)
    df = pd.DataFrame(rows[1:], columns=rows[0])
    print(df.pivot(index="year", columns="layer", values="capex_b").to_string())


if __name__ == "__main__":
    main()
