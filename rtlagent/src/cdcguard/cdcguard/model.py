"""Core data model for CDC certification."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Literal
import hashlib, json, datetime

Verdict = Literal["pass", "fail", "unproven", "not_applicable"]

SYNC_KINDS = {"two_flop_sync", "three_flop_sync"}
BUS_KINDS  = {"gray_bus", "async_fifo", "handshake"}


@dataclass
class Crossing:
    id: str
    signal: str
    src_domain: str
    dst_domain: str
    kind: str
    width: int = 1
    sync_depth: int | None = None
    encoding: str = "unknown"
    driven_directly_by_flops: bool = False   # the boolean that catches the gray rewrite
    cells: list[str] = field(default_factory=list)
    src_file: str = ""
    src_line: int = 0
    structural_hash: str = ""
    verdict: str = "unreviewed"
    reason: str = ""

    @staticmethod
    def make_id(signal: str, src: str, dst: str) -> str:
        return hashlib.sha1(f"{signal}|{src}|{dst}".encode()).hexdigest()[:12]


@dataclass
class PropertyResult:
    name: str
    verdict: Verdict
    reason: str = ""
    evidence_ref: str = ""
    affected: list[str] = field(default_factory=list)


@dataclass
class Manifest:
    design_hash: str
    tool_versions: dict
    domains: list[dict]
    crossings: list[Crossing]
    protected_cells: list[str] = field(default_factory=list)
    reconvergence: list[dict] = field(default_factory=list)
    version: str = "1.0"

    def by_id(self) -> dict[str, Crossing]:
        return {c.id: c for c in self.crossings}

    def to_json(self) -> dict:
        d = asdict(self)
        d["crossings"] = [asdict(c) for c in self.crossings]
        return d


@dataclass
class Certificate:
    golden_hash: str
    revised_hash: str
    tool_versions: dict
    properties: list[PropertyResult]
    scope_not_checked: list[str]
    generated_at: str = ""
    version: str = "1.0"

    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.datetime.now(datetime.UTC).isoformat()

    @property
    def verdict(self) -> str:
        """Calibration: unproven is NEVER reported as pass."""
        if any(p.verdict == "fail" for p in self.properties):
            return "blocked"
        if any(p.verdict == "unproven" for p in self.properties):
            return "needs_review"
        return "safe_to_merge"

    @property
    def exit_code(self) -> int:
        return 0 if self.verdict == "safe_to_merge" else 1

    def to_json(self) -> dict:
        return {"version": self.version,
                "golden_hash": self.golden_hash,
                "revised_hash": self.revised_hash,
                "tool_versions": self.tool_versions,
                "generated_at": self.generated_at,
                "properties": [asdict(p) for p in self.properties],
                "scope_not_checked": self.scope_not_checked,
                "verdict": self.verdict}
