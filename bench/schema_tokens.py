"""Static tool-schema cost of each browser layer -> results/schema_tokens.json.
Lists each MCP server's tools over stdio (tools/list) and Kairos's browser tool schema, then counts
tokens with Anthropic's count_tokens for claude-haiku-5-5 (exact; needs the anthropic key in
provider.json) and with tiktoken o200k_base (approximate, always)."""
import json
import subprocess
import sys

import tiktoken

import bench

ENC = tiktoken.get_encoding("o200k_base")
LAYERS = {**bench.MCP, "cc-devin-default-caps": [a for a in bench.MCP["cc-devin"] if a not in ("--caps", "all")]}


def mcp_tools(cmd) -> list:
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                         text=True, encoding="utf-8")
    send = lambda m: (p.stdin.write(json.dumps(m) + "\n"), p.stdin.flush())
    send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "bench", "version": "1"}}})
    send({"jsonrpc": "2.0", "method": "notifications/initialized"})
    send({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    for line in p.stdout:
        msg = json.loads(line)
        if msg.get("id") == 2:
            p.kill()
            return [{"name": t["name"], "description": t.get("description", ""),
                     "input_schema": t.get("inputSchema", {})} for t in msg["result"]["tools"]]
    raise RuntimeError(f"no tools/list reply from {cmd}")


def kairos_tools() -> list:
    sys.argv = sys.argv[:1]
    from kairos.providers.anthropic import translate_tools
    from kairos_run import BenchAgent
    return translate_tools(BenchAgent(str(bench.ROOT / "tmp"), "glm-5.3-flash")._get_tool_schema())


def main():
    # Partial re-measures after a code change, written to their own files so the others stay untouched:
    # "kairos-only" -> *_full3.json (Kairos), "full4" -> *_full4.json (cloak-mcp and Kairos).
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    suffix, layers = {"kairos-only": ("_full3", []), "full4": ("_full4", ["cc-cloak"])}.get(mode, ("", list(LAYERS)))
    out = {name: mcp_tools(LAYERS[name]) for name in layers}
    out["kairos"] = kairos_tools()
    key = bench.anthropic_key()
    client = None
    if key:
        import anthropic
        client = anthropic.Anthropic(api_key=key)
    count = lambda tools: client.messages.count_tokens(
        model=bench.CORE_MODEL, messages=[{"role": "user", "content": "hi"}], **({"tools": tools} if tools else {})).input_tokens
    base = count([]) if client else 0
    report = {}
    for name, tools in out.items():
        report[name] = {"tools": len(tools), "tiktoken_o200k": len(ENC.encode(json.dumps(tools))),
                        "anthropic_tokens": (count(tools) - base) if client else None}
        print(name, report[name], flush=True)
    (bench.ROOT / "results").mkdir(exist_ok=True)
    (bench.ROOT / "results" / f"schema_tokens{suffix}.json").write_text(json.dumps(report, indent=2))
    (bench.ROOT / "results" / f"tool_schemas{suffix}.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
