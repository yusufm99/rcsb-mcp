"""Tool-selection probe runner for rcsb-mcp (see README.md and probes.xml).

Loads the ACTUAL tool schemas + `instructions=` block from a given checkout of the server,
asks a model to act on each prompt in probes.xml, and grades the model's FIRST tool call
against that probe's <expect> assertion. Run it twice — once with --src pointing at the
pre-change server, once at the current one — and compare the pass rates with --compare.

Usage:
  # strong model / current tree
  ANTHROPIC_API_KEY=... python run_probes.py --backend anthropic --model claude-haiku-4-5-20251001 --k 5
  # a local vLLM (OpenAI-compatible endpoint; usually needs no key)
  python run_probes.py --backend openai --base-url http://localhost:8000 --model <id> --k 5
  # A/B against a pre-change checkout, then diff
  python run_probes.py ... --src /tmp/old/src --out /tmp/old.json
  python run_probes.py ... --src src          --out /tmp/new.json
  python run_probes.py --compare /tmp/old.json /tmp/new.json

Only the tool DECISION is graded; the RCSB API is never called. No secrets are logged.
"""
import argparse
import asyncio
import importlib
import json
import os
import sys
import xml.etree.ElementTree as ET

import httpx

HERE = os.path.dirname(os.path.abspath(__file__))
PROBES_XML = os.path.join(HERE, "probes.xml")


# --------------------------------------------------------------------------- #
# probes.xml -> probes + the <expect> interpreter
# --------------------------------------------------------------------------- #
def load_probes(path=PROBES_XML):
    root = ET.parse(path).getroot()
    probes = []
    for p in root.findall("probe"):
        probes.append({
            "id": p.get("id"),
            "probes": p.get("probes") or "",
            "seed": p.get("seed"),
            "prompt": (p.findtext("prompt") or "").strip(),
            "expect": p.find("expect"),
        })
    return probes


def _eq(actual, expected, ignore_case=False):
    """Compare an arg value to an expected string; "true"/"false" compare against booleans."""
    if isinstance(actual, bool):
        return actual == (str(expected).strip().lower() == "true")
    a, e = str(actual), str(expected)
    if ignore_case:
        a, e = a.lower(), e.lower()
    return a == e


def check(expect, tool, args):
    """Evaluate a probe's <expect> assertion against the model's first tool call."""
    if expect is None:
        return False
    if expect.get("tool") and tool != expect.get("tool"):
        return False
    if expect.get("tool-in") and tool not in [x.strip() for x in expect.get("tool-in").split(",")]:
        return False
    if expect.get("tool-not") and tool == expect.get("tool-not"):
        return False

    for el in expect:
        if el.tag == "arg":
            name = el.get("name")
            val = args.get(name, el.get("default")) if el.get("default") is not None else args.get(name)
            if el.get("set") == "true":
                if val is None or val == "" or val == [] or val == {}:
                    return False
            elif el.get("equals") is not None:
                if val is None or not _eq(val, el.get("equals"), el.get("ignore-case") == "true"):
                    return False
            elif el.get("contains") is not None:
                if el.get("contains") not in str(val if val is not None else ""):
                    return False
        elif el.tag == "attribute":
            path, op = el.get("path"), el.get("operator")
            hit = False
            for a in args.get("attributes") or []:
                if isinstance(a, dict) and path in str(a.get("attribute", "")):
                    if op is None or a.get("operator") == op:
                        hit = True
                        break
            if not hit:
                return False
    return True


# --------------------------------------------------------------------------- #
# server under test + model backends
# --------------------------------------------------------------------------- #
def load_server(src_path):
    """Fresh-import rcsb_mcp.server from a specific src dir; return (instructions, tools)."""
    src_path = os.path.abspath(src_path)
    sys.path.insert(0, src_path)
    for m in [k for k in list(sys.modules) if k.startswith("rcsb_mcp")]:
        del sys.modules[m]
    server = importlib.import_module("rcsb_mcp.server")
    tools = asyncio.run(server.mcp.list_tools())
    instr = getattr(server.mcp, "instructions", "") or ""
    sys.path.remove(src_path)
    return instr, [{"name": t.name, "description": t.description or "", "schema": t.inputSchema} for t in tools]


def call_anthropic(system, tools, messages, model, temperature):
    body = {
        "model": model, "max_tokens": 1024, "system": system, "temperature": temperature,
        "tools": [{"name": t["name"], "description": t["description"], "input_schema": t["schema"]} for t in tools],
        "tool_choice": {"type": "auto"}, "messages": messages,
    }
    r = httpx.post("https://api.anthropic.com/v1/messages", json=body, timeout=120, headers={
        "x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"})
    r.raise_for_status()
    return [(b["name"], b.get("input", {})) for b in r.json().get("content", []) if b.get("type") == "tool_use"]


