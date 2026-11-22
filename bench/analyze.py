"""Builds results/summary.md from the raw logs. usage: python analyze.py [phase]   (default: full)"""
import json
import math
import sys
from collections import defaultdict
from statistics import mean, median

import bench

PHASE = sys.argv[1] if len(sys.argv) > 1 else "full"
runs = [r for r in bench.read_jsonl(bench.RUNS) if r["phase"] == PHASE]
# v1 ("full") was measured with cloak-mcp 96aa864; schema_tokens.json now holds the current (v2) numbers.
v1_schema = bench.ROOT / "results" / "schema_tokens_v1.json"
schema = json.loads((v1_schema if PHASE == "full" and v1_schema.is_file()
                     else bench.ROOT / "results" / "schema_tokens.json").read_text())
api_errors = [r for r in bench.read_jsonl(bench.API_ERRORS) if r["phase"] == PHASE]


def wilson(k, n, z=1.96):
    if n == 0:
        return 0, 0
    p, d = k / n, 1 + z * z / n
    c, h = (p + z * z / (2 * n)) / d, z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0, c - h), min(1, c + h)


def table(rows, key, title):
    groups = defaultdict(list)
    for r in rows:
        groups[key(r)].append(r)
    out = [f"### {title}", "",
           "| group | runs | success (95% CI) | per-repeat success | timeout rate | tool errors/run | tokens per success "
           "| tool calls/task | median wall s | $/run | runs with >100K-token requests |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    for g, rs in sorted(groups.items()):
        k, n = sum(r["passed"] for r in rs), len(rs)
        lo, hi = wilson(k, n)
        reps = defaultdict(list)
        for r in rs:
            reps[r["repeat"]].append(r["passed"])
        per_rep = " / ".join(f"{100 * mean(v):.0f}%" for _, v in sorted(reps.items()))
        ok = [r for r in rs if r["passed"]]
        tps = f"{mean(r['tokens_in'] + r['tokens_out'] for r in ok):,.0f}" if ok else "-"
        out.append(f"| {g} | {n} | {100 * k / n:.0f}% ({100 * lo:.0f}-{100 * hi:.0f}) | {per_rep} "
                   f"| {100 * mean(r['status'] == 'timeout' for r in rs):.0f}% | {mean(r['n_tool_errors'] for r in rs):.2f} "
                   f"| {tps} | {mean(r['n_calls'] for r in rs):.1f} | {median(r['wall_s'] for r in rs):.0f} "
                   f"| {mean(r['cost_usd'] for r in rs):.4f} | {sum(r.get('n_long_ctx_requests', 0) > 0 for r in rs)} |")
    return "\n".join(out) + "\n"


def excerpt(run_id, n=12):
    path = bench.RAW / "transcripts" / f"{run_id}.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    keep = [l for l in lines if '"tool_use"' in l or '"tool_result"' in l or '"k": "start"' in l
            or '"k": "end"' in l or '"k": "assistant"' in l or '"type":"result"' in l]
    return "\n".join(l[:300] for l in keep[-n:])


core = [r for r in runs if r["model"] == bench.CORE_MODEL]
md = [f"# Results ({PHASE} phase)", "",
      f"{len(runs)} finished runs, {len(api_errors)} API-error records (re-queued, not counted), "
      f"total spend ${bench.spent():.2f}.", "",
      "Wall-clock times are confounded: cloak-mcp, devinwangd and Kairos use humanized (deliberately slower) input; "
      "Playwright MCP does not.", ""]
# hand-written findings, kept separate so the summary stays generated
notes = bench.ROOT / "results" / ("notes.md" if PHASE == "full" else f"notes_{PHASE}.md")
if notes.is_file():
    md += [notes.read_text(encoding="utf-8")]
