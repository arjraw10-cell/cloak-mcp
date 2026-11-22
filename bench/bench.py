"""Benchmark runner. usage:
  python bench.py dev|pilot|full [--workers 4] [--bonus glm-5.3-flash,gpt-6-luna,gpt-6.1-sol]
                             [--configs cc-cloak,...] [--tasks id,...] [--repeats N]
Writes results/raw/{runs,calls,api_errors}.jsonl and one transcript per run. Finished runs
(in runs.jsonl) are skipped on restart; runs that died from API errors are re-queued.
Must run in the logged-in desktop session (see BENCHMARK.md) so the browsers are headed.
"""
import argparse
import json
import os
import queue
import random
import subprocess
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import psutil
import tiktoken

import server
import tasks as T

ROOT = Path(__file__).parent
RAW = ROOT / "results" / "raw"
RUNS, CALLS, API_ERRORS = RAW / "runs.jsonl", RAW / "calls.jsonl", RAW / "api_errors.jsonl"
PROVIDER = Path(r"C:\Users\arjra\Documents\Kairos\provider.json")  # keys are read here at runtime, never copied
CLAUDE_EXE = r"C:\nvm4w\nodejs\node_modules\@anthropic-ai\claude-code\bin\claude.exe"
CLOAK_EXE = str(Path.home() / ".cloakbrowser" / "chromium-146.0.7680.177.5" / "chrome.exe")
TIMEOUT_S, MAX_CALLS, STOP_AT_USD, MAX_ATTEMPTS = 300, 30, 18.0, 3
STALL_S = 120  # a timeout with no tool call in flight and no client output for this long = provider stall
CORE_MODEL, EFFORT, SEED = "claude-haiku-5-5", "low", 2026
MCP = {  # the browser MCP server each Claude Code config loads (and nothing else)
    "cc-cloak": ["node", str(ROOT / "vendor/cloak-mcp/dist/index.js")],
    # --caps all = the 80-tool setup cloak-mcp replaced; --humanize because CloakBrowser input is always humanized
    "cc-devin": ["node", str(ROOT / "mcp-servers/node_modules/@devinwangd/cloak-browser-mcp/dist/index.js"),
                 "--caps", "all", "--humanize"],
    "cc-playwright": ["node", str(ROOT / "mcp-servers/node_modules/@playwright/mcp/cli.js"),
                      "--isolated", "--executable-path", CLOAK_EXE],
}
CORE = ["cc-cloak", "cc-devin", "cc-playwright", "kairos"]
ENC = tiktoken.get_encoding("o200k_base")
_write_lock = threading.Lock()


def provider() -> dict:
    return json.loads(PROVIDER.read_text(encoding="utf-8"))


def anthropic_key():
    keys = provider()["providers"].get("anthropic", {}).get("api_keys") or []
    return keys[0] if keys else None


def price(setup, inp, cache_read, cache_write, out) -> float:
    """USD for one API request: uncached input, cache reads/writes and output x provider.json prices."""
    p = provider()["setups"][setup]["pricing"]
    lc = p.get("long_context")
    if lc and inp + cache_read + cache_write > lc["threshold"]:
        p = {**p, **lc}
    return (inp * p["input"] + cache_read * p.get("cached_input", p["input"])
            + cache_write * p.get("cache_write", p["input"]) + out * p["output"]) / 1e6


def append(path: Path, rec: dict):
    with _write_lock, path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()] if path.is_file() else []


def spent() -> float:
    return sum(r.get("cost_usd") or 0 for r in read_jsonl(RUNS) + read_jsonl(API_ERRORS))


