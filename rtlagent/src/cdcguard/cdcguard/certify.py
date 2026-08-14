"""The seven properties. Differential: does what held in golden still hold?"""
from __future__ import annotations
from .model import Manifest, Certificate, PropertyResult, SYNC_KINDS

SCOPE_NOT_CHECKED = [
    "power intent (UPF)",
    "DFT / scan chain integrity",
    "multicycle path assertions",
    "X-propagation semantics",
    "analog / mixed-signal boundaries",
]


def _p(name, verdict, reason="", affected=None):
    return PropertyResult(name=name, verdict=verdict, reason=reason,
                          affected=affected or [])


def crossing_set_unchanged(g: Manifest, r: Manifest) -> PropertyResult:
    gk, rk = set(g.by_id()), set(r.by_id())
    new, gone = rk - gk, gk - rk
    if not new and not gone:
        return _p("crossing_set_unchanged", "pass")
    bits = []
    if new:
        bits.append("%d NEW crossing(s): %s" % (
            len(new), ", ".join(f"{r.by_id()[i].signal} "
                                f"({r.by_id()[i].src_domain}->{r.by_id()[i].dst_domain}) "
                                f"at {r.by_id()[i].src_file}:{r.by_id()[i].src_line}"
                                for i in sorted(new))))
    if gone:
        bits.append("%d crossing(s) disappeared: %s" % (
            len(gone), ", ".join(g.by_id()[i].signal for i in sorted(gone))))
    return _p("crossing_set_unchanged", "fail", "; ".join(bits),
              sorted(new | gone))


def synchroniser_topology_unchanged(g: Manifest, r: Manifest) -> PropertyResult:
    gm, rm = g.by_id(), r.by_id()
    problems, affected = [], []
    for cid in set(gm) & set(rm):
        gc, rc = gm[cid], rm[cid]
        if gc.kind not in SYNC_KINDS:
            continue
        if rc.sync_depth is not None and gc.sync_depth is not None \
                and rc.sync_depth < gc.sync_depth:
            problems.append(
                f"{gc.signal}: synchroniser depth reduced {gc.sync_depth}->{rc.sync_depth} "
                f"at {rc.src_file}:{rc.src_line}. Metastability margin degraded.")
            affected.append(cid)
        elif gc.structural_hash and rc.structural_hash and \
                gc.structural_hash != rc.structural_hash:
            problems.append(
                f"{gc.signal}: synchroniser topology changed at "
                f"{rc.src_file}:{rc.src_line}")
            affected.append(cid)
    return _p("synchroniser_topology_unchanged",
              "pass" if not problems else "fail", " | ".join(problems), affected)


def gray_encoding_preserved(g: Manifest, r: Manifest) -> PropertyResult:
    """THE headline property. Catches the equivalent-but-unsafe rewrite."""
    gm, rm = g.by_id(), r.by_id()
    gray = [c for c in set(gm) & set(rm) if gm[c].encoding == "gray"]
    if not gray:
        return _p("gray_encoding_preserved", "not_applicable",
                  "no gray-coded crossings in the golden design")
    problems, affected = [], []
    for cid in gray:
        rc = rm[cid]
        if not rc.driven_directly_by_flops:
            problems.append(
                f"{rc.signal} in {rc.src_file}:{rc.src_line} is no longer driven "
                f"directly by flop outputs. Driver is combinational. "
                f"Single-bit-transition guarantee is lost; the receiving domain can "
                f"sample a glitch. NOTE: this change may be functionally equivalent — "
                f"equivalence does not imply CDC safety.")
            affected.append(cid)
        elif rc.encoding != "gray":
            problems.append(f"{rc.signal}: encoding changed gray->{rc.encoding}")
            affected.append(cid)
    return _p("gray_encoding_preserved",
              "pass" if not problems else "fail", " | ".join(problems), affected)


def reconvergence_unchanged(g: Manifest, r: Manifest) -> PropertyResult:
    gs = {tuple(sorted(x["signals"])) for x in g.reconvergence}
    rs = {tuple(sorted(x["signals"])) for x in r.reconvergence}
    new = rs - gs
    if not new:
        return _p("reconvergence_unchanged", "pass")
    return _p("reconvergence_unchanged", "fail",
              f"{len(new)} new reconvergent group(s): {sorted(new)}")


def fifo_protocol_unchanged(g: Manifest, r: Manifest) -> PropertyResult:
    gm, rm = g.by_id(), r.by_id()
    fifos = [c for c in set(gm) & set(rm) if gm[c].kind == "async_fifo"]
    if not fifos:
        return _p("fifo_protocol_unchanged", "not_applicable")
    bad = [c for c in fifos if gm[c].structural_hash != rm[c].structural_hash]
    return _p("fifo_protocol_unchanged", "pass" if not bad else "fail",
              "" if not bad else
              "pointer/comparison topology changed for: " +
              ", ".join(rm[c].signal for c in bad), bad)


def reset_crossings_unchanged(g: Manifest, r: Manifest) -> PropertyResult:
    gm, rm = g.by_id(), r.by_id()
    gr = {c for c in gm if gm[c].kind == "reset_crossing"}
    rr = {c for c in rm if rm[c].kind == "reset_crossing"}
    new = rr - gr
    if not new:
        return _p("reset_crossings_unchanged", "pass")
    return _p("reset_crossings_unchanged", "fail",
              f"{len(new)} new reset domain crossing(s): " +
              ", ".join(rm[c].signal for c in sorted(new)), sorted(new))


def attributes_survive_synthesis(g: Manifest, r: Manifest,
                                 post_synth: Manifest | None = None) -> PropertyResult:
    """Yosys opt_merge will collapse a 2-flop synchroniser because it looks
    redundant. This catches the TOOL, not the human."""
    if post_synth is None:
        return _p("attributes_survive_synthesis", "unproven",
                  "post-synthesis netlist not supplied")
    lost = set(r.protected_cells) - set(post_synth.protected_cells)
    if not lost:
        return _p("attributes_survive_synthesis", "pass")
    return _p("attributes_survive_synthesis", "fail",
              f"{len(lost)} protected cell(s) removed by synthesis: "
              + ", ".join(sorted(lost)[:5]), sorted(lost))


def certify(golden: Manifest, revised: Manifest,
            post_synth: Manifest | None = None) -> Certificate:
    props = [
        crossing_set_unchanged(golden, revised),
        synchroniser_topology_unchanged(golden, revised),
        gray_encoding_preserved(golden, revised),
        reconvergence_unchanged(golden, revised),
        fifo_protocol_unchanged(golden, revised),
        reset_crossings_unchanged(golden, revised),
        attributes_survive_synthesis(golden, revised, post_synth),
    ]
    return Certificate(golden_hash=golden.design_hash,
                       revised_hash=revised.design_hash,
                       tool_versions={**golden.tool_versions,
                                      "cdcguard": "0.1.0"},
                       properties=props,
                       scope_not_checked=SCOPE_NOT_CHECKED)
