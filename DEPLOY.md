# Deploying to Streamlit Community Cloud

The repo is committed locally on branch `main` and ready to push. These are the
steps that need your accounts (run them in your own terminal where you're signed
in to GitHub).

## 1. Create the GitHub repo

Option A — github.com (no CLI):
1. Go to https://github.com/new
2. Owner: **fbncldy**, name: `ai-infra-capex-dashboard` (or your choice).
3. **Public** (Streamlit Community Cloud needs a public repo on the free tier).
4. Do **not** add a README/.gitignore/license (we already have them).
5. Create repository.

## 2. Push this repo

From `Desktop\AI Infrastructure` (PowerShell):

```powershell
git remote add origin https://github.com/fbncldy/ai-infra-capex-dashboard.git
git push -u origin main
```

If prompted to authenticate, complete the GitHub sign-in (browser or token).

## 3. Deploy on Streamlit Community Cloud

1. Go to https://share.streamlit.io and sign in **with GitHub**.
2. **Create app** → **Deploy a public app from GitHub**.
3. Repository: `fbncldy/ai-infra-capex-dashboard`
   - Branch: `main`
   - Main file path: `dashboard/app.py`
4. **Deploy.** First build installs `requirements.txt` (~1–2 min).

You'll get a public URL like
`https://ai-infra-capex-dashboard-fbncldy.streamlit.app` — that's the link for
your application.

## Notes
- The deployed app only needs `data/processed/*.csv` (committed). The large
  Alphabet 10-K PDFs are intentionally **git-ignored** — they're only used by the
  offline extraction pipeline, not the live app.
- To refresh data later: update the CSVs (or re-run `model/build_capex_dataset.py`
  with the raw files present), commit, and `git push`. Streamlit auto-redeploys.
- `requirements.txt` is the lean runtime set (streamlit/pandas/plotly).
  `requirements-dev.txt` adds the PDF-extraction deps for local pipeline work.
