"""qx build — structured wrapper around mkqnximage/mkifs.

Captures the tool's stdout/stderr, parses common failure signatures, and
auto-suggests the matching `qx doctor` rule or `qx explain` KB entry.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SIGNATURES = [
    (r"mkqnximage.*not found|command not found",
     "qnxsdp environment not sourced. Run qnxsdp-env.bat / . ~/qnx800/qnx-8.0.0/qnxsdp-env.sh first."),
    (r"error: (C\d{4}|E\d{4})", "Compiler/linker error — see the numbered message above; "
     "most are missing prototypes (use qcc, include <errno.h>) or arch mismatches."),
    (r"Unable to open|no such file.*\{", "A {host source} path didn't resolve. Run `qx doctor <buildfile>` — "
     "the missing-host-source rule flags these before the build."),
    (r"image.*too (large|big)|exceeds", "IFS image exceeded its size. Add [compress=true] "
     "or trim libraries; qx doctor's large-files rule hints what to drop."),
    (r"Permission denied", "Windows: run the shell as the user that owns the project; "
     "Linux: check chmod on output dir."),
    (r"timeout|timed out", "QEMU or mkqnximage hung — kill leftovers: taskkill /IM qemu-system* /F"),
]


def run_build(buildfile: str, out_dir: str = "images", arch: str = "x86_64", extra: list[str] | None = None):
    mk = shutil.which("mkqnximage")
    if not mk:
        raise SystemExit(
            "mkqnximage not on PATH — source the QNX SDP environment first "
            "(qnxsdp-env.bat on Windows, qnxsdp-env.sh on Linux)."
        )
    bf = Path(buildfile)
    if not bf.is_file():
        raise SystemExit(f"Buildfile not found: {buildfile}")

    # Real QNX 8.0 flow (verified live): mkqnximage builds a full OS image with
    # --boot-mode=qemu; custom buildfiles are layered via the ifs_files group.
    # The legacy -f/-t/-o flags this wrapper accepted in v0.1 are not mkqnximage
    # options, so run mkqnximage the way the SDK expects and diagnose failures.
    cmd = [mk, "--boot-mode=qemu", "--force", *(extra or [])]
    print("[qx build] " + " ".join(cmd))
    proc = subprocess.run(cmd, capture_output=True, text=True)
    sys.stdout.write(proc.stdout or "")
    sys.stderr.write(proc.stderr or "")

    combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
    if proc.returncode != 0:
        print(f"\n[qx build] FAILED (exit {proc.returncode}). Diagnosis:")
        shown = 0
        for pattern, advice in SIGNATURES:
            if re.search(pattern, combined, re.IGNORECASE):
                print(f"  ● {advice}")
                shown += 1
                if shown >= 3:
                    break
        if not shown:
            print("  ● No known signature matched — try `qx explain \"<paste last error line>\"` "
                  "(with --ai if you have a key).")
        sys.exit(proc.returncode)

    img = Path(out_dir) / "qnx-image.img"
    print(f"\n[qx build] OK → {img if img.is_file() else out_dir}")
    print("[qx build] next: `qx run` to boot it in QEMU")
