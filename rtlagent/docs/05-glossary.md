# 05 — Glossary

Where a Vivado equivalent exists it is given, because the concepts transfer directly.

## Timing

| Term | Meaning |
|---|---|
| **Slack** | Spare time on a timing path. Negative means too slow. Same as Vivado's slack column. |
| **WNS / TNS** | Worst negative slack — how bad the worst path is. Total negative slack — how *widespread* the problem is. A design at WNS −0.3 / TNS −400 is a very different problem from WNS −0.3 / TNS −0.3. |
| **Setup / hold** | Setup: data must arrive early enough (checked at the **slow** corner). Hold: data must not arrive too early (checked at the **fast** corner). |
| **Fmax** | Highest achievable clock frequency. Found by **binary search on the period**, not by quoting slack at one target. |
| **Corner** | A process/voltage/temperature combination. Timing must hold at all of them. |
| **Timing closure** | Iterating until WNS ≥ 0 everywhere, at every corner. |

## Constraints

| Term | Meaning |
|---|---|
| **SDC** | The Tcl constraint format. Vivado's XDC is SDC plus Xilinx extensions — you already write this. |
| **Generated clock** | A clock derived from another by division or gating. |
| **False path** | A path never functionally exercised. |
| **Multicycle path** | A path allowed more than one clock period. |
| **Clock groups** | Declaring domains mutually asynchronous so cross-domain paths are not timed as if synchronous. **One line; makes this benchmark tractable.** |

## Clock domains

| Term | Meaning |
|---|---|
| **CDC** | Clock domain crossing — a signal passing between clocks with no fixed phase relationship. |
| **Synchroniser** | Two or three flops in series on the destination clock. |
| **Metastability** | A flop caught mid-decision, output hovering between levels for an unbounded time. |
| **MTBF** | Mean time between synchronisation failures. A **physical** property no equivalence checker models. |
| **Gray code** | Encoding where consecutive values differ in exactly one bit. What makes a multi-bit crossing safe. |
| **Elastic buffer** | A FIFO absorbing frequency difference between the two ends of a link. Uses gray-coded pointers. |
| **Reconvergence** | Two separately synchronised signals recombining downstream — can glitch even when each crossing is individually correct. |
| **RDC** | Reset domain crossing. Same hazard, on reset nets. |

## Transformations

| Term | Meaning |
|---|---|
| **Pipelining** | Adding a register stage. Raises Fmax, **adds latency**, legal only on feed-forward cuts. |
| **Retiming** | Relocating existing registers. Latency unchanged, legal only if every loop keeps its register count. |
| **C-slow retiming** | Replicating loop registers to interleave *C* independent data streams. The only way past the iteration bound. |
| **Feed-forward cut set** | A dividing line across the dataflow graph where every crossing edge points the same way. |
| **SCC** | Strongly connected component — a feedback loop in the dataflow graph. |
| **Iteration bound** | max over loops of (loop delay ÷ loop registers). A hard floor on clock period that no retiming beats. |

## Verification

| Term | Meaning |
|---|---|
| **Formal equivalence** | Proving two designs compute the same outputs for **all** inputs, not just the tested ones. |
| **Miter** | A construction feeding both designs the same inputs and XOR-ing the outputs, so equivalence becomes one provable property. |
| **Latency-adjusted miter** | Same, with the golden outputs delayed by N to match a pipelined revision. |
| **k-induction** | Proving a property by induction over k steps. Prone to spurious counterexamples from unreachable states without a reset anchor. |
| **Counterexample** | The concrete input sequence a failed proof returns. **Our repair signal.** |
| **Partition coverage** | Fraction of a design's partitions proven when a full proof times out. Partial credit beats bare failure. |

## Tools

| Tool | What it is | Vivado analogue |
|---|---|---|
| **Yosys** | Open-source synthesis with a programmable IR (RTLIL) | `synth_design` |
| **OpenSTA** | Open-source static timing analysis | `report_timing_summary` |
| **OpenROAD / OpenLane2** | Open-source place and route, and a scripted wrapper | `place_design` + `route_design` |
| **EQY** | Equivalence checker | none in free Vivado |
| **SymbiYosys (SBY)** | General formal property prover | none in free Vivado |
| **Verilator** | Fast simulator and linter; `--xml-only` dumps the AST | XSim |
| **cocotb** | Python testbench framework | — |
| **OSS CAD Suite** | One prebuilt download containing all of the above. **Use it. Do not compile from source.** | — |

## ASIC concepts new to FPGA engineers

| Term | Meaning |
|---|---|
| **Standard cell** | A pre-characterised logic gate from a chosen library. |
| **Liberty (.lib)** | File giving each cell's delay as a function of input slew and output load. In Vivado this was built in; in ASIC **you supply it**. |
| **Technology mapping** | Converting generic logic into library cells. Vivado does this to LUTs invisibly; Yosys does it explicitly via `abc -liberty`. |
| **PPA** | Power, Performance, Area. Area in µm², the analogue of LUT/FF utilisation. |

## Ours

| Term | Meaning |
|---|---|
| **Evidence bundle** | Everything a reviewer needs to accept a change without re-deriving it. The product surface. |
| **CDC certificate** | Differential attestation that every clock-domain property surviving a change. The flagship artefact. |
| **Legal menu** | The finite enumerated set of transformations the model may choose from. |
| **Bounded scope** | The mandatory `scope_not_checked` field. What we did **not** verify. |
| **Structural hash** | Hash over a crossing's topology, ignoring net names. Makes differential comparison robust to renaming. |
