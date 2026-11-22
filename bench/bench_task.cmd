@echo off
rem Runs bench.py with the given arguments; launched by launch.ps1 as a scheduled task in the desktop session.
cd /d C:\Users\arjra\Documents\browser-mcp-bench
if not exist results\raw mkdir results\raw
.venv\Scripts\python.exe -u bench.py %* >> results\raw\console.log 2>&1
