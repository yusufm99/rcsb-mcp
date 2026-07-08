"""Network-free tests for server-side logic that isn't a pure query builder.

Covers _flatten_object_fields (the recursive GraphQL-schema flatten behind
rcsb_list_data_fields) by injecting a synthetic, deliberately CYCLIC schema in place
of the live introspection calls — so depth-capping, cycle-guarding, keyword filtering,
and the result cap are all exercised without touching the network.
"""
import asyncio
import inspect
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from rcsb_mcp import server  # noqa: E402


# --- synthetic introspection shapes (what _field_descriptor/_unwrap_type expect) ---------- #
def _scalar(name, desc=""):
    return {"name": name, "description": desc, "type": {"kind": "SCALAR", "name": "String", "ofType": None}}


def _obj(name, type_name, desc=""):
    return {"name": name, "description": desc, "type": {"kind": "OBJECT", "name": type_name, "ofType": None}}


def _list_obj(name, type_name, desc=""):
    return {"name": name, "description": desc,
            "type": {"kind": "LIST", "name": None,
                     "ofType": {"kind": "OBJECT", "name": type_name, "ofType": None}}}


# CoreEntry -> polymer_entities -> entry is a back-reference: the classic schema cycle.
_SCHEMA = {
    "CoreEntry": [
        _scalar("rcsb_id"),
        _obj("struct", "Struct", "structure info"),
        _obj("pubmed", "CorePubmed"),
        _list_obj("polymer_entities", "CorePolymerEntity"),
    ],
    "Struct": [_scalar("title", "the structure title")],
    "CorePubmed": [_scalar("rcsb_pubmed_abstract_text", "the paper abstract")],
    "CorePolymerEntity": [
        _obj("rcsb_polymer_entity", "RcsbPolymerEntity"),
        _obj("entry", "CoreEntry"),  # cycle back to the root type
    ],
    "RcsbPolymerEntity": [_scalar("pdbx_description", "molecule description")],
}


def _with_fake_schema(coro_factory):
    """Run an async flatten with server._type_fields swapped for the synthetic schema."""
    async def fake_type_fields(type_name, url=None):
        return _SCHEMA.get(type_name, [])

    orig = server._type_fields
    server._type_fields = fake_type_fields
    try:
        return asyncio.run(coro_factory())
    finally:
        server._type_fields = orig


def _flatten(**kw):
    kw.setdefault("root_type", "CoreEntry")
    kw.setdefault("url", "x")
    kw.setdefault("max_depth", 3)
    kw.setdefault("query", None)
    kw.setdefault("max_results", server.DATA_FIELDS_RESULT_CAP)
    return _with_fake_schema(lambda: server._flatten_object_fields(**kw))


def test_flatten_depth_and_traversal():
    fields, truncated = _flatten(max_depth=3)
    paths = {f["path"] for f in fields}
    # nested within-object + one traversal hop + that hop's nested object are all reached
    assert "struct.title" in paths
    assert "pubmed.rcsb_pubmed_abstract_text" in paths           # the motivating field
    assert "polymer_entities.rcsb_polymer_entity.pdbx_description" in paths
    # object fields are listed too (not just leaves), so they can be drilled/selected
    assert "polymer_entities" in paths and "struct" in paths
    assert not truncated
    print("ok: flatten depth + traversal")


def test_flatten_cycle_guard():
    # polymer_entities.entry re-enters CoreEntry (already on the path): the edge is listed,
    # but the walk does NOT recurse back into it, so nothing appears beneath it.
    fields, _ = _flatten(max_depth=6)
    paths = {f["path"] for f in fields}
    assert "polymer_entities.entry" in paths
    assert not any(p.startswith("polymer_entities.entry.") for p in paths), \
        "cycle guard should stop recursion into an ancestor type"
    print("ok: flatten cycle guard")


def test_flatten_depth_one():
    fields, _ = _flatten(max_depth=1)
    paths = {f["path"] for f in fields}
    assert paths == {"rcsb_id", "struct", "pubmed", "polymer_entities"}  # top level only
    assert not any("." in p for p in paths)
    print("ok: flatten depth=1")


