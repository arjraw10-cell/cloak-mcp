"""Pilot numbers and the Phase 2 projection. usage: python pilot_report.py"""
import json
from collections import defaultdict
from statistics import mean

import bench
import tasks as T

runs = [r for r in bench.read_jsonl(bench.RUNS) if r["phase"] == "pilot"]
calls = defaultdict(list)
for c in bench.read_jsonl(bench.CALLS):
    calls[c["run_id"]].append(c)
api_errors = [r for r in bench.read_jsonl(bench.API_ERRORS) if r["phase"] == "pilot"]

print("| run | status | pass | calls | tool errs | tokens in (cached) | out | wall s | cost $ |")
print("|---|---|---|---|---|---|---|---|---|")
for r in sorted(runs, key=lambda r: (r["config"], r["model"], r["task"])):
    print(f"| {r['config']} / {r['model']} / {r['task']} | {r['status']} | {'Y' if r['passed'] else 'N'} | {r['n_calls']} "
          f"| {r['n_tool_errors']} | {r['tokens_in']:,} ({r['cache_read']:,}) | {r['tokens_out']:,} | {r['wall_s']} | {r['cost_usd']:.4f} |")

full_runs_per_combo = len(T.TASKS) * 2
print(f"\nPer config (Phase 2 = {len(T.TASKS)} tasks x 2 repeats = {full_runs_per_combo} runs per row; 4 workers)")
print("| config / model | pilot runs | passed | avg tokens in | avg out | avg wall s | avg $/run | projected $ | projected run-hours | runs with >100K requests |")
print("|---|---|---|---|---|---|---|---|---|---|")
groups = defaultdict(list)
for r in runs:
    groups[(r["config"], r["model"])].append(r)
for (cfg, model), rs in sorted(groups.items()):
    c, w = mean(r["cost_usd"] for r in rs), mean(r["wall_s"] for r in rs)
    print(f"| {cfg} / {model} | {len(rs)} | {sum(r['passed'] for r in rs)} | {mean(r['tokens_in'] for r in rs):,.0f} "
          f"| {mean(r['tokens_out'] for r in rs):,.0f} | {w:.0f} | {c:.4f} | {c * full_runs_per_combo:.2f} "
          f"| {w * full_runs_per_combo / 3600:.2f} | {sum(r.get('n_long_ctx_requests', 0) > 0 for r in rs)} |")
print(f"\npilot API-error records: {len(api_errors)}; total spent so far (all phases): ${bench.spent():.4f}")
