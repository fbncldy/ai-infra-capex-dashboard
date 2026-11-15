"""Minimal SEC EDGAR client for the build scripts.

SEC's fair-access policy requires a User-Agent with a contact. It is read from
the SEC_USER_AGENT environment variable so no personal address lives in the
code. On Windows set it once, in your own terminal:
    setx SEC_USER_AGENT "AI Value Chain research <your address>"
(a process environment variable of the same name takes precedence).
"""
from __future__ import annotations

import datetime as dt
import json
import os
import time
import urllib.request

BASE = "https://data.sec.gov/api/xbrl"


def _user_env(name: str) -> str:
    """Windows user-scope environment variable (set via setx), read from the
    registry so it works in shells started before it was set."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
            return str(winreg.QueryValueEx(k, name)[0])
    except (ImportError, OSError):
        return ""


def _headers() -> dict[str, str]:
    ua = (os.environ.get("SEC_USER_AGENT") or _user_env("SEC_USER_AGENT")).strip()
    if not ua:
        raise SystemExit("SEC_USER_AGENT is not set; see model/edgar.py")
    if "example.com" in ua:
        raise SystemExit("SEC_USER_AGENT still holds the example address")
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
