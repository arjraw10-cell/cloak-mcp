"""cloak-mcp and Kairos across the reruns -> results/compare_full4.md. usage: python compare_full4.py
cloak-mcp: full (v1 96aa864), full2 (v2 76211fc), full4 (v2.1 1d22924).
Kairos: full and full2 (v1 ac28cd7, run twice: the noise band), full3 (v2 116efbc), full4 (v2.1 0367e99)."""
import json
import math
from collections import defaultdict
from statistics import mean

import bench
import server
import tasks as T

CLOAK = [("full", "v1"), ("full2", "v2"), ("full4", "v2.1")]
KAIROS = [("full", "v1"), ("full2", "v1 rerun"), ("full3", "v2"), ("full4", "v2.1")]
MODELS = [bench.CORE_MODEL, "glm-5.3-flash", "gpt-6-luna", "gpt-6.1-sol"]
CATS = ["basic", "forms", "dialogs", "frames-tabs", "large", "dynamic"]
COLS = ["success", "hangs", "tool errors/run", "tokens/success", "calls/task", "$/run"]
PHASES = {"full", "full2", "full3", "full4"}
runs = [r for r in bench.read_jsonl(bench.RUNS) if r["phase"] in PHASES]
calls = [c for c in bench.read_jsonl(bench.CALLS) if c["run_id"].split(".")[0] in PHASES]
schema = {f: json.loads((bench.ROOT / "results" / f).read_text()) for f in
          ("schema_tokens_v1.json", "schema_tokens.json", "schema_tokens_full3.json", "schema_tokens_full4.json")}


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


def pick(phase, config, model=bench.CORE_MODEL, cat=None):
    return [r for r in runs if r["phase"] == phase and r["config"] == config and r["model"] == model
            and (cat is None or r["cat"] == cat)]


def table(title, config, model, phases):
    out = [f"## {title}", "", "| scope | run | runs | " + " | ".join(COLS) + " |", "|---|---|---|" + "---|" * len(COLS)]
    for cat in [None] + CATS:
        for ph, label in phases:
            m = metrics(pick(ph, config, model, cat))
            out.append(f"| {cat or 'all'} | {ph} ({label}) | {m['n']} | " + " | ".join(m[c] for c in COLS) + " |")
    return out + [""]


def tool_events(r):
    """[(tool, raw_args, result_text)] in call order, from the run's raw transcript."""
    lines = (bench.RAW / "transcripts" / f"{r['run_id']}.jsonl").read_text(encoding="utf-8").splitlines()
    out, pending, inputs = [], [], {}
    for line in lines:
        try:
            o = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r["config"] == "kairos":
            if o.get("k") == "assistant":
                pending += o.get("calls") or []
            elif o.get("k") == "end" and pending:
                name, args = pending.pop(0)
                d = json.loads(o["result"])
                out.append((name, args, d.get("output") or d.get("error") or ""))
            continue
        for b in (o.get("message") or {}).get("content") or []:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "tool_use":
                inputs[b["id"]] = (b["name"].removeprefix("mcp__browser__"), json.dumps(b.get("input") or {}))
            elif b.get("type") == "tool_result" and b.get("tool_use_id") in inputs:
                parts = b["content"] if isinstance(b.get("content"), list) else [{"type": "text", "text": b.get("content") or ""}]
                out.append((*inputs[b["tool_use_id"]], "".join(p.get("text", "") for p in parts if p.get("type") == "text")))
    return out


s = lambda f, k: f"{schema[f][k]['anthropic_tokens']:,}" if k in schema[f] else "-"
md = ["# cloak-mcp and Kairos across the reruns", "",
      "Same 30 tasks, checkers, fixtures, prompts, limits and seeded run order in every phase (filtered phases keep the",
      "full run's relative order). cloak-mcp: `full` = v1 96aa864, `full2` = v2 76211fc, `full4` = v2.1 1d22924.",
      "Kairos: `full` and `full2` = v1 ac28cd7 run twice (their difference is the noise band), `full3` = v2 116efbc,",
      "`full4` = v2.1 0367e99. All Claude Code rows use claude-haiku-5-5 at effort low.", "",
      f"Static schema (Anthropic tokens): cloak-mcp v1 {s('schema_tokens_v1.json', 'cc-cloak')}, v2 {s('schema_tokens.json', 'cc-cloak')}, "
      f"v2.1 {s('schema_tokens_full4.json', 'cc-cloak')}; Kairos v1 {s('schema_tokens_v1.json', 'kairos')}, "
      f"v2 {s('schema_tokens_full3.json', 'kairos')}, v2.1 {s('schema_tokens_full4.json', 'kairos')}.", ""]
md += table("cloak-mcp (Claude Code, claude-haiku-5-5)", "cc-cloak", bench.CORE_MODEL, CLOAK)
for model in MODELS:
    md += table(f"Kairos on {model}", "kairos", model, KAIROS)

cols = ([("cc-cloak", ph) for ph, _ in CLOAK] + [("kairos", ph) for ph, _ in KAIROS] + [("cc-playwright", "full2")])
md += ["## Large-page tasks: mean tokens (in + out) per run and passes (claude-haiku-5-5)", "",
       "| task | " + " | ".join(f"{c.replace('cc-', '')} {ph}" for c, ph in cols) + " |", "|---|" + "---|" * len(cols)]
