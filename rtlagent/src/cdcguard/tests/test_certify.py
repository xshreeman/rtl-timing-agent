"""The tests that define done for the flagship."""
import pytest
from cdcguard.model import Manifest, Crossing
from cdcguard.certify import certify

TOOLS = {"yosys": "0.44", "cdcguard": "0.1.0"}


def mk(crossings, protected=None, recon=None, h="aaa"):
    return Manifest(design_hash=h, tool_versions=TOOLS,
                    domains=[{"name": "CLK_LANE0", "root_clock": "CLK_LANE0",
                              "kind": "master", "async_group": 0},
                             {"name": "CLK_CORE", "root_clock": "CLK_CORE",
                              "kind": "master", "async_group": 1}],
                    crossings=crossings, protected_cells=protected or [],
                    reconvergence=recon or [])


def gray_ok():
    return Crossing(id="c1", signal="rd_ptr_gray", src_domain="CLK_LANE0",
                    dst_domain="CLK_CORE", kind="gray_bus", width=4,
                    encoding="gray", driven_directly_by_flops=True,
                    structural_hash="h1", src_file="lane_rx.v", src_line=200)


def gray_rewritten():
    """The trap: functionally equivalent, structurally unsafe."""
    c = gray_ok()
    c.driven_directly_by_flops = False       # now driven by bin->gray comb logic
    c.src_line = 214
    return c


def sync(depth=2):
    return Crossing(id="c2", signal="mgmt_req_sync", src_domain="CLK_LANE0",
                    dst_domain="CLK_CORE", kind="two_flop_sync",
                    sync_depth=depth, driven_directly_by_flops=True,
                    structural_hash=f"s{depth}", src_file="sync.v", src_line=40)


def test_identical_design_is_safe():
    m = mk([gray_ok(), sync(2)])
    assert certify(m, m).verdict in ("safe_to_merge", "needs_review")


def test_gray_rewrite_is_caught():
    """THE headline test. Equivalence would PASS this. We must not."""
    cert = certify(mk([gray_ok()]), mk([gray_rewritten()]))
    p = next(p for p in cert.properties if p.name == "gray_encoding_preserved")
    assert p.verdict == "fail"
    assert "no longer driven directly by flop outputs" in p.reason
    assert "214" in p.reason                      # actionable: names the line
    assert cert.verdict == "blocked"
    assert cert.exit_code == 1


def test_synchroniser_depth_reduction_is_caught():
    cert = certify(mk([sync(2)]), mk([sync(1)]))
    p = next(p for p in cert.properties if p.name == "synchroniser_topology_unchanged")
    assert p.verdict == "fail"
    assert "2->1" in p.reason


def test_new_crossing_is_caught():
    extra = Crossing(id="c9", signal="leaked", src_domain="CLK_LANE0",
                     dst_domain="CLK_CORE", kind="unsynchronised")
    cert = certify(mk([sync(2)]), mk([sync(2), extra]))
    p = next(p for p in cert.properties if p.name == "crossing_set_unchanged")
    assert p.verdict == "fail"
    assert "NEW crossing" in p.reason


def test_unproven_is_not_pass():
    """Calibration: a timed-out or unsupplied check must never read as pass."""
    cert = certify(mk([sync(2)]), mk([sync(2)]))     # no post-synth manifest
    p = next(p for p in cert.properties if p.name == "attributes_survive_synthesis")
    assert p.verdict == "unproven"
    assert cert.verdict == "needs_review"            # NOT safe_to_merge


def test_scope_is_always_declared():
    """Bounded scope is a trust property. Never ship a certificate without it."""
    cert = certify(mk([sync(2)]), mk([sync(2)]))
    assert cert.scope_not_checked
    assert any("DFT" in s for s in cert.scope_not_checked)
