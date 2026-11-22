"""One Kairos benchmark run (a child process of bench.py, which enforces the timeout).

Drives Kairos by importing its Agent class; no Kairos file is changed. The subclass only:
  - offers the browser tools and nothing else (no terminal, files, sub-agents, web_search, desktop),
  - starts with the browser group on, with the guide enable_tools would return appended to the system prompt,
  - stops the run at the 31st tool call,
  - records each tool call and each API request's usage as JSONL lines on stdout.
usage: kairos_run.py <setup> <effort> <workspace>   (prompt on stdin)
"""
import faulthandler
import json
import sys
import time

import kairos.providers.anthropic as anthropic_adapter
from kairos.agent import Agent, APIRequestError

MAX_CALLS = 30
out = sys.stdout


def emit(**rec):
    out.write(json.dumps(rec, ensure_ascii=False) + "\n")
    out.flush()


# Anthropic reports cache writes separately; Kairos folds them into prompt tokens. Tap them for pricing.
_cache_writes = []
_orig_parse = anthropic_adapter.parse_sse


def _tap(lines):
    for ev in _orig_parse(lines):
        if ev.get("type") == "message_start":
            _cache_writes.append((ev.get("message", {}).get("usage", {}) or {}).get("cache_creation_input_tokens") or 0)
        yield ev


anthropic_adapter.parse_sse = _tap


class BenchAgent(Agent):
    n_calls = 0

    def _get_tool_schema(self, all_groups=False):
        return [t for t in super()._get_tool_schema(all_groups=True) if t["function"]["name"].startswith("browser_")]

    def _stream_response(self):
        _cache_writes.clear()
        emit(k="request", t=time.time())
        content, calls, usage = super()._stream_response()
        emit(k="usage", usage=usage, cache_write=sum(_cache_writes))
        emit(k="assistant", text=content, calls=[[c["name"], json.dumps(c["arguments"])[:300]] for c in calls])
        return content, calls, usage

    def _retry_delay(self, n, error=None):
        emit(k="api_retry", error=str(error)[:300])  # provider errors, kept apart from tool errors
        return super()._retry_delay(n, error=error)

    def _execute_tool(self, name, args, max_chars=None):
        self.n_calls += 1
        idx = self.n_calls
        if idx > MAX_CALLS:
            emit(k="cap")
            self.interrupt()
            return json.dumps({"success": False, "output": "", "error": "Tool call limit reached."})
        emit(k="start", idx=idx, tool=name, arg_chars=len(json.dumps(args)), t=time.time())
        result = super()._execute_tool(name, args, max_chars)
        d = json.loads(result)
        emit(k="end", idx=idx, t=time.time(), result=result, is_error=not d.get("success", True),
             error=(d.get("error") or "")[:500])
        return result


def main():
    setup, effort, workspace = sys.argv[1:4]
    faulthandler.dump_traceback_later(290)  # just before bench.py's 300 s kill: shows where a hung run is stuck
    prompt = sys.stdin.read()
    agent = BenchAgent(workspace, setup)
    agent.set_effort(effort)
    agent.enabled_tool_groups.add("browser")
    agent.conversation_history[0]["content"] += "\n\n" + Agent.BROWSER_PROMPT.strip()
    emit(k="model", model=agent.model, effort=agent.effort, n_tools=len(agent._get_tool_schema()))
    try:
        final = agent.run(prompt)
        emit(k="final", status="cap" if agent.n_calls > MAX_CALLS else "done", text=final)
    except APIRequestError as e:
        emit(k="final", status="api_error", text=str(e))
    except Exception as e:  # noqa: BLE001 - recorded, the run counts as failed
        emit(k="final", status="error", text=f"{type(e).__name__}: {e}")
    finally:
        try:
            agent.browser_manager.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
