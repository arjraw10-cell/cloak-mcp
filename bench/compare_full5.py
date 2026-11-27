"""Kairos across all reruns -> results/compare_full5.md. usage: python compare_full5.py
full and full2 = v1 ac28cd7 (run twice: the noise band), full3 = v2 116efbc, full4 = v2.1 0367e99, full5 = f1ff3f8."""
import json
import math
from collections import defaultdict
from statistics import mean, median

import bench
import server

PHASES = [("full", "v1"), ("full2", "v1 rerun"), ("full3", "v2"), ("full4", "v2.1"), ("full5", "f1ff3f8")]
MODELS = [bench.CORE_MODEL, "glm-5.3-flash", "gpt-6-luna", "gpt-6.1-sol"]
CATS = ["basic", "forms", "dialogs", "frames-tabs", "large", "dynamic"]
runs = [r for r in bench.read_jsonl(bench.RUNS) if r["phase"] in dict(PHASES) and r["config"] == "kairos"]
calls = [c for c in bench.read_jsonl(bench.CALLS) if c["config"] == "kairos" and c["run_id"].split(".")[0] in dict(PHASES)]


def wilson(k, n, z=1.96):  # same 95% interval as analyze.py
    p, d = k / n, 1 + z * z / n
    c, h = (p + z * z / (2 * n)) / d, z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0, c - h), min(1, c + h)


def pick(phase, model, cat=None, task=None):
    return [r for r in runs if r["phase"] == phase and r["model"] == model
            and (cat is None or r["cat"] == cat) and (task is None or r["task"] == task)]


def row(rs):
    if not rs:
        return ["-"] * 7
    k, n = sum(r["passed"] for r in rs), len(rs)
    lo, hi = wilson(k, n)
    ok, large = [r for r in rs if r["passed"]], [r for r in rs if r["cat"] == "large"]
    return [str(n), f"{100 * k / n:.0f}% ({100 * lo:.0f}-{100 * hi:.0f})", str(sum(r["status"] == "timeout" for r in rs)),
            f"{mean(r['n_tool_errors'] for r in rs):.2f}",
            f"{mean(r['tokens_in'] + r['tokens_out'] for r in ok):,.0f}" if ok else "-",
            f"{mean(r['tokens_in'] + r['tokens_out'] for r in large):,.0f}" if large else "-",
            f"{mean(r['n_calls'] for r in rs):.1f}"]


def tool_events(r):
    """[(tool, raw_args, result_text)] in call order, from a Kairos run's event transcript."""
    out, pending = [], []
    for line in (bench.RAW / "transcripts" / f"{r['run_id']}.jsonl").read_text(encoding="utf-8").splitlines():
        try:
            o = json.loads(line)
        except json.JSONDecodeError:
            continue
        if o.get("k") == "assistant":
            pending += o.get("calls") or []
        elif o.get("k") == "end" and pending:
            name, args = pending.pop(0)
            d = json.loads(o["result"])
            out.append((name, args, d.get("output") or d.get("error") or ""))
    return out


md = ["# Kairos across the reruns", "",
      "Same 30 tasks, checkers, fixtures, prompts, limits and seeded run order in every phase. Kairos versions:",
      "`full` and `full2` = v1 ac28cd7 (the same code run twice: their difference is the noise band), `full3` = v2",
      "116efbc, `full4` = v2.1 0367e99, `full5` = f1ff3f8 (adds 328f1a3: `browser_console` refuses while a dialog is",
      "open; 0310529/a9820da: `browser_type` retypes once without CloakBrowser's typos when stray letters are left).",
      "Large-page tokens = mean tokens (in + out) per run over the 5 large-page tasks.", ""]
head = "| run | runs | success (95% CI) | hangs | tool errors/run | tokens/success | large-page tokens/run | calls/task |"
for model in MODELS:
    md += [f"## {model}", "", head, "|---|---|---|---|---|---|---|---|"]
    md += [f"| {ph} ({label}) | " + " | ".join(row(pick(ph, model))) + " |" for ph, label in PHASES]
    md.append("")