def drive(cmd, env, prompt, cwd, transcript, on_line):
    """Run cmd with prompt on stdin; feed each stdout JSON line to on_line(t, obj), which may return
    "cap" to stop the run. Kills the whole process tree (MCP server, browsers) at the end.
    Returns (verdict, idle_s): verdict "timeout", "cap" or None; idle_s = seconds since the last output line."""
    proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=open(transcript.with_suffix(".err"), "w", encoding="utf-8"),
                            text=True, encoding="utf-8", errors="replace")
    proc.stdin.write(prompt)
    proc.stdin.close()
    lines, tree, verdict = queue.Queue(), {proc.pid}, None
    threading.Thread(target=lambda: [lines.put(l) for l in proc.stdout] + [lines.put(None)], daemon=True).start()
    deadline, last_scan = time.time() + TIMEOUT_S, 0
    last_line = time.time()
    with transcript.open("w", encoding="utf-8") as tr:
        while True:
            if time.time() - last_scan > 1:  # remember descendants so orphaned browsers can be killed too
                try:
                    tree |= {c.pid for c in psutil.Process(proc.pid).children(recursive=True)}
                except psutil.Error:
                    pass
                last_scan = time.time()
            try:
                line = lines.get(timeout=max(0.1, min(1.0, deadline - time.time())))
            except queue.Empty:
                if time.time() >= deadline:
                    verdict = "timeout"
                    break
                continue
            if line is None:
                break
            last_line = time.time()
            tr.write(line)
            if line.lstrip().startswith("{"):
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if on_line(time.time(), obj) == "cap":
                    verdict = "cap"
                    break
    idle = round(time.time() - last_line, 1)
    for pid in tree:
        try:
            psutil.Process(pid).kill()
        except psutil.Error:
            pass
    proc.wait(timeout=30)
    return verdict, idle


def run_claude_code(spec, prompt, work, env, transcript):
    key = anthropic_key()
    cfg = work / "mcp.json"
    cfg.write_text(json.dumps({"mcpServers": {"browser": {"command": MCP[spec["config"]][0],
                                                          "args": MCP[spec["config"]][1:]}}}))
    env = {**env, "ANTHROPIC_API_KEY": key, "ENABLE_TOOL_SEARCH": "false", "DISABLE_AUTOUPDATER": "1",
           "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1"}
    env.pop("ANTHROPIC_AUTH_TOKEN", None)
    cmd = [CLAUDE_EXE, "--bare", "-p", "--model", spec["model"], "--effort", EFFORT,
           "--mcp-config", str(cfg), "--strict-mcp-config", "--tools", "", "--allowedTools", "mcp__browser",
           "--permission-mode", "dontAsk", "--output-format", "stream-json", "--verbose",
           "--max-turns", str(MAX_CALLS + 1), "--no-session-persistence"]
    st = dict(calls={}, order=[], usage={}, final="", result=None, init=None, last_text="", sys=[])

    def on_line(t, o):
        if o.get("type") == "system" and o.get("subtype") == "init":
            st["init"] = {"tools": len(o.get("tools") or []), "mcp_servers": o.get("mcp_servers"), "model": o.get("model")}
        elif o.get("type") == "system" and o.get("subtype") not in ("tool_progress", "ui_invalidate"):  # e.g. API retries
            st["sys"].append(json.dumps(o)[:300])
        elif o.get("type") == "assistant":
            m = o["message"]
            st["usage"][m.get("id")] = m.get("usage") or {}
            for b in m.get("content") or []:
                if b.get("type") == "tool_use" and b["id"] not in st["calls"]:
                    st["order"].append(b["id"])
                    st["calls"][b["id"]] = dict(idx=len(st["order"]), tool=b["name"].removeprefix("mcp__browser__"),
                                                arg_chars=len(json.dumps(b.get("input"))), t=t)
                    if len(st["order"]) > MAX_CALLS:
                        return "cap"
                elif b.get("type") == "text" and b.get("text"):
                    st["last_text"] = b["text"]
        elif o.get("type") == "user":
            for b in (o.get("message") or {}).get("content") or []:
                if isinstance(b, dict) and b.get("type") == "tool_result" and b.get("tool_use_id") in st["calls"]:
                    c = st["calls"][b["tool_use_id"]]
                    parts = b["content"] if isinstance(b.get("content"), list) else [{"type": "text", "text": b.get("content") or ""}]
                    text = "".join(p.get("text", "") for p in parts if p.get("type") == "text")
                    c.update(latency_s=round(t - c["t"], 3), result_tokens=len(ENC.encode(text, disallowed_special=())),
                             n_images=sum(p.get("type") == "image" for p in parts),
                             is_error=bool(b.get("is_error")), error=text[:500] if b.get("is_error") else "")
        elif o.get("type") == "result":
            st["result"] = o
            st["final"] = o.get("result") or ""

    verdict, idle = drive(cmd, env, prompt, work, transcript, on_line)
    reqs = [(u.get("input_tokens", 0), u.get("cache_read_input_tokens") or 0,
             u.get("cache_creation_input_tokens") or 0, u.get("output_tokens", 0)) for u in st["usage"].values()]
    res = st["result"] or {}
    # stream-json carries each message's usage as first reported, so output (incl. thinking) is undercounted
    # there; the final result has the true total. Killed runs (no result) keep the undercount.
    res_out = (res.get("usage") or {}).get("output_tokens")
    if res_out is not None and reqs:
        reqs[-1] = reqs[-1][:3] + (reqs[-1][3] + max(0, res_out - sum(q[3] for q in reqs)),)
    api_error = res.get("terminal_reason") == "api_error" or (not res and not st["order"] and verdict is None)
    status = verdict or ("api_error" if api_error else "done" if res.get("subtype") == "success" else (res.get("subtype") or "error"))
    calls = [st["calls"][i] for i in st["order"]]
    return dict(status=status, final=st["final"] or st["last_text"], calls=calls, requests=reqs, idle_s=idle,
                extra={"init": st["init"], "system_events": st["sys"], "cc_cost_usd": res.get("total_cost_usd"), "num_turns": res.get("num_turns"),
                       "model_usage": res.get("modelUsage"), "result_subtype": res.get("subtype")})


