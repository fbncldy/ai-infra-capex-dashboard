@echo off
REM Double-click to launch the AI Infrastructure Capex dashboard locally.
cd /d "%~dp0"
set PYTHONUTF8=1
".venv\Scripts\streamlit.exe" run "dashboard\app.py"
pause