def test_flatten_keyword_filter():
    # keyword matches the path OR the description; "abstract" hits only the pubmed leaf.
    fields, _ = _flatten(query="abstract")
    assert [f["path"] for f in fields] == ["pubmed.rcsb_pubmed_abstract_text"]
    # description-only match: "molecule" appears only in pdbx_description's description.
    desc_hit, _ = _flatten(query="molecule")
    assert [f["path"] for f in desc_hit] == ["polymer_entities.rcsb_polymer_entity.pdbx_description"]
    # a keyword matching nothing returns an empty catalog (not an error).
    none_hit, _ = _flatten(query="zzz_no_such_field")
    assert none_hit == []
    print("ok: flatten keyword filter")


def test_flatten_result_cap():
    # the result cap truncates and reports it (breadth-first, so shallow fields are kept).
    fields, truncated = _flatten(max_depth=3, max_results=2)
    assert truncated and len(fields) == 2
    print("ok: flatten result cap")


def test_field_descriptor_shape():
    # list-of-object unwraps to kind=object, list=True, with the inner type name.
    d = server._field_descriptor(_list_obj("polymer_entities", "CorePolymerEntity"))
    assert d == {"name": "polymer_entities", "kind": "object", "type": "CorePolymerEntity",
                 "list": True, "description": None}
    s = server._field_descriptor(_scalar("rcsb_id", "the id"))
    assert s["kind"] == "scalar" and s["list"] is False and s["type"] == "String"
    print("ok: field descriptor shape")


# --- _enrich_field_errors: raw GraphQL FieldUndefined -> self-correcting hint ------------- #
def _enrich(msgs, root_field="entries", url=None):
    """Run the enricher with the synthetic schema + a fake root-field->type resolver."""
    url = url or server.DATA_GRAPHQL_URL

    async def fake_type_fields(type_name, u=None):
        return _SCHEMA.get(type_name, [])

    async def fake_root_types(u=None):
        return {"entries": "CoreEntry", "alignments": "CoreEntry"}

    orig_tf, orig_rt = server._type_fields, server._root_field_types
    server._type_fields = fake_type_fields
    server._root_field_types = fake_root_types
    try:
        return asyncio.run(server._enrich_field_errors(msgs, root_field, url))
    finally:
        server._type_fields, server._root_field_types = orig_tf, orig_rt


def test_enrich_relocation():
    # a field placed on the wrong type is relocated to where it actually lives.
    out = _enrich("Field 'rcsb_pubmed_abstract_text' in type 'CoreEntry' is undefined")
    assert "not defined on type 'CoreEntry'" in out
    assert "pubmed.rcsb_pubmed_abstract_text" in out                 # correct path surfaced
    assert 'rcsb_list_data_fields("entries", query="rcsb_pubmed_abstract_text")' in out
    print("ok: enrich relocation")


def test_enrich_sibling_typo():
    out = _enrich("Field 'titel' in type 'Struct' is undefined")
    assert "Did you mean: title?" in out
    assert "It exists in the schema at" not in out                   # no spurious relocation
    print("ok: enrich sibling typo")


def test_enrich_passthrough_non_field():
    # a non-FieldUndefined error is returned verbatim (nothing to correct).
    raw = "Some syntax error near '}'"
    assert _enrich(raw) == raw
    print("ok: enrich passthrough")


def test_enrich_unknown_field():
    # a pure hallucination still gets the discovery steer, but no false relocation/typo hint.
    out = _enrich("Field 'totally_made_up' in type 'CoreEntry' is undefined")
    assert "not defined on type 'CoreEntry'" in out
    assert "It exists in the schema at" not in out and "Did you mean" not in out
    assert 'rcsb_list_data_fields("entries", query="totally_made_up")' in out
    print("ok: enrich unknown field")


def test_enrich_seqcoord_steer():
    # on the Sequence Coordinates endpoint the steer names the seqcoord discovery tool.
    out = _enrich("Field 'foo' in type 'CoreEntry' is undefined",
                  root_field="alignments", url=server.SEQCOORD_GRAPHQL_URL)
    assert 'rcsb_describe_seqcoord_object("alignments"' in out
    assert "rcsb_list_data_fields" not in out
    print("ok: enrich seqcoord steer")


