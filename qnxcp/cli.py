"""qnx-copilot CLI entry point (`qx`)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .parser import parse_buildfile
from .doctor import diagnose, summarize, RULE_COUNT
from .run import run_image
from .ai import explain
from .build import run_build


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="qx",
        description="QNX Copilot — AI-powered build & run companion for QNX 8.0 projects.",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_doc = sub.add_parser("doctor", help="analyze a .build file and report issues")
    p_doc.add_argument("buildfile", help="path to *.build")
    p_doc.add_argument("--json", action="store_true", help="emit machine-readable findings")

    p_run = sub.add_parser("run", help="boot the built QNX image in QEMU")
    p_run.add_argument("--root", default=".", help="project root to search for the image")
    p_run.add_argument("--arch", default="x86_64", choices=["x86_64", "aarch64"])
    p_run.add_argument("--memory", default="512M")
    p_run.add_argument("--forward", help="guest TCP port to forward (e.g. 8000)")
    p_run.add_argument("--uefi", action="store_true", help="boot with OVMF (x86_64)")

    p_exp = sub.add_parser("explain", help="explain a QNX error message")
    p_exp.add_argument("error", help="error text or '-' to read stdin")
    p_exp.add_argument("--ai", action="store_true", help="also ask an LLM (needs API key)")

    p_bld = sub.add_parser("build", help="run mkqnximage with structured error diagnosis")
    p_bld.add_argument("buildfile", help="path to *.build")
    p_bld.add_argument("--out", default="images", help="output dir for the image")
    p_bld.add_argument("--arch", default="x86_64", choices=["x86_64", "aarch64"])
    p_bld.add_argument("extra", nargs="*", help="extra args passed to mkqnximage")

    sub.add_parser("codelab", help="generate a codelab skeleton for the current project")

    args = ap.parse_args(argv)

    if args.cmd == "doctor":
        text = Path(args.buildfile).read_text(encoding="utf-8", errors="replace")
        bf = parse_buildfile(text, path=args.buildfile)
        findings = diagnose(bf)
        if args.json:
            import json

            print(json.dumps([f.__dict__ for f in findings], indent=2))
        else:
            print(summarize(findings))
            print(f"(rules run: {RULE_COUNT})")
            sys.exit(2 if any(f.level == "ERROR" for f in findings) else 0)

    elif args.cmd == "run":
        run_image(Path(args.root), args.arch, args.memory, args.forward, args.uefi)

    elif args.cmd == "explain":
        text = sys.stdin.read() if args.error == "-" else args.error
        print(explain(text, use_ai=args.ai))

    elif args.cmd == "build":
        run_build(args.buildfile, args.out, args.arch, args.extra)

    elif args.cmd == "codelab":
        from .codelab import generate

        generate(Path.cwd())


if __name__ == "__main__":
    main()
