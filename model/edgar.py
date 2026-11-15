"""Minimal SEC EDGAR client for the build scripts.

SEC's fair-access policy requires a User-Agent with a contact. It is read from
the SEC_USER_AGENT environment variable so no personal address lives in the
code; set it in your shell profile, e.g.
    export SEC_USER_AGENT="AI Value Chain research <you@example.com>"
"""
from __future__ import annotations

import datetime as dt
import json
import os
import time
import urllib.request

BASE = "https://data.sec.gov/api/xbrl"


def _headers() -> dict[str, str]:
    ua = os.environ.get("SEC_USER_AGENT", "").strip()
    if not ua:
        raise SystemExit("SEC_USER_AGENT is not set; see model/edgar.py")
    return {"User-Agent": ua}


def get(url: str) -> dict:
    req = urllib.request.Request(url, headers=_headers())
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.load(r)
    time.sleep(0.25)                      # stay well under SEC's rate limit
    return data


def company_facts(cik: int) -> dict:
    return get(f"{BASE}/companyfacts/CIK{cik:010d}.json")


def annual(facts: dict, tags: list[str], taxonomy: str = "us-gaap",
           forms: tuple[str, ...] = ("10-K", "20-F")) -> dict[int, float]:
    """Annual values ($B) keyed by fiscal-year-end year, first tag that has data.
    Prefers the as-originally-reported figure (fy == end year)."""
    for tag in tags:
        try:
            units = facts["facts"][taxonomy][tag]["units"]["USD"]
        except KeyError:
            continue
        out: dict[int, dict[bool, float]] = {}
        for u in units:
            s, e = u.get("start"), u.get("end")
            if not s or u.get("form") not in forms:
                continue
            days = (dt.date.fromisoformat(e) - dt.date.fromisoformat(s)).days
            if 350 <= days <= 380:
                y = int(e[:4])
                out.setdefault(y, {})[u.get("fy") == y] = u["val"] / 1e9
        if out:
            return {y: v.get(True, v.get(False)) for y, v in out.items()}
    return {}
