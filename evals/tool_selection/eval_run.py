"""Tool-selection regression runner for the rcsb-mcp docstring trim.

Loads the ACTUAL tool schemas + `instructions=` block from a given checkout of the
server, asks a model to act on each prompt in eval_cases.py, and grades the model's
first tool call against the case predicate. Run it twice — once with --src pointing at
the pre-trim server, once at the current one — and diff the per-case pass rates.

Usage:
  # strong model, current tree
  ANTHROPIC_API_KEY=... python eval_run.py --backend anthropic --model claude-sonnet-5 --k 5
  # your vLLM/Gemma OpenAI-compatible endpoint
  python eval_run.py --backend openai --base-url http://localhost:8000 --model gemma-... --k 5
  # A/B: old docstrings (checkout/worktree at the pre-trim commit)
  python eval_run.py --backend openai --base-url ... --model ... --k 5 --src /path/to/old/src \
      --out results_old.json

Only the tool DECISION is graded; the RCSB API is never called. No secrets are logged.
"""
import argparse, importlib, json, os, sys
import httpx

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from eval_cases import CASES  # noqa: E402


def load_server(src_path):
    """Fresh-import rcsb_mcp.server from a specific src dir; return (instructions, tools)."""
    src_path = os.path.abspath(src_path)
    sys.path.insert(0, src_path)
    for m in [k for k in list(sys.modules) if k.startswith("rcsb_mcp")]:
        del sys.modules[m]
    server = importlib.import_module("rcsb_mcp.server")
    import asyncio
    tools = asyncio.run(server.mcp.list_tools())
    instr = getattr(server.mcp, "instructions", "") or ""
    sys.path.remove(src_path)
    return instr, [{"name": t.name, "description": t.description or "", "schema": t.inputSchema} for t in tools]


def first_tool_calls_anthropic(system, tools, messages, model, temperature):
    body = {
        "model": model, "max_tokens": 1024, "system": system,
        "tools": [{"name": t["name"], "description": t["description"], "input_schema": t["schema"]} for t in tools],
        "tool_choice": {"type": "auto"}, "temperature": temperature, "messages": messages,
    }
    r = httpx.post("https://api.anthropic.com/v1/messages", json=body, timeout=120, headers={
        "x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"})
    r.raise_for_status()
    return [(b["name"], b.get("input", {})) for b in r.json().get("content", []) if b.get("type") == "tool_use"]


def first_tool_calls_openai(base_url, system, tools, messages, model, temperature):
    body = {
        "model": model, "temperature": temperature,
        "tools": [{"type": "function", "function": {"name": t["name"], "description": t["description"],
                                                    "parameters": t["schema"]}} for t in tools],
        "tool_choice": "auto",
        "messages": [{"role": "system", "content": system}] + messages,
    }
    r = httpx.post(base_url.rstrip("/") + "/v1/chat/completions", json=body, timeout=120,
                   headers={"Authorization": f"Bearer {os.environ.get('OPENAI_API_KEY', 'x')}"})
    r.raise_for_status()
    calls = r.json()["choices"][0]["message"].get("tool_calls") or []
    out = []
    for c in calls:
        fn = c["function"]
        try:
            args = json.loads(fn.get("arguments") or "{}")
        except json.JSONDecodeError:
            args = {}
        out.append((fn["name"], args))
    return out


def build_messages(case):
    """Single-turn, or a seeded 2-turn history for the empty-result case."""
    if not case.get("seed_zero_result"):
        return [{"role": "user", "content": case["prompt"]}]
    # Seed: the model already ran an attribute search that returned 0 hits; now the follow-up.
    return [
        {"role": "user", "content": case["prompt"]},
        {"role": "assistant", "content": "I searched with rcsb_search_by_attribute and it returned "
                                         "{\"total_count\": 0, \"hits\": []}."},
        {"role": "user", "content": "So are there none? Don't broaden to a keyword search — just answer."},
    ]


def run(args):
    instr, tools = load_server(args.src)
    only = set(x for x in (args.only or "").split(",") if x)
    results = {}
    for case in CASES:
        if only and case["id"] not in only:
            continue
        passes = 0
        errs = []
        observed = []
        for _ in range(args.k):
            msgs = build_messages(case)
            try:
                if args.backend == "anthropic":
                    calls = first_tool_calls_anthropic(instr, tools, msgs, args.model, args.temperature)
                else:
                    calls = first_tool_calls_openai(args.base_url, instr, tools, msgs, args.model, args.temperature)
            except Exception as e:  # noqa: BLE001
                errs.append(str(e)[:120]); continue
            name, cargs = calls[0] if calls else ("<none>", {})
            try:
                ok = bool(case["check"](name, cargs))
            except Exception:  # noqa: BLE001
                ok = False
            passes += ok
            observed.append({"tool": name, "args": cargs, "pass": ok})
        rate = passes / max(1, args.k)
        results[case["id"]] = {"rate": rate, "probes": case["probes"], "errors": errs,
                               "calls": observed}
        flag = "" if rate == 1 else ("  <-- FAIL" if rate == 0 else "  <-- flaky")
        print(f"  {case['id']:16} {int(rate*100):3d}% ({passes}/{args.k}){flag}   {case['probes']}")
    overall = sum(v["rate"] for v in results.values()) / max(1, len(results))
    print(f"\n  OVERALL mean pass-rate: {overall:.2f}   (src={args.src}, model={args.model}, k={args.k})")
    if args.out:
        json.dump({"src": args.src, "model": args.model, "k": args.k, "results": results},
                  open(args.out, "w"), indent=2)
        print(f"  saved -> {args.out}")
    return results


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--backend", choices=["anthropic", "openai"], required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--base-url", default="http://localhost:8000", help="openai backend only")
    p.add_argument("--src", default="src", help="server src dir to load tools from (point at old checkout for A/B)")
    p.add_argument("--k", type=int, default=5, help="samples per case (compare RATES, not single runs)")
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--only", default="", help="comma-separated case ids to run (default: all)")
    p.add_argument("--out", default="")
    run(p.parse_args())