def run_kairos(spec, prompt, work, env, transcript):
    st = dict(calls={}, reqs=[], final="", status=None, retries=[])

    def on_line(t, o):
        k = o.get("k")
        if k == "start":
            st["calls"][o["idx"]] = dict(idx=o["idx"], tool=o["tool"], arg_chars=o["arg_chars"], t=o["t"])
        elif k == "end":
            c = st["calls"][o["idx"]]
            c.update(latency_s=round(o["t"] - c["t"], 3), result_tokens=len(ENC.encode(o["result"], disallowed_special=())),
                     n_images=int('"image_url"' in o["result"]), is_error=o["is_error"], error=o["error"])
        elif k == "usage" and o.get("usage"):
            u, cw = o["usage"], o.get("cache_write") or 0
            cached = u.get("cached_tokens") or 0
            st["reqs"].append((u["prompt_tokens"] - cached - cw, cached, cw, u["completion_tokens"]))
        elif k == "api_retry":
            st["retries"].append(o["error"])
        elif k == "final":
            st["final"], st["status"] = o.get("text") or "", o["status"]

    cmd = [sys.executable, str(ROOT / "kairos_run.py"), spec["model"], EFFORT, str(work)]
    verdict, idle = drive(cmd, {**env, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}, prompt, work, transcript, on_line)
    calls = [st["calls"][i] for i in sorted(st["calls"])]
    return dict(status=verdict or st["status"] or "error", final=st["final"], calls=calls, requests=st["reqs"],
                idle_s=idle, extra={"api_retries": st["retries"]})


