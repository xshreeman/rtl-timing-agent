"""Backward tracing primitives. The core of crossing detection."""
from __future__ import annotations
import networkx as nx

REG_KINDS  = {"reg", "memory"}
COMB_KINDS = {"comb", "operator", "net"}


def source_flops(G: nx.DiGraph, flop: str) -> tuple[set[str], bool]:
    """Walk backwards from a flop's data input through combinational logic only,
    stopping at the first registers encountered.

    Returns (source_flops, comb_logic_on_path).

    `comb_on_path` becomes `driven_directly_by_flops = not comb_on_path`.
    That single boolean catches the gray-code rewrite failure, which is
    the whole reason this tool exists.
    """
    frontier = [p for p in G.predecessors(flop)
                if G.edges[p, flop].get("port") != "CLK"]
    seen: set[str] = set()
    sources: set[str] = set()
    comb_on_path = False

    while frontier:
        n = frontier.pop()
        if n in seen:
            continue
        seen.add(n)
        kind = G.nodes[n].get("kind", "net")

        if kind in REG_KINDS:
            sources.add(n)                    # stop; do not traverse through
        elif kind == "port":
            sources.add(n)                    # primary input = its own domain
        else:
            if kind in {"comb", "operator"}:
                comb_on_path = True
            frontier.extend(G.predecessors(n))

    return sources, comb_on_path


def successors_through_comb(G: nx.DiGraph, node: str) -> list[str]:
    """Forward walk to the next register(s), skipping pure nets."""
    out, frontier, seen = [], list(G.successors(node)), set()
    while frontier:
        n = frontier.pop()
        if n in seen:
            continue
        seen.add(n)
        kind = G.nodes[n].get("kind", "net")
        if kind in REG_KINDS:
            out.append(n)
        else:
            frontier.extend(G.successors(n))
    return out


def comb_logic_between(G: nx.DiGraph, a: str, b: str) -> bool:
    """True if any combinational cell sits between two registers.
    A synchroniser chain with logic between stages is BROKEN."""
    for path in nx.all_simple_paths(G, a, b, cutoff=6):
        for n in path[1:-1]:
            if G.nodes[n].get("kind") in {"comb", "operator"}:
                return True
    return False


def sync_depth(G: nx.DiGraph, first: str) -> int:
    """Length of a clean flop chain on one clock with no logic between stages."""
    depth, cur = 1, first
    while True:
        succ = successors_through_comb(G, cur)
        if len(succ) != 1:
            break                                   # fanout -> not a clean chain
        nxt = succ[0]
        if G.nodes[nxt].get("kind") not in REG_KINDS:
            break
        if G.nodes[nxt].get("clock_domain") != G.nodes[cur].get("clock_domain"):
            break
        if comb_logic_between(G, cur, nxt):
            break                                   # logic between stages = broken
        depth += 1
        cur = nxt
    return depth
