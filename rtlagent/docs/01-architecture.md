# 01 — System architecture

## The six layers

Each layer depends only on the layer beneath it. That is what lets three people build in parallel.

```mermaid
flowchart TB
    subgraph L5["Layer 5 — PRESENT"]
        M11["M11<br/>Review console"]
        M13["M13<br/>Evaluation harness"]
    end
    subgraph L4["Layer 4 — DRIVE"]
        M10["M10<br/>Orchestrator"]
        M12["M12<br/>Post-route confirm"]
    end
    subgraph L3["Layer 3 — CERTIFY"]
        M09["★ M09 — Evidence bundle<br/>four gates, one signed artefact"]
    end
    subgraph L2["Layer 2 — PROPOSE"]
        M06["★ M06<br/>Legality analyser"]
        M08["M08<br/>Proposer + retrieval"]
        M07["M07<br/>Transform engine"]
    end
    subgraph L1["Layer 1 — UNDERSTAND"]
        M03["M03<br/>Design graph"]
        M04["★ M04<br/>CDC-Guard"]
        M05["M05<br/>Diagnosis"]
    end
    subgraph L0["Layer 0 — GROUND"]
        M00["M00<br/>Infrastructure"]
        M01["M01<br/>Benchmark"]
        M02["M02<br/>Flow harness"]
    end
    L0 --> L1 --> L2 --> L3 --> L4 --> L5

    style M04 fill:#FCF0D2,stroke:#B8860B,stroke-width:3px
    style M09 fill:#FCF0D2,stroke:#B8860B,stroke-width:3px
    style M06 fill:#FBF1DC,stroke:#C08A2E,stroke-width:2px
```

## Dependency graph — what actually blocks what

```mermaid
flowchart LR
    M00 --> M01 & M02 & M03
    M01 --> M02
    M02 --> M03 & M05
    M03 --> M04 & M05 & M06
    M04 --> M06 & M09
    M05 --> M06 & M08
    M06 --> M08 & M07
    M08 --> M07
    M07 --> M09
    M09 --> M10
    M10 --> M11 & M12 & M13

    style M04 fill:#FCF0D2,stroke:#B8860B,stroke-width:3px
    style M09 fill:#FCF0D2,stroke:#B8860B,stroke-width:3px
```

**Critical path:** `M00 → M02 → M03 → M04 → M09`. Everything else has slack. If M02 slips, everything slips — that is why HW-B front-loads it.

## One iteration of the loop

```mermaid
sequenceDiagram
    autonumber
    participant O as M10 Orchestrator
    participant F as M02 Flow
    participant G as M03 Graph
    participant C as M04 CDC-Guard
    participant D as M05 Diagnose
    participant L as M06 Legality
    participant P as M08 Proposer
    participant X as M07 Transform
    participant E as M09 Evidence

    O->>F: synthesise + STA (both corners)
    F-->>O: timing.json
    O->>G: build/refresh design graph
    G-->>O: graph.json
    O->>C: extract crossings, mark protected
    C-->>O: cdc_manifest.json (baseline)
    O->>D: cluster violations by root cause
    D-->>O: clusters.json
    O->>L: legal moves for top cluster
    L-->>O: legal_moves.json
    O->>P: evidence package + legal menu
    P-->>O: directive.json
    O->>X: apply directive on new branch
    X-->>O: candidate branch + diff
    O->>E: run four gates
    E->>C: certify(baseline, candidate)
    C-->>E: cdc_certificate.json
    alt proof failed
        E-->>P: counterexample
        P-->>O: repaired directive
    end
    E-->>O: evidence_bundle.json
    O->>F: re-measure whole design
    F-->>O: timing.json
    O->>O: accept globally or roll back
```

## The evaluation ladder

Evaluating a candidate costs anywhere from a millisecond to half an hour. Running the full flow on every idea consumes the month, so candidates pass through a funnel.

