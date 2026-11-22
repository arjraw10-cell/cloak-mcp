# Starts bench.py (with these arguments) as a scheduled task that runs only when the owner is logged on,
# so the browsers open headed on the desktop and the run survives SSH disconnects.
# usage: powershell -File launch.ps1 pilot --bonus glm-5.3-flash
$cmd = "C:\Users\arjra\Documents\browser-mcp-bench\bench_task.cmd " + ($args -join ' ')
schtasks /create /tn BrowserMcpBench /tr $cmd /sc once /st 00:00 /it /f 2>$null | Out-Null
schtasks /run /tn BrowserMcpBench