def test_enrich_syntax_error():
    # a malformed selection (ANTLR/parse error) gets the accepted format + a discovery steer.
    raw = "Invalid syntax with ANTLR error 'token recognition error at: '.t'' at line 1 column 70"
    out = _enrich(raw)
    assert raw in out                                   # keep the original diagnostic
    assert "`fields=`" in out and "separated by spaces or commas" in out
    assert 'rcsb_list_data_fields("entries"' in out
    print("ok: enrich syntax error")


def test_search_return_type_defaults():
    # Per-tool return_type defaults are deliberate; pin them so they aren't swapped by accident.
    def _default(tool):
        return inspect.signature(tool).parameters["return_type"].default

    # strucmotif defaults to "assembly" — the most general unit for a 3D motif and the
    # default of RCSB.org advanced search (symmetry mates only exist at assembly level).
    assert _default(server.rcsb_search_strucmotif) == "assembly"
    # the other polymer-oriented services default to "polymer_entity"
    assert _default(server.rcsb_search_by_sequence) == "polymer_entity"
    assert _default(server.rcsb_search_by_seqmotif) == "polymer_entity"
    # chemical defaults to the chemical component itself
    assert _default(server.rcsb_search_by_chemical) == "mol_definition"
    print("ok: search return_type defaults")


# --- _get_json: a 204 / empty body must not crash the rcsb_find_* resolvers ---------------- #
class _FakeResp:
    def __init__(self, status_code, content=b""):
        self.status_code = status_code
        self.content = content

    @property
    def is_success(self):
        return 200 <= self.status_code < 300

    @property
    def text(self):
        return self.content.decode() if isinstance(self.content, bytes) else str(self.content)

    def json(self):
        import json as _json
        return _json.loads(self.content)  # raises on empty body — the bug, if 204 isn't handled


class _FakeClient:
    def __init__(self, resp):
        self._resp = resp

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def get(self, url, params=None):
        return self._resp


def _get_json_with(resp):
    orig = server.httpx.AsyncClient
    server.httpx.AsyncClient = lambda *a, **k: _FakeClient(resp)
    try:
        return asyncio.run(server._get_json("http://x", {}, "Test"))
    finally:
        server.httpx.AsyncClient = orig


def test_get_json_204_empty():
    # 204 No Content (what EBI InterPro returns for a no-match query) -> {}, not a JSONDecodeError.
    assert _get_json_with(_FakeResp(204, b"")) == {}
    # a 200 with an empty body is treated the same way.
    assert _get_json_with(_FakeResp(200, b"")) == {}
    # a normal 200 JSON body still decodes.
    assert _get_json_with(_FakeResp(200, b'{"results": [1, 2]}')) == {"results": [1, 2]}
    print("ok: _get_json 204/empty")


def test_interpro_no_match_graceful():
    # with no matches (empty payload) the resolver returns count 0 + a fall-back-to-keyword note,
    # instead of propagating the JSONDecodeError that this input used to trigger.
    async def fake_get_json(url, params, service):
        return {}

    orig = server._get_json
    server._get_json = fake_get_json
    try:
        r = asyncio.run(server.rcsb_find_interpro_domains(
            query="acyltransferase domain polyketide synthase", limit=15, with_pdb_counts=False))
    finally:
        server._get_json = orig
    assert r["count"] == 0 and r["entries"] == []
    assert r.get("note"), "should advise a keyword fallback when nothing matched"
    print("ok: interpro no-match graceful")


if __name__ == "__main__":
    test_flatten_depth_and_traversal()
    test_flatten_cycle_guard()
    test_flatten_depth_one()
    test_flatten_keyword_filter()
    test_flatten_result_cap()
    test_field_descriptor_shape()
    test_enrich_relocation()
    test_enrich_sibling_typo()
    test_enrich_passthrough_non_field()
    test_enrich_unknown_field()
    test_enrich_seqcoord_steer()
    test_enrich_syntax_error()
    test_search_return_type_defaults()
    test_get_json_204_empty()
    test_interpro_no_match_graceful()
    print("\nAll server tests passed.")
