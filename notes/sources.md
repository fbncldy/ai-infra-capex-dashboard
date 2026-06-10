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

## Power & data centers — `gigawatt_projects.csv`

The constraint that bites *after* packaging/memory. You can buy chips in months;
a high-voltage substation takes 3–5 years.

**Flagship GW-scale projects (announced/planned capacity):** Stargate
(OpenAI/Oracle/SoftBank) ~7 GW across 8 US sites, >$400B committed; Meta Hyperion
(LA) 5 GW (2 GW by 2030 → 5 GW); xAI Colossus (Memphis) ~2 GW, ~555k GPUs; Meta
Prometheus (OH) 1 GW online 2026; Anthropic–Amazon New Carlisle (IN) ~1 GW;
Microsoft Fairwater ~1 GW. Named total ~17 GW. Figures are site totals at varying
horizons, not installed base. Sources: NextBigFuture, Introl, Sherwood, Data
Center Knowledge.

**Macro context:** global DC capacity ~103 → ~200 GW by 2030 (~2×); Goldman —
data-center power demand +165% by 2030 (vs 2023), ~$720B grid spend needed
through 2030; HV-substation lead times 3–5 yrs; 7 of 13 US grid regions below
safety margins by 2030 (E. Schmidt: +29 GW by 2027, +67 GW more by 2030).
Sources: Goldman Sachs, IEA, Belfer Center, WEF.

## Value-chain player financials (added)

- **Foundry — TSMC** (`foundry_players.csv`): revenue $75.9B (2022) → $69.3B
  (2023 downturn) → $90.1B (2024) → $122B (2025); capex $30–40B, 2026E guide
  $52–56B. CoWoS ≈ 7–9% of revenue. Source: TSMC results (SEC 6-K).
- **Systems** (`systems_vendors.csv`): Dell ISG $43.6B (FY25, incl storage),
  Supermicro ~$22B (+47%), HPE server ~$19B. ODMs (Foxconn/Quanta/Wistron)
  dominate AI-server volume but under-disclose. Sources: Dell/SMCI/HPE results.
- **Networking** (`networking_vendors.csv`): Arista $9.0B (AI/DC pure-play),
  Ciena $4.77B (optical), Nokia €19.9B/~$21.5B total (NI +9%), Cisco $56.7B
  total (Networking +12%). Cisco/Nokia totals are diversified — flagged.

## Data-center construction crossover (`dc_construction.csv`)

US Census: data-center construction ~$9B (2020) → ~$41B (2025, +344%); office
~$72B → ~$49B (lowest since 2015). Monthly run-rate crossed Dec-2025 (DC ~$45B >
office ~$44B). Mid-years interpolated between Census anchors. Sources: US Census,
Wolf Street.

## AI labs — revenue & capability (`ai_lab_revenue.csv`, `llm_benchmark.csv`)

Annualized run-rate: Anthropic $47B (May-26, overtook OpenAI; $1B→$47B in ~18mo),
OpenAI $25B (Feb-26), xAI $0.43B (Q3-25), Mistral $0.40B (Jan-26). Source: Epoch
AI revenue dataset. Capability: GPQA-Diamond best-frontier ~39% (GPT-4, 2023) →
94.3% (Gemini 3.1 Pro, Feb-26); MMLU saturated ~93%; PhD-expert baseline ~65%.
Representative best-published scores; Source: Epoch AI Benchmarking Hub /
leaderboards (approximate).

## Expanded historical datasets (2020→today)

- **Silicon** (`silicon_revenue.csv`): NVIDIA / AMD / Broadcom / Micron total
  revenue by fiscal year (reported; FY offsets noted). NVIDIA DC segment ~$115B
  FY25. Replaced the earlier HBM TAM chart per request (revenues, not TAM).
- **Foundry** (`foundry_players.csv`): TSMC / GlobalFoundries / UMC revenue +
  capex 2020-25 (separate charts). TSMC ~70% share; Samsung/Intel foundry omitted
  (loss-making segments). Source: company filings (SEC).
- **Servers** (`systems_vendors.csv`): Dell ISG / Supermicro / HPE server revenue
  by fiscal year; Supermicro 2026 = company target (guidance); HPE partly est.
  ODMs (Foxconn/Quanta/Wistron) noted, not charted.
- **Networking** (`networking_vendors.csv`): Arista, Ciena (pure-plays) + Nokia
  **Network Infrastructure segment only** (excl mobile). Cisco Networking
  (~$28-30B) noted but omitted to keep comparison clean.
- **AI demand:** `chatgpt_users.csv` (WAU 100M Aug-23 → 900M Feb-26, OpenAI
  disclosures); `llm_benchmark_by_lab.csv` (best GPQA-Diamond by lab — OpenAI/
  Anthropic/Google/Meta/DeepSeek — representative best-published, approximate).