def run_one(spec):
    token = uuid.uuid4().hex[:10]
    task = T.BY_ID[spec["task"]]
    prompt = T.PROMPT.format(instruction=task["instruction"],
                             url=task["url"].format(base=f"http://127.0.0.1:{server.PORT}/r/{token}/"))
    work = ROOT / "work" / spec["run_id"]
    work.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "CLOAKBROWSER_PROFILES_DIR": str(work / "profiles"), "CLOAKBROWSER_AUTO_UPDATE": "false"}
    transcript = RAW / "transcripts" / f"{spec['run_id']}.jsonl"
    t0 = time.time()
    r = (run_kairos if spec["config"] == "kairos" else run_claude_code)(spec, prompt, work, env, transcript)
    wall = round(time.time() - t0, 1)
    if r["status"] == "timeout" and r["idle_s"] > STALL_S and all("latency_s" in c for c in r["calls"]):
        r["status"], r["extra"]["api_stall_s"] = "api_error", r["idle_s"]  # waiting on the model API, not a hang
    setup = spec["model"]
    cost = sum(price(setup, *q) for q in r["requests"])
    for c in r["calls"]:
        c.setdefault("latency_s", None)
        c["timed_out"] = c["latency_s"] is None and r["status"] in ("timeout", "cap")
        c.pop("t", None)
        append(CALLS, {"run_id": spec["run_id"], "config": spec["config"], "model": spec["model"],
                       "task": spec["task"], **c})
    base = dict(spec, token=token, started=t0, wall_s=wall, status=r["status"], cost_usd=round(cost, 6),
                n_requests=len(r["requests"]), tokens_in=sum(q[0] + q[1] + q[2] for q in r["requests"]),
                cache_read=sum(q[1] for q in r["requests"]), cache_write=sum(q[2] for q in r["requests"]),
                tokens_out=sum(q[3] for q in r["requests"]),
                n_long_ctx_requests=sum(q[0] + q[1] + q[2] > 100_000 for q in r["requests"]), **r["extra"])
    if r["status"] == "api_error":
        append(API_ERRORS, {**base, "final": r["final"][:1000]})
        return "api_error"
    passed, reason = T.check(task, r["final"], server.events_for(token))
    append(RUNS, {**base, "passed": passed, "reason": reason, "final_answer": T.final_answer(r["final"]),
                  "n_calls": len(r["calls"]), "n_tool_errors": sum(bool(c.get("is_error")) for c in r["calls"]),
                  "n_timed_out_calls": sum(c["timed_out"] for c in r["calls"])})
    print(f"{time.strftime('%H:%M:%S')} {spec['run_id']}: {r['status']} passed={passed} {wall}s ${cost:.4f} ({reason})",
          flush=True)
    return "ok"


def plan(phase, bonus, configs, task_ids, repeats):
    task_ids = task_ids or (T.PILOT if phase in ("dev", "pilot") else [t["id"] for t in T.TASKS])
    combos = [(c, CORE_MODEL) for c in CORE] + [("kairos", m) for m in bonus]
    specs = [dict(run_id=f"{phase}.{c}.{m}.{t}.r{r}", phase=phase, config=c, model=m, effort=EFFORT, task=t,
                  cat=T.BY_ID[t]["cat"], repeat=r)
             for c, m in combos if not configs or c in configs
             for t in task_ids for r in range(1, repeats + 1)]
    random.Random(SEED).shuffle(specs)
    return specs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=["dev", "pilot", "full"])  # dev = harness checks, not analysed
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--bonus", default="")
    ap.add_argument("--configs", default="")
    ap.add_argument("--tasks", default="")
    ap.add_argument("--repeats", type=int)
    a = ap.parse_args()
    split = lambda s: [x for x in s.split(",") if x]
    specs = plan(a.phase, split(a.bonus), split(a.configs), split(a.tasks), a.repeats or (2 if a.phase == "full" else 1))
    if not anthropic_key():
        skipped = [s for s in specs if s["model"] == CORE_MODEL]
        specs = [s for s in specs if s["model"] != CORE_MODEL]
        print(f"provider.json has no anthropic api_keys: skipping {len(skipped)} {CORE_MODEL} runs", flush=True)
    done = {r["run_id"] for r in read_jsonl(RUNS)}
    todo = [s for s in specs if s["run_id"] not in done]
    print(f"{len(specs)} runs planned, {len(specs) - len(todo)} already done, {len(todo)} to run; spent so far ${spent():.4f}",
          flush=True)
    (RAW / "transcripts").mkdir(parents=True, exist_ok=True)
    server.start()
    attempts, stop = {}, threading.Event()

    def worker(spec):
        while not stop.is_set():
            if spent() >= STOP_AT_USD:
                stop.set()
                print(f"spend reached ${STOP_AT_USD}: not launching more runs", flush=True)
                return
            attempts[spec["run_id"]] = attempts.get(spec["run_id"], 0) + 1
            try:
                if run_one(spec) == "ok":
                    return
            except Exception as e:  # noqa: BLE001 - a harness bug in one run must not stop the others
                print(f"{spec['run_id']}: harness error {type(e).__name__}: {e}", flush=True)
                return
            if attempts[spec["run_id"]] >= MAX_ATTEMPTS:
                print(f"{spec['run_id']}: API errors on {MAX_ATTEMPTS} attempts, left for a later restart", flush=True)
                return
            time.sleep(30)

    with ThreadPoolExecutor(a.workers) as pool:
        list(pool.map(worker, todo))
    print(f"finished; total spent ${spent():.4f}", flush=True)


if __name__ == "__main__":
    main()
