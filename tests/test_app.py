"""Smoke test: the dashboard must render without exceptions.

Run: python tests/test_app.py (used by CI on every push).
"""
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "dashboard" / "app.py"


def main():
    at = AppTest.from_file(str(APP), default_timeout=120).run()
    if at.exception:
        print("FAIL: app raised an exception")
        for e in at.exception:
            print(e)
        sys.exit(1)
    n_tabs = len(at.tabs)
    if n_tabs < 10:
        print(f"FAIL: expected at least 10 tabs, got {n_tabs}")
        sys.exit(1)
    print(f"PASS: {n_tabs} tabs, {len(at.metric)} metrics, "
          f"{len(at.dataframe)} dataframes rendered without errors")


if __name__ == "__main__":
    main()