md += ["## Per category, claude-haiku-5-5 (tokens per success)", "",
       "| category | " + " | ".join(ph for ph, _ in PHASES) + " |", "|---|" + "---|" * len(PHASES)]
for cat in CATS:
    md.append(f"| {cat} | " + " | ".join(row(pick(ph, bench.CORE_MODEL, cat=cat))[4] + f" ({row(pick(ph, bench.CORE_MODEL, cat=cat))[1].split(' ')[0]})"
                                         for ph, _ in PHASES) + " |")

# Fix 1: dyn-spa-create. Names created, and browser_type latency (a retype shows as a longer type call).
md += ["", "## dyn-spa-create: created names and browser_type latency (all models)", "",
       "| run | runs | runs with a name other than \"Orion\" | browser_type calls | median latency s | max latency s |",
       "|---|---|---|---|---|---|"]
odd = defaultdict(list)
for ph, label in PHASES:
    rs = [r for r in runs if r["phase"] == ph and r["task"] == "dyn-spa-create"]
    for r in rs:
        names = [e["data"].get("name") for e in server.events_for(r["token"]) if e["event"] == "create"]
        if any(n != "Orion" for n in names):
            odd[ph].append(f"`{r['run_id']}` created {names}")
    lat = [c["latency_s"] for c in calls if c["task"] == "dyn-spa-create" and c["tool"] == "browser_type"
           and c["run_id"].split(".")[0] == ph and c.get("latency_s") is not None]
    md.append(f"| {ph} ({label}) | {len(rs)} | {len(odd[ph])} | {len(lat)} | "
              + (f"{median(lat):.1f} | {max(lat):.1f} |" if lat else "- | - |"))
md += [""] + [f"- {ph}: {x}" for ph, _ in PHASES for x in odd[ph]]

# Fix 2: dialogs-welcome. browser_console calls made while the alert was open, and silent exits.
md += ["", "## dialogs-welcome: browser_console while the alert is open, and silent exits (all models)", ""]
for ph, label in PHASES:
    rs = [r for r in runs if r["phase"] == ph and r["task"] == "dialogs-welcome"]
    cons = []
    for r in rs:
        for name, args, res in tool_events(r):
            if name == "browser_console":
                cons.append(f"`{r['run_id']}`: {res[:140]!r}")
        # a call that started but never ended (the process died or was killed during it)
    lost = [c for c in calls if c["task"] == "dialogs-welcome" and c["run_id"].split(".")[0] == ph and c.get("latency_s") is None]
    errs = [r for r in rs if r["status"] == "error"]
    md.append(f"- {ph} ({label}): {len(rs)} runs, {sum(r['passed'] for r in rs)} passed, {len(cons)} browser_console calls, "
              f"{len(lost)} calls that never returned, {len(errs)} runs ending in status error"
              + (f" (exit codes {[r.get('exit_code') for r in errs]})" if errs else ""))
    md += [f"  - console: {x}" for x in cons]
    md += [f"  - never returned: `{c['run_id']}` call {c['idx']} {c['tool']}" for c in lost]

# Exit codes recorded from full5 on.
full5 = [r for r in runs if r["phase"] == "full5"]
codes = defaultdict(int)
for r in full5:
    codes[r.get("exit_code")] += 1
md += ["", "## full5 child-process exit codes", "", f"- {dict(codes)} (status error: "
       f"{[r['run_id'] for r in full5 if r['status'] == 'error'] or 'none'})"]

md += ["", "## Every full5 failure", ""]
md += [f"- `{r['run_id']}`: {r['status']}, exit code {r.get('exit_code')}, {r['reason']}"
       for r in sorted(full5, key=lambda r: r["run_id"]) if not r["passed"]] or ["- none"]
(bench.ROOT / "results" / "compare_full5.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print("\n".join(md))
