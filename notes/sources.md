# Sourcing log

Every datapoint in the dashboard traces back to a source recorded here. This is
the auditability backbone — the part a Technical Intelligence reviewer trusts.

## Alphabet — 10-K (extracted & cross-validated)

Line item: **Purchases of property and equipment**, Consolidated Statements of
Cash Flows. Each fiscal year appears in three overlapping filings; all values
matched exactly, so they are treated as verified.

| FY | Capex ($M) | Source file | Page | Cross-check |
|----|-----------|-------------|------|-------------|
| 2018 | 25,139 | 2020.pdf | 59 | matches 2020 filing |
| 2019 | 23,548 | 2020.pdf | 59 | matches 2020, 2021 filings |
| 2020 | 22,281 | 2020.pdf | 59 | matches 2020, 2021, 2022 filings |
| 2021 | 24,640 | 2021.pdf | 54 | matches 2021, 2022, 2023 filings |
| 2022 | 31,485 | 2022.pdf | 52 | matches 2022, 2023, 2024 filings |
| 2023 | 32,251 | 2023.pdf | 56 | matches 2023, 2024, 2025 filings |
| 2024 | 52,535 | 2024.pdf | 57 | matches 2024, 2025 filings |
| 2025 | 91,447 | 2025.pdf | 53 | latest filing |

Extraction script: `model/extract_capex2.py` (pdfplumber, targets the
Consolidated Statements of Cash Flows page).

## Microsoft / Amazon / Meta — 10-K (EDGAR XBRL)

Pulled from SEC EDGAR's XBRL company-concept API (`data.sec.gov`), cached in
`data/raw/edgar/*.json`, using the **as-originally-reported** annual value (the
filing whose own fiscal year matches the period end). Rebuilt by
`model/build_capex_dataset.py`; each row cites the filing accession number.

Capex concept (cash purchases of PP&E), kept consistent for comparability:
- `PaymentsToAcquirePropertyPlantAndEquipment` — Microsoft, Meta (and Alphabet)
- `PaymentsToAcquireProductiveAssets` — Amazon

Caveats encoded in the `note` column:
- **Microsoft** FY ends June 30 (not calendar-aligned); figure excludes finance
  leases, so it is *below* Microsoft's headline "capital expenditures incl.
  finance leases."
- **Amazon** capex includes fulfilment/logistics, not only AWS — apply an
  AI-share haircut.
- **Meta** has minor later reclassifications (e.g. FY2022 $31,431M originally →
  $31,186M restated); we use as-originally-reported for series consistency.

CIKs: Microsoft 0000789019 · Amazon 0001018724 · Meta 0001326801.

## 2026 forward capex guidance — `capex_guidance_2026.csv`

**Definition caveat:** guidance is reported on a broader basis (total capex,
incl. finance leases) than the cash-PP&E actuals — kept as a separate series, not
a continuation of the historical line. Big-4 2026E ≈ $710B (sum of midpoints),
~2x FY2025 actual.

| Company | 2026E ($B) | Definition | Source |
|---------|-----------|------------|--------|
| Microsoft | 190 | Total capex incl. finance leases (CY2026) | Q2 FY26 earnings / CNBC |
| Amazon | ~200 | All-Amazon total capex | Q4'25 earnings |
| Alphabet | 180–190 | Total capex | Q4'25 earnings |
| Meta | 125–145 | Total capex incl. finance-lease principal | Q4'25 8-K |

Microsoft flagged ~$25B of its step-up as memory/component **cost inflation**, not
capacity — i.e. the HBM bottleneck showing up in price. Sources: Tom's Hardware,
CNBC (2026-02-06), Meta 8-K (EDGAR).

## NeoClouds — `neoclouds.csv`

GPU-as-a-service layer; the strategic angle is **financing durability** (>$20B
sector GPU-backed debt against fast-depreciating assets).

- **CoreWeave** (NASDAQ: CRWV) — 2025 revenue >$5B; backlog $66.8B end-2025
  (~$100B by Q1'26); 9mo-2025 capex $6.2B; ~1GW active power; OpenAI deal +$11.2B
  backlog. SEC CIK 0001769628.
- **Nebius** (NASDAQ: NBIS) — 2026E revenue $3.0–3.4B; ARR target $7–9B; capex
  $20–25B; >3GW contracted by end-2026; $27B Meta deal.
- **Crusoe** (private) — ~$998M 2025E revenue; $10B valuation (Oct-2025); 3.4GW,
  ~946K GPU capacity.
- **Lambda** (private) — ~$520M 2025 revenue; Series E $1.5B (Nov-2025).

Sources: company 8-Ks/press releases on EDGAR, BigGo (NBIS Q1'26 call), Contrary
Research (Crusoe), CB Insights (Lambda).

## Upstream bottleneck — `cowos_capacity.csv`, `hbm_market.csv`

The supply ceiling that gates everything downstream.

**CoWoS (TSMC advanced packaging, k wafers/month):** ~14 (end-2023) → ~35 (2024)
→ ~78 (2025, record) → 90–150 (2026E, wide range; CoWoS-L/S fully booked).
~10× in three years, demand still outpacing supply. Source: TrendForce.

**HBM (TAM $B):** ~$5.5B (2023) → ~$17B (2024) → ~$35B (2025) → ~$100B (2028E,
~40% CAGR). Q3'25 share: SK Hynix 57% / Micron 21% / Samsung 22%; suppliers sold
out through 2026; Micron 2026 HBM run-rate ~$8B. Sources: TrendForce, Astute
Group, Silicon Analysts.

**Supply→demand model (illustrative):** CoWoS k-wpm × 12 × *effective
accelerators/wafer* (default 7; theoretical max ~16 B200 / ~25-29 Hopper, net of
yield/ramp/shared usage). 2025 ceiling ~6.6M/yr vs Big-4 capex-implied demand
~5.7M (~87% of global ceiling **before** NeoClouds/sovereign/enterprise). Flagged
order-of-magnitude, not a forecast. Ties back to Microsoft's ~$25B 2026
memory-cost callout = the bottleneck leaking into price.

## To add next
- Gigawatt-scale power & data-center commitments (cross-provider) — the *next*
  binding constraint after packaging/memory.
- HBM4 transition (2026+) and CoWoP / OSAT outsourcing (ASE) as capacity relief.