md += ["## Static tool-schema cost", "", "| layer | tools | Anthropic tokens | tiktoken o200k |", "|---|---|---|---|"]
md += [f"| {k} | {v['tools']} | {v['anthropic_tokens'] or '-'} | {v['tiktoken_o200k']} |" for k, v in schema.items()]
all_runs = bench.read_jsonl(bench.RUNS) + bench.read_jsonl(bench.API_ERRORS)
by_model = defaultdict(float)
for r in all_runs:
    by_model[r["model"]] += r.get("cost_usd") or 0
md += ["", "## Spend by model (all phases, including pilot, dev checks and API-error runs)", "",
       "| model | $ |", "|---|---|"] + [f"| {m} | {v:.4f} |" for m, v in sorted(by_model.items())]
md += ["", "## Core comparison (all claude-haiku-5-5, effort low)", "",
       table(core, lambda r: r["config"], "Per config"),
       "## Per config x category (core)", "",
       table(core, lambda r: f"{r['config']} / {r['cat']}", "Per config and category"),
       "## Kairos native browser tools across models (not compared head-to-head with Claude Code)", "",
       table([r for r in runs if r["config"] == "kairos"], lambda r: r["model"], "Per model (Kairos)")]

# Where a config failed a task that another core config passed at least once.
by_task = defaultdict(lambda: defaultdict(list))
for r in core:
    by_task[r["task"]][r["config"]].append(r["passed"])
md += ["## Per task (core, passes / runs)", "", "| task | " + " | ".join(bench.CORE) + " |",
       "|---|" + "---|" * len(bench.CORE)]
for task, cfgs in sorted(by_task.items()):
    md.append(f"| {task} | " + " | ".join(f"{sum(cfgs[c])}/{len(cfgs[c])}" if cfgs[c] else "-" for c in bench.CORE) + " |")
md += ["", "## Where cloak-mcp / Kairos lose (tasks where another core config passed more often)", ""]
for task, cfgs in sorted(by_task.items()):
    for mine in ("cc-cloak", "kairos"):
        if cfgs[mine]:
            better = [c for c in bench.CORE if c != mine and cfgs[c] and mean(cfgs[c]) > mean(cfgs[mine])]
            if better:
                md.append(f"- {mine} on `{task}`: {sum(cfgs[mine])}/{len(cfgs[mine])}, beaten by "
                          + ", ".join(f"{c} {sum(cfgs[c])}/{len(cfgs[c])}" for c in better))

# Checker sensitivity (not the official score): answer-task failures where an accepted answer appears
# inside the given answer, e.g. "July 12, 1904 in Parral, Chile" for "July 12, 1904".
import tasks as T
loose = defaultdict(list)
for r in runs:
    acc = T.BY_ID[r["task"]]["check"].get("answer")
    if acc and not r["passed"] and r.get("final_answer") and any(T.norm(x) in T.norm(r["final_answer"]) for x in acc):
        loose[f"{r['config']} / {r['model']}"].append(f"{r['task']}: {r['final_answer']!r}")
md += ["## Checker sensitivity", "", "Failed answer tasks that a looser 'contains the accepted answer' check would pass "
       "(the official score keeps the pre-written exact check):", ""]
md += [f"- {k}: {len(v)} ({'; '.join(v[:4])})" for k, v in sorted(loose.items())] or ["- none"]
md.append("")

# Failure candidates: failed runs on tasks that some other config passed, timeouts first.
fails = [r for r in core if not r["passed"] and any(any(v) for c, v in by_task[r["task"]].items() if c != r["config"])]
fails.sort(key=lambda r: (r["status"] != "timeout", r["config"]))
md += ["", "## Failure candidates (pick the 5 most informative for the write-up)", ""]
for r in fails[:15]:
    md += [f"### {r['run_id']}", f"status `{r['status']}`, {r['n_calls']} calls, {r['n_tool_errors']} tool errors: {r['reason']}",
           "```", excerpt(r["run_id"]), "```", ""]
(bench.ROOT / "results" / ("summary.md" if PHASE == "full" else f"summary_{PHASE}.md")).write_text("\n".join(md), encoding="utf-8")
print("\n".join(md[:60]))
