"""Structural hashing: compare topology, never instance names.

Synthesis renames things. Comparing manifests by net name is fragile.
Two crossings with the same structural_hash are structurally identical
even if every net was renamed. This is what makes differential
certification robust.
"""
from __future__ import annotations
import hashlib, json, pathlib
import networkx as nx


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def structural_hash(G: nx.DiGraph, root: str, depth: int = 4) -> str:
    """Hash the SHAPE of a subgraph: cell reference types and connectivity,
    with instance names deliberately excluded."""
    walk, frontier = [], [(root, 0)]
    seen = set()
    while frontier:
        n, d = frontier.pop()
        if n in seen or d > depth:
            continue
        seen.add(n)
        nd = G.nodes[n]
        walk.append((
            nd.get("kind", "net"),
            nd.get("ref", ""),                       # cell TYPE, never name
            nd.get("clock_domain", ""),
            sorted(G.edges[n, s].get("port", "") for s in G.successors(n)),
        ))
        for s in list(G.successors(n)) + list(G.predecessors(n)):
            frontier.append((s, d + 1))
    return hashlib.sha256(canonical(sorted(map(list, walk))).encode()).hexdigest()[:16]


def design_hash(rtl_dir: str) -> str:
    """sha256 over sorted file contents. Identical designs hash identically
    regardless of mtime or path."""
    h = hashlib.sha256()
    for p in sorted(pathlib.Path(rtl_dir).rglob("*.[sv]v")):
        h.update(p.name.encode())
        h.update(p.read_bytes())
    return h.hexdigest()
