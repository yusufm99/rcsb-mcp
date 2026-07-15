"""Tool-selection regression cases for the rcsb-mcp docstring trim.

Each case: a natural-language prompt + a predicate over the model's FIRST tool call
(name, args). Predicates are deliberately tolerant (substring / operator checks) so a
correct-but-differently-phrased call still passes. The point is to compare pass RATES
between the old and new docstrings, not to score absolutely.
"""


def _attrs(args):
    return args.get("attributes") or []


def _has_attr(args, path_substr, operator=None):
    for a in _attrs(args):
        if isinstance(a, dict) and path_substr in str(a.get("attribute", "")):
            if operator is None or a.get("operator") == operator:
                return True
    return False


CASES = [
    dict(id="kw-routing", prompt="Find PDB structures related to CRISPR immunity.",
         probes="keyword routing (no clear attribute)",
         check=lambda t, a: t == "rcsb_search_fulltext"),

    dict(id="attr-vs-kw", prompt="List X-ray structures with resolution better than 1.5 Angstrom.",
         probes="attribute vs keyword",
         check=lambda t, a: t == "rcsb_search_by_attribute"
                            and _has_attr(a, "resolution_combined", "less")),

    dict(id="ontology-disease", prompt="Find structures associated with cystic fibrosis.",
         probes="ontology routing (list moved to instructions) -> resolver first",
         check=lambda t, a: t == "rcsb_find_disease_terms"),

    dict(id="group-by-uniprot",
         prompt="Give me one representative structure per UniProt accession for human protein "
                "kinases, choosing the best-resolution one.",
         probes="group_by requires return_type=polymer_entity (value list moved to instructions)",
         check=lambda t, a: a.get("group_by") is not None
                            and a.get("return_type") == "polymer_entity"),

    dict(id="sort-sortable",
         prompt="Show human hemoglobin structures, best resolution first.",
         probes="sort_by sortability + direction",
         check=lambda t, a: "resolution_combined" in str(a.get("sort_by", ""))
                            and a.get("sort_direction", "asc") == "asc"),

    dict(id="sequence", prompt="Find proteins with a sequence similar to MVLSPADKTNVKAAWGKVGAHAGEYGAEALERMFLSFPTTKTYFPHF.",
         probes="sequence service selection",
         check=lambda t, a: t == "rcsb_search_by_sequence" and bool(a.get("sequence"))),

    dict(id="chem-smiles", prompt="Find chemical components matching the SMILES c1ccccc1O.",
         probes="chemical descriptor",
         check=lambda t, a: t == "rcsb_search_by_chemical" and a.get("query_type", "descriptor") == "descriptor"),

    dict(id="chem-formula", prompt="Which chemical components have the molecular formula C8H9NO2?",
         probes="chemical formula",
         check=lambda t, a: t == "rcsb_search_by_chemical" and a.get("query_type") == "formula"),

    dict(id="shape", prompt="Find structures with a 3D shape similar to entry 4HHB.",
         probes="whole-shape structure service",
         check=lambda t, a: t == "rcsb_search_by_structure" and str(a.get("entry_id", "")).upper() == "4HHB"),

    dict(id="strucmotif", prompt="Find structures containing a catalytic-triad geometry like the one in 4CHA.",
         probes="strucmotif vs by_structure/by_seqmotif (routing survived)",
         check=lambda t, a: t == "rcsb_search_strucmotif"),

    dict(id="all-hits", prompt="Give me ALL human structures released in 2024 — the complete list.",
         probes="all_hits vs paging on an explicit ALL request",
         check=lambda t, a: a.get("all_hits") is True),

    # Multi-turn: seed the model with a zero-count attribute result, then ask a follow-up.
    # Passing = it does NOT switch to a keyword search (the 'empty result is valid' gotcha).
    dict(id="empty-valid", multiturn=True,
         prompt="Are there any structures of protein X from organism Y at better than 0.5 Angstrom?",
         seed_zero_result=True,
         probes="empty-result-is-valid (don't fall back to fulltext)",
         check=lambda t, a: t != "rcsb_search_fulltext"),
]
