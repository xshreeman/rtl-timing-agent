# rtl-timing-agent

**A timing-closure agent whose product is not the patch, but the machine-checked understanding that makes the patch safe to accept without re-deriving it.**

Astera Labs challenge · *Constraint Optimization through RTL Enhancement Using Generative AI*
Build window: **15 August → 14 September 2026** · Team of three

---

## The one paragraph version

Chips miss their clock targets. Synthesis tools fix the easy parts but are *forbidden* from changing a design's architecture, because that changes observable behaviour. So a human does it: reads the timing report, guesses the cause, edits RTL, waits, repeats. An AI can generate those edits. That is not the hard part.

The hard part is that **a change nobody can cheaply trust is worse than no change at all.** Verification and review already consume 60–70% of chip project effort. An agent that emits fifty patches, each costing forty minutes of expert review, has *created* thirty hours of work.

So we build the thing that removes the review cost: every change ships with a **machine-checked evidence bundle** — legality justification, formal equivalence certificate, timing delta at both corners, and a **CDC safety certificate** that no equivalence checker can produce. Review collapses from forty minutes to two.

Inside that system sits one component that could be lifted out and sold on its own: **CDC-Guard**.

---

## The flagship: CDC-Guard

```
$ cdcguard certify --golden rtl/golden --revised rtl/candidate_017
✗ FAIL  gray_encoding_preserved
        rd_ptr_gray[3:0] in lane0_elastic_buffer is no longer driven directly
        by flop outputs. Driver is now combinational (binary→gray converter)
        at rtl/lane_rx.v:214.
        Single-bit-transition guarantee is lost. Receiving domain can sample
        a glitch.
        (Functional equivalence: PASS. Equivalence does not imply safety.)
exit 1
```

Give it two versions of a design. It returns a signed certificate stating whether every clock-domain-crossing property that held before still holds after — and if not, exactly which one broke and where.

It is **differential**, not absolute. Commercial CDC tools ask *"is this design clean?"* and return thousands of findings requiring triage, so teams run them rarely and late. We ask *"did this diff break anything that was already established?"* — one verdict, seconds, on every commit.

It gates changes from our optimiser, from a junior engineer, from an IP version bump, from a synthesis tool upgrade. **Its value does not depend on believing in AI at all.**

---

## Start here

| If you are… | Read |
|---|---|
| Anyone on the team, day 1 | [`docs/00-vision.md`](docs/00-vision.md) — the thesis and why it is shaped this way |
| Looking for the system map | [`docs/01-architecture.md`](docs/01-architecture.md) |
| Wondering what you build | [`docs/03-team.md`](docs/03-team.md) then your module runbooks |
| Blocked on someone else's module | [`docs/04-contracts.md`](docs/04-contracts.md) — write a mock, keep moving |
| Wondering what day it is | [`docs/02-timeline.md`](docs/02-timeline.md) |
| Confused by a word | [`docs/05-glossary.md`](docs/05-glossary.md) |

---

## Module index

★ = flagship. Tier 1 must ship or we have no submission.

| Module | Name | Owner | Days | Tier |
|---|---|---|---|---|
| [M00](docs/modules/M00-infrastructure.md) | Infrastructure and contracts | SW-1 | 2 | 1 |
| [M01](docs/modules/M01-benchmark.md) | Benchmark and fault injector | HW-A | 6 | 1 |
| [M02](docs/modules/M02-flow-harness.md) | Flow harness: synthesis + STA | HW-B | 5 | 1 |
| [M03](docs/modules/M03-design-graph.md) | Design knowledge graph | HW-B + SW-1 | 5 | 1 |
| [M04](docs/modules/M04-cdc-guard.md) | ★ **CDC-Guard** | HW-A | 9 | 1 |
| [M05](docs/modules/M05-diagnosis.md) | Diagnosis engine | HW-B | 5 | 1 |
| [M06](docs/modules/M06-legality.md) | ★ Legality analyser | HW-A + SW-1 | 7 | 1 |
| [M07](docs/modules/M07-transform.md) | Transformation engine | HW-B | 6 | 1 |
| [M08](docs/modules/M08-proposer.md) | Generative proposer | SW-1 | 7 | 1 |
| [M09](docs/modules/M09-evidence.md) | ★ Evidence bundle and gates | HW-A + SW-1 | 7 | 1 |
| [M10](docs/modules/M10-orchestrator.md) | Orchestrator and search | SW-1 | 5 | 1 |
| [M11](docs/modules/M11-console.md) | Review console | SW-1 + HW-B | 4 | 2 |
| [M12](docs/modules/M12-physical.md) | Physical confirmation | HW-B | 3 | 2 |
| [M13](docs/modules/M13-evaluation.md) | Evaluation and review-time study | HW-A | 4 | 1 |

---

## Quick start

```bash
git clone <repo> && cd rtl-timing-agent
make env            # pulls pinned OSS CAD Suite image
make smoke          # 20-line design → real slack number. Must pass on day 1.
make test           # unit tests across all modules
```

---

## The rule that decides every argument

> The **analyser** decides what is legal.
> The **model** decides what is worth doing.
> The **prover** decides what is allowed to ship.
> The **certificate** decides how long a human has to spend before they believe it.

If a module blurs those boundaries, the module is wrong.