- **Telecoms** (`telecom_capex.csv`, `telecom_players.csv`): global telecom capex
  ~$300B flat / $295B 2024 lowest since 2011 (MTN Consulting) vs Big-4
  hyperscaler capex overtaking it; major US/EU operator revenue+capex (latest yr,
  some approx; DT overlaps T-Mobile US). Sources: company filings, MTN Consulting.

## Additions of 2026-06-04

- **Oracle** added to the hyperscaler set (now Big-5): annual capex from EDGAR
  XBRL (CIK 0001341439, FY ends May 31; FY2025 $21.2B), 2026 guidance ~$50B
  (raised by $15B during FY26; RPO $553B). Big-5 FY25 $379B (+69% vs FY24
  $224B); 2026E guidance midpoints sum to ~$760B.
- **Quarterly capex** (`hyperscaler_capex_quarterly.csv`): derived from 10-Q/10-K
  XBRL year-to-date cash-flow values by differencing within each fiscal year;
  validated to sum exactly to reported annuals (Alphabet and Meta 2025 checked).
  Alphabet quarterly also from EDGAR XBRL (annual stays PDF-extracted).
- **Accelerator vendor revenue** (`accelerator_dc_revenue.csv`): NVIDIA
  data-center segment by FY mapped to calendar year (FY2026 $194B -> CY2025);
  AMD data-center segment from 2022 (first reported). Source: company filings.
- **US telecom series** (`telecom_us_series.csv`): AT&T / Verizon / T-Mobile US
  revenue + capex 2020-2024, reported figures (AT&T pre-2022 includes
  WarnerMedia). EU operators remain a 2024 snapshot; their group reports use
  differing capex definitions (cash capex vs eCapex) so a clean series needs
  the annual reports directly.
- **Benchmarks hardened** (`llm_benchmark_by_lab.csv`): scores now from model /
  system cards where published (GPT-4 35.7 GPQA paper; Claude 3.5 Sonnet 59.4;
  o1 78.0; Claude Opus 4 79.6; Gemini 2.5 Pro 84.0; Llama 3.1 405B 50.7;
  Llama 4 Maverick 69.8; DeepSeek V3 59.1 / R1 71.5). Two estimate rows remain,
  flagged (Gemini 1.0, 2026 Chinese frontier).
- **Construction hardened** (`dc_construction.csv`): DC 2023 ($20B) and 2024
  ($31B) now derived from Census-reported growth rates (Wolf Street); 2021-22
  and office mid-years remain interpolated, flagged.
- **CI**: GitHub Action (.github/workflows/ci.yml) runs tests/test_app.py
  (Streamlit AppTest smoke test) on every push.

## Additions of 2026-06-04 (second round)

- **Capex funding** (`hyperscaler_ocf.csv`): annual operating cash flow for the
  Big-5 from EDGAR XBRL (NetCashProvidedByUsedInOperatingActivities), built by
  `model/build_capex_dataset.py`. FY2025 capex/OCF: Oracle 102%, Amazon 94%,
  Meta 60%, Alphabet 56%, Microsoft 47%. Bond context: hyperscalers issued
  $121B of bonds in 2025 vs ~$28B five-year average; Meta $30B (largest
  corporate since 2023); Alphabet 100-year bond; sub-5% average rates. Sources:
  Janus Henderson, Wolf Street (2026-02-07), Yahoo Finance.
- **Exec summary rewritten** to the funding-constraint framing. Checked claims:
  IEA World Energy Investment 2025 (upstream oil & gas ~$570B, total fossil
  ~$1.1T); ChatGPT conversion ~5-6% (OpenAI: ~50M paying subscribers Apr 2026 vs
  900M WAU); capex/revenue ~30-75% across the five.
- **System Integrators tab** (`system_integrators.csv`,
  `accenture_genai_bookings.csv`): Accenture $44.3B (FY20) to $69.7B (FY25,
  reported); TCS $22.2B to $30.2B; Infosys $13.6B to $19.3B (both FY ends
  March, reported); Capgemini in USD-converted EUR (estimate-flagged).
  Accenture GenAI new bookings: ~$3B FY24, $5.9B FY25 (quarterly $1.2B to
  $1.8B). Sources: company results, Accenture 8-K (EDGAR).

## To add next
- HBM4 transition (2026+) and CoWoP / OSAT outsourcing (ASE) as capacity relief.
- Behind-the-meter power deals (nuclear/SMR, gas) by operator.
- EU telecom 2020-2024 series from annual reports (definitions differ by firm).
