# AI Infrastructure Capex Dashboard

A supply-side intelligence view of AI infrastructure spend across the compute
value chain — built as a Technical Intelligence proof-of-work.

**What it shows**
- Full-breadth map of the AI compute value chain (silicon → foundry → systems →
  power/DC → cloud → NeoClouds → AI labs) and each layer's bottleneck.
- A rigorous **hyperscaler capex deep-dive**, anchored on Alphabet figures
  extracted and cross-validated directly from 10-K filings.
- An interactive model: adjustable AI-attributable share and blended unit cost
  that translate headline capex into AI-specific spend and implied accelerator
  volumes.
- Full source/assumption transparency — every number is typed by provenance.

## Run it

```powershell
# from this folder
.venv\Scripts\streamlit run dashboard\app.py
```

Then open the URL Streamlit prints (default http://localhost:8501).

## Project layout

```
data/raw/          annual reports & 10-Ks (source PDFs)
data/processed/    cleaned CSVs the dashboard reads
model/             extraction scripts (pdfplumber)
dashboard/app.py   the Streamlit dashboard
notes/             sourcing log + assumptions
```

## Data integrity

| source_type | meaning |
|-------------|---------|
| `10-K (extracted)` | parsed from filings in `data/raw`, cross-validated across years |
| `public (verify)`  | public placeholder, pending primary-source extraction |

See `notes/sources.md` for the full provenance log.

## Hardening roadmap
1. Drop Microsoft / Amazon / Meta 10-Ks into `data/raw/<company>/` and extend
   `model/extract_capex2.py` to replace the placeholders.
2. Add NeoCloud backlog and gigawatt-scale power commitments.
3. Add upstream supply (TSMC CoWoS, HBM) to model the binding constraint.
4. Deploy to Streamlit Community Cloud for a shareable link.
