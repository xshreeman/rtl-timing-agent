# cdcguard

**Differential clock-domain-crossing certification.** Give it two versions of an RTL
design; it tells you whether the change broke any clock-domain safety property.

Unlike absolute CDC sign-off tools, which analyse a whole design and return thousands
of findings requiring triage, `cdcguard` answers one question: *did this diff break
anything that was already established?* One verdict, in seconds, on every commit.

## Why this exists

A gray-coded FIFO pointer rewritten as `binary counter -> bin2gray converter` is
**bit-for-bit functionally equivalent**. A formal equivalence checker approves it.
But the gray value now comes out of combinational logic, which glitches — and the
receiving clock domain can sample the glitch.

Functional equivalence is a statement about *values*. Clock-domain safety is a
statement about *structure and timing*. One does not imply the other.

## Install

    pip install cdcguard

## Use

    cdcguard extract --rtl rtl/golden  --out golden.manifest.json
    cdcguard extract --rtl rtl/revised --out revised.manifest.json
    cdcguard certify --golden golden.manifest.json --revised revised.manifest.json

Exit code 0 = safe to merge, 1 = blocked. Drop it into CI.

## Properties checked

1. `crossing_set_unchanged` — no new unprotected crossings appeared
2. `synchroniser_topology_unchanged` — depth, clock and chain shape preserved
3. `gray_encoding_preserved` — bus still driven directly by flops; single-bit transition still holds
4. `reconvergence_unchanged` — separately synchronised signals still recombine the same way
5. `fifo_protocol_unchanged` — pointer comparison and synchronisation topology preserved
6. `reset_crossings_unchanged` — same analysis over reset nets
7. `attributes_survive_synthesis` — protection attributes not optimised away

Every certificate names its tool versions, hashes both inputs, and lists what it did
**not** check. `unproven` is a first-class verdict and is never reported as `pass`.