def call_openai(base_url, system, tools, messages, model, temperature):
    body = {
        "model": model, "temperature": temperature, "tool_choice": "auto",
        "tools": [{"type": "function", "function": {"name": t["name"], "description": t["description"],
                                                    "parameters": t["schema"]}} for t in tools],
        "messages": [{"role": "system", "content": system}] + messages,
    }
    r = httpx.post(base_url.rstrip("/") + "/v1/chat/completions", json=body, timeout=120,
                   headers={"Authorization": f"Bearer {os.environ.get('OPENAI_API_KEY', 'x')}"})
    r.raise_for_status()
    out = []
    for c in r.json()["choices"][0]["message"].get("tool_calls") or []:
        try:
            out.append((c["function"]["name"], json.loads(c["function"].get("arguments") or "{}")))
        except json.JSONDecodeError:
            out.append((c["function"]["name"], {}))
    return out


def build_messages(probe):
    """Single-turn, or a seeded history for probes that need prior context."""
    if probe.get("seed") != "zero-result":
        return [{"role": "user", "content": probe["prompt"]}]
    return [
        {"role": "user", "content": probe["prompt"]},
        {"role": "assistant", "content": "I searched with rcsb_search_by_attribute and it returned "
                                         "{\"total_count\": 0, \"hits\": []}."},
        {"role": "user", "content": "So are there none? Don't broaden to a keyword search — just answer."},
    ]


# --------------------------------------------------------------------------- #
def run(args):
    instr, tools = load_server(args.src)
    only = {x for x in (args.only or "").split(",") if x}
    results = {}
    for probe in load_probes():
        if only and probe["id"] not in only:
            continue
        passes, errs, observed = 0, [], []
        for _ in range(args.k):
            msgs = build_messages(probe)
            try:
                if args.backend == "anthropic":
                    calls = call_anthropic(instr, tools, msgs, args.model, args.temperature)
                else:
                    calls = call_openai(args.base_url, instr, tools, msgs, args.model, args.temperature)
            except Exception as e:  # noqa: BLE001
                errs.append(str(e)[:120])
                continue
            tool, targs = calls[0] if calls else ("<none>", {})
            ok = bool(check(probe["expect"], tool, targs))
            passes += ok
            observed.append({"tool": tool, "args": targs, "pass": ok})
        rate = passes / max(1, args.k)
        results[probe["id"]] = {"rate": rate, "probes": probe["probes"], "errors": errs, "calls": observed}
        flag = "" if rate == 1 else ("  <-- FAIL" if rate == 0 else "  <-- flaky")
        print(f"  {probe['id']:16} {int(rate*100):3d}% ({passes}/{args.k}){flag}   {probe['probes']}")
    overall = sum(v["rate"] for v in results.values()) / max(1, len(results))
    print(f"\n  OVERALL mean pass-rate: {overall:.2f}   (src={args.src}, model={args.model}, k={args.k})")
    if args.out:
        json.dump({"src": args.src, "model": args.model, "k": args.k, "results": results},
                  open(args.out, "w"), indent=2)
        print(f"  saved -> {args.out}")
    return results


def compare(old_path, new_path):
    """Diff two result files. A regression = a probe whose pass-rate DROPPED old->new."""
    old, new = json.load(open(old_path)), json.load(open(new_path))
    o, n = old["results"], new["results"]
    print(f"A/B  old_src={old['src']}  new_src={new['src']}  model={new['model']}  k={new['k']}\n")
    regress, improved, unchanged, preexisting = [], [], [], []
    for pid, nr in n.items():
        if pid not in o:
            continue
        ro, rn = o[pid]["rate"], nr["rate"]
        if rn < ro:
            regress.append((pid, ro, rn, nr["probes"]))
        elif rn > ro:
            improved.append((pid, ro, rn))
        else:
            (preexisting if rn < 1.0 else unchanged).append(pid)
    for pid, ro, rn, probes in regress:
        print(f"  REGRESSION  {pid:16} {int(ro*100):3d}% -> {int(rn*100):3d}%   {probes}")
    for pid, ro, rn in improved:
        print(f"  improved    {pid:16} {int(ro*100):3d}% -> {int(rn*100):3d}%")
    if preexisting:
        print(f"  (pre-existing <100% on both, not change-caused: {', '.join(preexisting)})")
    print(f"\n  {len(regress)} regression(s), {len(improved)} improved, "
          f"{len(unchanged)+len(preexisting)} unchanged")
    print("  VERDICT:", "SAFE — no regressions" if not regress else "REVIEW — behaviour changed above")
    return regress


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--compare", nargs=2, metavar=("OLD", "NEW"), help="diff two result files and exit")
    p.add_argument("--backend", choices=["anthropic", "openai"])
    p.add_argument("--model")
    p.add_argument("--base-url", default="http://localhost:8000", help="openai backend only")
    p.add_argument("--src", default="src", help="server src dir to load tools from (point at an old checkout for A/B)")
    p.add_argument("--k", type=int, default=5, help="samples per probe (compare RATES, not single runs)")
    p.add_argument("--temperature", type=float, default=1.0)
    p.add_argument("--only", default="", help="comma-separated probe ids to run (default: all)")
    p.add_argument("--out", default="")
    a = p.parse_args()
    if a.compare:
        sys.exit(1 if compare(*a.compare) else 0)
    if not a.backend or not a.model:
        p.error("--backend and --model are required (unless --compare)")
    run(a)
