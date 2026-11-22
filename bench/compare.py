"""cloak-mcp v1 (phase "full") vs v2 (phase "full2") -> results/compare_v1_v2.md. usage: python compare.py"""
import json
import math
from collections import defaultdict
from statistics import mean

import bench


def wilson(k, n, z=1.96):  # same 95% interval as analyze.py
    p, d = k / n, 1 + z * z / n
    c, h = (p + z * z / (2 * n)) / d, z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0, c - h), min(1, c + h)


V1, V2 = "full", "full2"
runs = [r for r in bench.read_jsonl(bench.RUNS) if r["phase"] in (V1, V2)]
schema = {p: json.loads((bench.ROOT / "results" / f).read_text())
          for p, f in ((V1, "schema_tokens_v1.json"), (V2, "schema_tokens.json"))}
CATS = ["basic", "forms", "dialogs", "frames-tabs", "large", "dynamic"]


def metrics(rs):
    if not rs:
        return {"n": 0, **{c: "-" for c in ("success", "hangs", "tool errors/run", "tokens/success", "calls/task", "$/run")}}
    k, n = sum(r["passed"] for r in rs), len(rs)
    lo, hi = wilson(k, n)
    ok = [r for r in rs if r["passed"]]
    return {"n": n, "success": f"{100 * k / n:.0f}% ({100 * lo:.0f}-{100 * hi:.0f})",
            "hangs": f"{sum(r['status'] == 'timeout' for r in rs)}",
            "tool errors/run": f"{mean(r['n_tool_errors'] for r in rs):.2f}",
            "tokens/success": f"{mean(r['tokens_in'] + r['tokens_out'] for r in ok):,.0f}" if ok else "-",
            "calls/task": f"{mean(r['n_calls'] for r in rs):.1f}",
            "$/run": f"{mean(r['cost_usd'] for r in rs):.4f}"}


def pick(phase, config, model=bench.CORE_MODEL, cat=None):
    return [r for r in runs if r["phase"] == phase and r["config"] == config and r["model"] == model
            and (cat is None or r["cat"] == cat)]


cols = ["success", "hangs", "tool errors/run", "tokens/success", "calls/task", "$/run"]
md = ["# cloak-mcp v1 vs v2", "",
      "v1 = phase `full` (cloak-mcp 96aa864), v2 = phase `full2` (cloak-mcp 76211fc). Same 30 tasks, checkers, prompts,",
      "limits and run order; every config was rerun, so the unchanged configs give a same-setup noise baseline.", "",
      f"Static schema: cloak-mcp v1 {schema[V1]['cc-cloak']['tools']} tools / {schema[V1]['cc-cloak']['anthropic_tokens']:,} "
      f"tokens, v2 {schema[V2]['cc-cloak']['tools']} tools / {schema[V2]['cc-cloak']['anthropic_tokens']:,} tokens (Anthropic count).", "",
      "## cc-cloak, overall and per category", "",
      "| scope | version | runs | " + " | ".join(cols) + " |", "|---|---|---|" + "---|" * len(cols)]
for cat in [None] + CATS:
    for ph, label in ((V1, "v1"), (V2, "v2")):
        m = metrics(pick(ph, "cc-cloak", cat=cat))
        md.append(f"| {cat or 'all'} | {label} | {m['n']} | " + " | ".join(m[c] for c in cols) + " |")

md += ["", "## Noise baseline: unchanged configs, v1 vs v2", "",
       "| config / model | version | runs | " + " | ".join(cols) + " |", "|---|---|---|" + "---|" * len(cols)]
for cfg, model in [("cc-devin", bench.CORE_MODEL), ("cc-playwright", bench.CORE_MODEL), ("kairos", bench.CORE_MODEL),
                   ("kairos", "glm-5.3-flash"), ("kairos", "gpt-6-luna"), ("kairos", "gpt-6.1-sol")]:
    for ph, label in ((V1, "v1"), (V2, "v2")):
        m = metrics(pick(ph, cfg, model))
        md.append(f"| {cfg} / {model} | {label} | {m['n']} | " + " | ".join(m[c] for c in cols) + " |")

md += ["", "## Large-page tasks: mean tokens (in + out) per run, and passes, core configs", "",
       "| task | " + " | ".join(f"{c} v1 | {c} v2" for c in bench.CORE) + " |", "|---|" + "---|---|" * len(bench.CORE)]
for task in sorted({r["task"] for r in runs if r["cat"] == "large"}):
    cells = []
    for c in bench.CORE:
        for ph in (V1, V2):
            rs = [r for r in pick(ph, c) if r["task"] == task]
            cells.append(f"{mean(r['tokens_in'] + r['tokens_out'] for r in rs):,.0f} ({sum(r['passed'] for r in rs)}/{len(rs)})"
                         if rs else "-")
    md.append(f"| {task} | " + " | ".join(cells) + " |")

# How cc-cloak v2 agents used the new tools, from the raw stream-json transcripts.
use = defaultdict(list)  # kind -> [(run_id, cat, result_tokens)]
nav = {V1: [], V2: []}   # navigate result tokens on large pages
for ph in (V1, V2):
    for r in pick(ph, "cc-cloak"):
        inputs, path = {}, bench.RAW / "transcripts" / f"{r['run_id']}.jsonl"
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            for b in (o.get("message") or {}).get("content") or []:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "tool_use":
                    inputs[b["id"]] = (b["name"].removeprefix("mcp__browser__"), b.get("input") or {})
                elif b.get("type") == "tool_result" and b.get("tool_use_id") in inputs:
                    name, inp = inputs[b["tool_use_id"]]
                    parts = b["content"] if isinstance(b.get("content"), list) else [{"type": "text", "text": b.get("content") or ""}]
                    tok = len(bench.ENC.encode("".join(p.get("text", "") for p in parts if p.get("type") == "text"), disallowed_special=()))
                    if name == "browser_navigate" and r["cat"] == "large":
                        nav[ph].append(tok)
                    if ph == V2 and name == "browser_find":
                        use["browser_find"].append((r["run_id"], r["cat"], tok))
                    if ph == V2 and name == "browser_snapshot":
                        kind = "browser_snapshot (target/depth)" if ("target" in inp or "depth" in inp) else "browser_snapshot (whole page)"
                        use[kind].append((r["run_id"], r["cat"], tok))
v2_runs = pick(V2, "cc-cloak")
md += ["", "## How cc-cloak v2 agents used the new tools", "",
       "| tool | calls | runs using it (of 60) | categories | mean result tokens | max result tokens |", "|---|---|---|---|---|---|"]
for kind in ["browser_find", "browser_snapshot (target/depth)", "browser_snapshot (whole page)"]:
    xs = use.get(kind, [])
    cats = defaultdict(int)
    for _, c, _ in xs:
        cats[c] += 1
    md.append(f"| {kind} | {len(xs)} | {len({x[0] for x in xs})} | {', '.join(f'{c} {n}' for c, n in sorted(cats.items())) or '-'} "
              f"| {mean(x[2] for x in xs):,.0f} | {max(x[2] for x in xs):,} |" if xs else f"| {kind} | 0 | 0 | - | - | - |")
md += ["", f"`browser_navigate` result size on large-page tasks: v1 mean {mean(nav[V1]):,.0f} tokens (max {max(nav[V1]):,}), "
       f"v2 mean {mean(nav[V2]):,.0f} tokens (max {max(nav[V2]):,})." if nav[V1] and nav[V2] else ""]
(bench.ROOT / "results" / "compare_v1_v2.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print("\n".join(md))
