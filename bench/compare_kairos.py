"""Kairos v1 (phases full, full2; Kairos ac28cd7) vs v2 (phase full3; Kairos 116efbc) -> results/compare_kairos.md.
full -> full2 ran the same Kairos code, so their drift is the noise band. usage: python compare_kairos.py"""
import json
import math
from collections import defaultdict
from statistics import mean

import bench

PHASES = [("full", "v1 (full)"), ("full2", "v1 (full2)"), ("full3", "v2 (full3)")]
MODELS = [bench.CORE_MODEL, "glm-5.3-flash", "gpt-6-luna", "gpt-6.1-sol"]
CATS = ["basic", "forms", "dialogs", "frames-tabs", "large", "dynamic"]
COLS = ["success", "hangs", "tool errors/run", "tokens/success", "calls/task", "$/run"]
runs = [r for r in bench.read_jsonl(bench.RUNS) if r["phase"] in dict(PHASES)]
calls = [c for c in bench.read_jsonl(bench.CALLS) if c["run_id"].split(".")[0] in dict(PHASES)]
schema = {p: json.loads((bench.ROOT / "results" / f).read_text())
          for p, f in (("v1", "schema_tokens_v1.json"), ("v2", "schema_tokens_full3.json"))}


def wilson(k, n, z=1.96):  # same 95% interval as analyze.py
    p, d = k / n, 1 + z * z / n
    c, h = (p + z * z / (2 * n)) / d, z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0, c - h), min(1, c + h)


def metrics(rs):
    if not rs:
        return {"n": 0, **{c: "-" for c in COLS}}
    k, n = sum(r["passed"] for r in rs), len(rs)
    lo, hi = wilson(k, n)
    ok = [r for r in rs if r["passed"]]
    return {"n": n, "success": f"{100 * k / n:.0f}% ({100 * lo:.0f}-{100 * hi:.0f})",
            "hangs": str(sum(r["status"] == "timeout" for r in rs)),
            "tool errors/run": f"{mean(r['n_tool_errors'] for r in rs):.2f}",
            "tokens/success": f"{mean(r['tokens_in'] + r['tokens_out'] for r in ok):,.0f}" if ok else "-",
            "calls/task": f"{mean(r['n_calls'] for r in rs):.1f}", "$/run": f"{mean(r['cost_usd'] for r in rs):.4f}"}


def pick(phase, config="kairos", model=bench.CORE_MODEL, cat=None):
    return [r for r in runs if r["phase"] == phase and r["config"] == config and r["model"] == model
            and (cat is None or r["cat"] == cat)]


md = ["# Kairos browser tools: v1 vs v2", "",
      "v1 = Kairos ac28cd7 (phases `full` and `full2`, the same code run twice: their difference is the noise band);",
      "v2 = Kairos 116efbc (phase `full3`, Kairos configs only): large-page card, `browser_search_page` over a fresh",
      "accessibility snapshot with refs and context, `browser_snapshot` target/depth. Same 30 tasks, checkers, prompts,",
      "limits and seeded run order.", "",
      f"Static schema (Anthropic tokens): Kairos v1 {schema['v1']['kairos']['anthropic_tokens']:,}, "
      f"v2 {schema['v2']['kairos']['anthropic_tokens']:,} ({schema['v2']['kairos']['tools']} tools in both).", ""]
for model in MODELS:
    md += [f"## {model}", "", "| scope | run | runs | " + " | ".join(COLS) + " |", "|---|---|---|" + "---|" * len(COLS)]
    for cat in [None] + CATS:
        for ph, label in PHASES:
            m = metrics(pick(ph, model=model, cat=cat))
            md.append(f"| {cat or 'all'} | {label} | {m['n']} | " + " | ".join(m[c] for c in COLS) + " |")
    md.append("")

md += ["## Large-page tasks: mean tokens (in + out) per run, and passes (Haiku 5.5)", "",
       "| task | Kairos full | Kairos full2 | Kairos full3 | cloak-mcp v2 (full2, reference) |", "|---|---|---|---|---|"]
for task in sorted({r["task"] for r in runs if r["cat"] == "large"}):
    cells = []
    for ph, cfg in [("full", "kairos"), ("full2", "kairos"), ("full3", "kairos"), ("full2", "cc-cloak")]:
        rs = [r for r in pick(ph, config=cfg) if r["task"] == task]
        cells.append(f"{mean(r['tokens_in'] + r['tokens_out'] for r in rs):,.0f} ({sum(r['passed'] for r in rs)}/{len(rs)})" if rs else "-")
    md.append(f"| {task} | " + " | ".join(cells) + " |")

# Tool use, from the Kairos event transcripts: each assistant step lists its calls (name, args); the
# start/end events that follow run them in that order.
use, nav = defaultdict(list), defaultdict(list)  # (phase, kind) -> [(run_id, model, cat, tokens)]
for r in runs:
    if r["config"] != "kairos":
        continue
    pending = []
    for line in (bench.RAW / "transcripts" / f"{r['run_id']}.jsonl").read_text(encoding="utf-8").splitlines():
        try:
            o = json.loads(line)
        except json.JSONDecodeError:
            continue
        if o.get("k") == "assistant":
            pending += o.get("calls") or []
        elif o.get("k") == "end" and pending:
            name, args = pending.pop(0)
            tok = len(bench.ENC.encode(o["result"], disallowed_special=()))
            if name == "browser_navigate" and r["cat"] == "large":
                nav[r["phase"]].append(tok)
            kind = None
            if name == "browser_search_page":
                kind = name
            elif name == "browser_snapshot":
                kind = name + (" (target/depth)" if ('"target"' in args or '"depth"' in args) else " (whole page)")
            if kind:
                use[(r["phase"], kind)].append((r["run_id"], r["model"], r["cat"], tok))
md += ["", "## How Kairos agents used page search and section snapshots (all models)", "",
       "| run | tool | calls | runs using it | of which Haiku | mean result tokens | max result tokens |",
       "|---|---|---|---|---|---|---|"]
for ph, label in PHASES:
    for kind in ["browser_search_page", "browser_snapshot (target/depth)", "browser_snapshot (whole page)"]:
        xs = use.get((ph, kind), [])
        md.append(f"| {label} | {kind} | {len(xs)} | {len({x[0] for x in xs})} | {sum(x[1] == bench.CORE_MODEL for x in xs)} "
                  + (f"| {mean(x[3] for x in xs):,.0f} | {max(x[3] for x in xs):,} |" if xs else "| - | - |"))
md += ["", "`browser_navigate` result size on large-page tasks (all models): "
       + "; ".join(f"{label} mean {mean(nav[ph]):,.0f} tokens (max {max(nav[ph]):,})" for ph, label in PHASES if nav[ph]) + "."]

# Known pre-existing Kairos bug: humanized scrolling to a far-down element is slow, so a click can time out.
slow = [c for c in calls if c["config"] == "kairos" and c["tool"] == "browser_click"
        and (("Timeout" in (c.get("error") or "") and "click" in (c.get("error") or "").lower())
             or (c.get("latency_s") or 0) > 20 or c.get("timed_out"))]
md += ["", "## Slow or timed-out clicks (known humanized-scroll issue)", ""]
md += [f"- `{c['run_id']}` call {c['idx']}: latency {c.get('latency_s')} s, error: {(c.get('error') or '-')[:160]}"
       for c in slow] or ["- none"]
(bench.ROOT / "results" / "compare_kairos.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print("\n".join(md))
