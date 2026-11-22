"""Build data/processed/telco_tsr.csv: total shareholder return inputs.

Yahoo Finance daily adjusted closes (dividends reinvested). One row per year
at the first trading day of January (2015 = the index base), plus the latest
close as a final row with its date in `note`. Raw responses are cached in
data/raw/yahoo/.

Run from the project root:  python model/build_telco_tsr.py
"""
from __future__ import annotations

import datetime as dt
import json
import time
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "yahoo"
OUT = ROOT / "data" / "processed" / "telco_tsr.csv"
TICKERS = {"AT&T": "T", "Verizon": "VZ", "Deutsche Telekom": "DTE.DE",
           "BT Group": "BT-A.L", "MSCI World (URTH)": "URTH"}
START = int(dt.datetime(2014, 12, 15, tzinfo=dt.timezone.utc).timestamp())


def fetch(symbol: str) -> pd.Series:
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
           f"?period1={START}&period2={int(time.time())}&interval=1d"
           f"&events=div,split")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.load(r)
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / f"{symbol}.json").write_text(json.dumps(data))
    res = data["chart"]["result"][0]
    idx = pd.to_datetime(res["timestamp"], unit="s").normalize()
    s = pd.Series(res["indicators"]["adjclose"][0]["adjclose"], index=idx)
    return s.dropna()


def main() -> None:
    rows = []
    for co, sym in TICKERS.items():
        s = fetch(sym)
        for y in range(2015, s.index.max().year + 1):
            first = s[s.index.year == y]
            if len(first):
                rows.append((co, y, round(first.iloc[0], 2), "reported",
                             f"first trading day {first.index[0]:%Y-%m-%d}"))
        last = s.index.max()
        rows.append((co, round(last.year + (last.dayofyear - 1) / 365, 2),
                     round(s.iloc[-1], 2), "reported",
                     f"latest {last:%Y-%m-%d}"))
        time.sleep(1)
    df = pd.DataFrame(rows, columns=["company", "year", "adj", "source_type",
                                     "note"])
    df.to_csv(OUT, index=False)
    print(df.groupby("company").tail(2).to_string(index=False))


if __name__ == "__main__":
    main()