for task in sorted({r["task"] for r in runs if r["cat"] == "large"}):
    cells = []
    for cfg, ph in cols:
        rs = [r for r in pick(ph, cfg) if r["task"] == task]
        cells.append(f"{mean(r['tokens_in'] + r['tokens_out'] for r in rs) / 1000:,.1f}k ({sum(r['passed'] for r in rs)}/{len(rs)})" if rs else "-")
    md.append(f"| {task} | " + " | ".join(cells) + " |")
avg = lambda cfg, ph: [r for r in pick(ph, cfg, cat="large")]
md.append("| **mean of the 5** | " + " | ".join(
    f"{mean(r['tokens_in'] + r['tokens_out'] for r in avg(c, ph)) / 1000:,.1f}k" if avg(c, ph) else "-" for c, ph in cols) + " |")

# The three problems found in full3, counted in every phase.
events = {r["run_id"]: server.events_for(r["token"]) for r in runs}
wrong, pipes, slow = defaultdict(list), defaultdict(list), defaultdict(list)
for r in runs:
    chk = T.BY_ID[r["task"]]["check"]
    if "event" in chk:
        bad = [e["data"] for e in events[r["run_id"]] if e["event"] == chk["event"]
               and not all(T.norm(e["data"].get(k, "")) == T.norm(v) for k, v in chk["fields"].items())]
        if bad:
            wrong[(r["phase"], r["config"])].append(f"`{r['run_id']}` {bad[:3]}")
    if r["config"] in ("cc-cloak", "kairos"):
        for name, args, res in tool_events(r):
            # Kairos: regex=true flag; cloak-mcp: the regex is its own string parameter ("regex": "...").
            if (name in ("browser_find", "browser_search_page") and "|" in args
                    and '"regex": true' not in args and '"regex": "' not in args):
                outcome = ("rescued by fallback" if "No literal match" in res[:400]
                           else "no matches" if "No matches for" in res[:400] else "literal hit")
                pipes[(r["phase"], r["config"])].append((r["run_id"], args[:80], outcome))
slow_calls = [c for c in calls if c["tool"] == "browser_click" and c["config"] in ("cc-cloak", "kairos")
              and ("Timeout" in (c.get("error") or "") or (c.get("latency_s") or 0) > 10 or c.get("timed_out"))]
for c in slow_calls:
    slow[(c["run_id"].split(".")[0], c["config"])].append(f"`{c['run_id']}` call {c['idx']} ({c.get('latency_s')} s)")
md += ["", "## The three full3 problems, per phase", "",
       "| phase | config | wrong-value actions (runs) | literal \"a\\|b\" searches: literal hit / rescued by fallback / no matches | slow or timed-out clicks |",
       "|---|---|---|---|---|"]
for ph in ["full", "full2", "full3", "full4"]:
    for cfg in ("cc-cloak", "kairos"):
        if not [r for r in runs if r["phase"] == ph and r["config"] == cfg]:
            continue
        ps = pipes[(ph, cfg)]
        n = lambda o: sum(p[2] == o for p in ps)
        md.append(f"| {ph} | {cfg} | {len(wrong[(ph, cfg)])} | {n('literal hit')} / {n('rescued by fallback')} / {n('no matches')} "
                  f"| {len(slow[(ph, cfg)])} |")
md += ["", "Details (full3 and full4):", ""]
for ph in ["full3", "full4"]:
    for cfg in ("cc-cloak", "kairos"):
        for kind, d in (("wrong-value action", wrong), ("slow click", slow)):
            md += [f"- {ph} {cfg} {kind}: {x}" for x in d[(ph, cfg)]]
        md += [f"- {ph} {cfg} literal \"|\" search: `{p[0]}` {p[1]} -> {p[2]}" for p in pipes[(ph, cfg)]]

# Tool use and result sizes for the search and section tools.
use = defaultdict(list)
for r in runs:
    if r["config"] in ("cc-cloak", "kairos") and r["phase"] in ("full2", "full3", "full4"):
        for name, args, res in tool_events(r):
            if name in ("browser_find", "browser_search_page"):
                kind = "search"
            elif name == "browser_snapshot":
                kind = "snapshot target/depth" if ('"target"' in args or '"depth"' in args) else "snapshot whole page"
            else:
                continue
            use[(r["phase"], r["config"], kind)].append((r["run_id"], len(bench.ENC.encode(res, disallowed_special=()))))
md += ["", "## Search and section-snapshot use (all models)", "",
       "| phase | config | tool | calls | runs using it | mean result tokens | max |", "|---|---|---|---|---|---|---|"]
for (ph, cfg, kind), xs in sorted(use.items()):
    md.append(f"| {ph} | {cfg} | {kind} | {len(xs)} | {len({x[0] for x in xs})} | {mean(x[1] for x in xs):,.0f} | {max(x[1] for x in xs):,} |")

md += ["", "## Every full4 failure", ""]
md += [f"- `{r['run_id']}`: {r['status']}, {r['reason']}" for r in sorted(runs, key=lambda r: r["run_id"])
       if r["phase"] == "full4" and not r["passed"]] or ["- none"]
(bench.ROOT / "results" / "compare_full4.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print("\n".join(md))
