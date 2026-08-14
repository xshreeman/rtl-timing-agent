"""cdcguard command line. Exit 0 = safe to merge, 1 = blocked. Drop into CI."""
from __future__ import annotations
import argparse, json, sys, pathlib
from dataclasses import asdict
from .model import Manifest, Crossing
from .certify import certify

GREEN, RED, YELLOW, GREY, RESET = "\033[32m", "\033[31m", "\033[33m", "\033[90m", "\033[0m"
MARK = {"pass": f"{GREEN}✓ PASS{RESET}", "fail": f"{RED}✗ FAIL{RESET}",
        "unproven": f"{YELLOW}? UNPR{RESET}", "not_applicable": f"{GREY}- N/A {RESET}"}


def load_manifest(path: str) -> Manifest:
    d = json.loads(pathlib.Path(path).read_text())
    d["crossings"] = [Crossing(**c) for c in d["crossings"]]
    d.pop("version", None)
    return Manifest(**d)


def cmd_extract(args):
    from .extract import extract_from_graph
    graph = json.loads(pathlib.Path(args.graph).read_text())
    man = extract_from_graph(graph)
    pathlib.Path(args.out).write_text(json.dumps(man.to_json(), indent=2))
    kinds = {}
    for c in man.crossings:
        kinds[c.kind] = kinds.get(c.kind, 0) + 1
    print(f"found {len(man.crossings)} crossings across {len(man.domains)} domains")
    for k, n in sorted(kinds.items()):
        print(f"  · {n} {k}")
    print(f"wrote {args.out}  (design_hash {man.design_hash[:6]}…)")
    return 0


def cmd_certify(args):
    golden = load_manifest(args.golden)
    revised = load_manifest(args.revised)
    post = load_manifest(args.post_synth) if args.post_synth else None
    cert = certify(golden, revised, post)

    for p in cert.properties:
        print(f"{MARK[p.verdict]}  {p.name}")
        if p.reason:
            for line in _wrap(p.reason, 72):
                print(f"        {line}")
    print()
    print(f"  {GREY}NOT CHECKED: {', '.join(cert.scope_not_checked)}{RESET}")
    colour = GREEN if cert.verdict == "safe_to_merge" else RED
    print(f"  VERDICT: {colour}{cert.verdict}{RESET}")

    if args.out:
        pathlib.Path(args.out).write_text(json.dumps(cert.to_json(), indent=2))
    return cert.exit_code


def _wrap(text, width):
    words, line, out = text.split(), "", []
    for w in words:
        if len(line) + len(w) + 1 > width:
            out.append(line); line = w
        else:
            line = f"{line} {w}".strip()
    if line:
        out.append(line)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="cdcguard",
        description="Differential clock-domain-crossing certification.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("extract", help="build a CDC manifest from a design graph")
    e.add_argument("--graph", required=True)
    e.add_argument("--out", required=True)
    e.set_defaults(fn=cmd_extract)

    c = sub.add_parser("certify", help="compare two manifests, emit a certificate")
    c.add_argument("--golden", required=True)
    c.add_argument("--revised", required=True)
    c.add_argument("--post-synth", default=None,
                   help="post-synthesis manifest, enables property 7")
    c.add_argument("--out", default=None)
    c.set_defaults(fn=cmd_certify)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
