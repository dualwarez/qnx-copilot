# Codelab: Ship your first QNX 8.0 image in 20 minutes (with QNX Copilot)

> This is the **Best Codelab prize entry** for the QNX Global Hackathon.
> It is also what `qx codelab` generates — the tool dogfoods its own output.

## What you'll build

A minimal QNX 8.0 image that boots in QEMU, ships a custom "hello-daemon"
binary plus a startup script, validated by `qx doctor` **before** the build —
catching 3 classic mistakes that normally cost a beginner an afternoon.

## Prerequisites

- QNX SDP 8.0 (free non-commercial license) with `qnxsdp-env` sourced
- QEMU system emulator on PATH (`qemu-system-x86_64`)
- Python 3.10+ and `pip install qnx-copilot`

## Step 1 — Write the buildfile (and get it wrong, on purpose)

Create `project.build`:

```
[image=usb]
<bin>
PATH=/bin:/nowhere
/bin/qn={build/x86_64/qn}
/bin/qn={build/x86_64/qn2}
LD_LIBRARY_PATH=/usr/lib
```

Run the doctor:

```sh
qx doctor project.build
```

Expected output:

```
qx doctor: 1 errors, 2 warnings, 1 tips

✗ [ERROR] project.build:6 (module <bin>)
   Duplicate target path '/bin/qn' (first at line 5).
   → Keep one — mkqnximage silently overwrites, hiding which binary actually ships.
! [WARN] ... PATH contains '/nowhere' but no entry ships that directory.
! [WARN] ... env var assignments should live inside a module section.
```

✅ Checkpoint: you see an ERROR exit code (2). The build would have silently
produced a broken image — the doctor caught it for free.

## Step 2 — Fix and build

Fix the duplicate, put `LD_LIBRARY_PATH=` inside the module, correct the PATH.
Then:

```sh
mkqnximage -o images/ -t x86_64 project.build
```

✅ Checkpoint: `images/qnx-image.img` exists and is > 1 MB.

## Step 3 — Boot it

```sh
qx run --arch x86_64 --forward 8000
```

✅ Checkpoint: the QNX login prompt appears on serial. `qconn` is reachable
from the host on port 8000 for `gdb` attach.

## Step 4 — Explain an error you *will* hit next week

```sh
qx explain "undefined reference to `__errno_location'"
```

The hybrid explainer gives the deterministic QNX-specific answer (errno is
thread-local; use `qcc` + `<errno.h>`, never plain gcc) — and with `--ai`
it enriches with an LLM when you have a key.

## What you learned

- The 5 most common buildfile mistakes and their fixes
- Deterministic pre-build validation beats post-build archaeology
- One-command QEMU boot with serial capture

## Next steps

- `qx codelab` in **your** project — generate the same tutorial for your team
- Star the repo: https://github.com/dualwarez/qnx-copilot