```mermaid
flowchart TB
    L0["<b>L0 — graph maths only</b><br/>~200 candidates · milliseconds<br/>predicted depth, balance, area delta"]
    L1["<b>L1 — changed module only</b><br/>~20 candidates · seconds<br/>incremental synth + STA + formal"]
    L2["<b>L2 — whole design</b><br/>~5 candidates · minutes<br/>both corners, area, power"]
    L3["<b>L3 — place and route</b><br/>2 candidates · ~30 min<br/>post-route timing"]
    L0 -->|"survivors"| L1 -->|"survivors"| L2 -->|"Pareto front"| L3
    style L0 fill:#DFF2EB,stroke:#1D9E75
    style L1 fill:#DFF2EB,stroke:#1D9E75
    style L2 fill:#DFF2EB,stroke:#1D9E75
    style L3 fill:#DFF2EB,stroke:#1D9E75
```

**Rule:** never run an expensive tier on something a cheap tier could have rejected.

## Core data model

```mermaid
classDiagram
    class DesignGraph {
        +dict~str,Node~ nodes
        +list~Edge~ edges
        +dict~str,ClockDomain~ domains
        +node_at(file, line) Node
        +domain_of(node_id) str
        +sccs() list~set~
        +feed_forward_cuts(region) list~Cut~
    }
    class Node {
        +str id
        +str kind
        +str src_file
        +int src_line
        +str clock_domain
        +str hier_path
        +bool protected
    }
    class Crossing {
        +str signal
        +str src_domain
        +str dst_domain
        +str kind
        +int sync_depth
        +str encoding
        +list~str~ cells
        +str structural_hash
    }
    class CdcManifest {
        +list~Crossing~ crossings
        +list~str~ protected_cells
        +str design_hash
        +fingerprint() str
    }
    class Certificate {
        +str golden_hash
        +str revised_hash
        +dict tool_versions
        +list~PropertyResult~ properties
        +list~str~ scope_not_checked
        +str verdict
    }
    class PropertyResult {
        +str name
        +str verdict
        +str reason
        +str evidence_ref
    }
    class EvidenceBundle {
        +str diff
        +str rationale
        +LegalityJustification legality
        +Certificate cdc
        +ProofResult equivalence
        +TimingDelta timing
        +int latency_delta
    }

    DesignGraph "1" *-- "many" Node
    CdcManifest "1" *-- "many" Crossing
    Certificate "1" *-- "many" PropertyResult
    EvidenceBundle "1" *-- "1" Certificate
    DesignGraph ..> CdcManifest : extracted from
    CdcManifest ..> Certificate : two manifests certify to
```

## Repository layout

```
rtl-timing-agent/
├── README.md
├── Makefile                    # env, smoke, test, run, report
├── docs/
│   ├── 00-vision.md            ← read first
│   ├── 01-architecture.md      ← you are here
│   ├── 02-timeline.md
│   ├── 03-team.md
│   ├── 04-contracts.md
│   ├── 05-glossary.md
│   └── modules/M00…M13.md      ← the runbooks
├── schemas/                    # 9 JSON schemas + examples  (M00)
│   ├── timing.schema.json
│   ├── graph.schema.json
│   ├── cdc_manifest.schema.json
│   ├── cdc_certificate.schema.json
│   ├── clusters.schema.json
│   ├── legal_moves.schema.json
│   ├── directive.schema.json
│   ├── evidence_bundle.schema.json
│   ├── run_record.schema.json
│   └── examples/               # hand-written mocks — the unblocker
├── rtl/
│   ├── shell/                  # 5-domain interconnect shell   (M01)
│   ├── golden/                 # optimised reference blocks
│   └── damaged/                # generated variants + fault manifests
├── flow/
│   ├── yosys/synth.tcl         # (M02)
│   ├── sta/timing.tcl
│   ├── formal/*.eqy *.sby      # (M09)
│   └── pnr/                    # (M12)
├── src/
│   ├── cdcguard/               # ★ standalone-installable   (M04)
│   ├── flowharness/            # (M02)
│   ├── dkg/                    # (M03)
│   ├── diagnose/               # (M05)
│   ├── legality/               # (M06)
│   ├── transform/              # (M07)
│   ├── proposer/               # (M08)
│   ├── evidence/               # (M09)
│   ├── orchestrator/           # (M10)
│   ├── console/                # (M11)
│   └── evaluate/               # (M13)
├── tests/
└── runs/                       # content-addressed artefact cache
```

**`src/cdcguard/` has its own `pyproject.toml` and README from day one.** It must be `pip install`-able and runnable with zero dependency on the rest of the repo. That is the difference between demonstrating a feature and demonstrating a tool somebody could adopt on Monday.
