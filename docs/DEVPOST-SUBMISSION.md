# Devpost Submission Draft — QNX Copilot

**Project:** QNX Copilot — AI-powered build & run companion for QNX 8.0
**Repo:** https://github.com/dualwarez/qnx-copilot
**Category:** Developer Tooling & Host Tools
**Deadline:** Dec 15, 2026 2:00 PM EST

---

## Elevator pitch (Devpost "Summary" field)

> QNX Copilot turns a QNX 8.0 buildfile from a 1985-era incantation into
> something a modern developer can ship in 20 minutes. It parses the buildfile
> grammar, runs 20 deterministic lint rules (duplicate targets, orphan PATH
> entries, missing qconn, io-pkt→io-sock drift, priority ranges), wraps
> mkqnximage with structured failure diagnosis, boots the image in QEMU with
> one command, and explains errors with a hybrid offline-knowledge-base +
> optional LLM. It dogfoods its own codelab generator — this submission's
> tutorial was written by the tool.

## Features (Devpost body)

1. **`qx doctor <buildfile>`** — 20 rules, exit-code semantics (2 = errors),
   `--json` for CI. Rules include: duplicate target paths, PATH entries with no
   shipping binary, env vars outside modules, missing {host source} blocks,
   [search=...] absence, missing startup/rc, qconn absent, io-pkt legacy drift,
   libc version drift, empty modules, absolute host paths without search, shell
   scripts without a shell binary, compress hints, duplicate modules,
   priority-range validation.
2. **`qx build <buildfile>`** — wraps `mkqnximage -f <bf> -t <arch>`; on failure
   matches 6 known failure signatures and prints the matching fix instead of a
   raw stack trace.
3. **`qx run`** — finds the built image, boots QEMU (x86_64/aarch64), wires
   serial-to-stdio, optional port-forward + UEFI.
4. **`qx explain <error>`** — 7-entry deterministic KB (procnto SIGSEGV, mkifs
   empty image, priority inversion, qconn refused, errno linkage, slay, io-pkt)
   + optional LLM enrichment (OPENAI_API_KEY / GEMINI_API_KEY) — works fully
   air-gapped without it.
5. **`qx codelab`** — generates the tutorial skeleton; this repo's
   docs/CODELAB.md is the proof (Best Codelab entry).

## Build & run instructions (Devpost field)

```
# prerequisites
pip install -e .
# tests
python -m pytest tests/ -q        # 3 passed
# analyze a buildfile (no QNX SDK needed!)
qx doctor examples/demo.build
qx explain "undefined reference to `__errno_location'"
# with QNX SDP 8.0 (free non-commercial license) sourced:
qx build project.build --out images
qx run --arch x86_64 --forward 8000
```

QNX 8.0 evidence: project.build + examples/demo.build use QNX buildfile grammar
and reference QNX_TARGET paths; `qx build` invokes mkqnximage from the QNX SDP;
docs/CODELAB.md documents the full SDP + QEMU flow.

## Video storyboard (<3 min, YouTube)

| t | shot | narration |
|---|---|---|
| 0:00–0:20 | Terminal, `qx --help` | "QNX 8.0 powers billions of devices. But its developer tooling hasn't changed in a decade. Meet QNX Copilot." |
| 0:20–0:50 | `qx doctor examples/demo.build` with live output | "20 rules catch the mistakes every beginner makes — before the build fails." |
| 0:50–1:20 | `qx build` failing on purpose → diagnosis printed | "When the build does fail, you get the fix, not a stack trace." |
| 1:20–1:50 | `qx run` — QEMU boots, QNX prompt on serial | "One command to boot. Serial captured. gdb-ready via qconn." |
| 1:50–2:20 | `qx explain` + `qx codelab` | "Hybrid AI: offline knowledge base, optional LLM. And it writes your onboarding docs." |
| 2:20–2:50 | GitHub repo, CI green badge, judging-criteria table | "Open source, MIT, tested. QNX Copilot — ship real-time, not retro." |

## Judging mapping (Devpost "judging" section)

- **Technological Implementation** — real buildfile grammar parser (100+ lines),
  20 rules, QEMU orchestration, subprocess pipeline; non-trivial working code,
  CI-tested.
- **Design** — single CLI, exit codes for CI, --json, zero-config defaults,
  works offline.
- **Potential Impact** — QNX developer onboarding measured in days today;
  embedded teams already pay for internal tooling of this shape. Target market:
  every new QNX hire + hobbyist entering via the free SDP license.
- **Innovation & AI Creativity** — first AI-native assistant for QNX build
  artifacts; hybrid deterministic-first design means it never hallucinates a
  buildfile fix when the KB knows the answer.


## QNX 8.0 E2E Evidence (Nov 21) — REAL, not mocked

The full chain was executed live and automated:

1. myQNX account registration + activation (email confirm refnum flow)
2. Non-commercial license: agreement accepted + deployed in License Manager ("Deployed")
3. QNX Software Center 2.0.4 silent install ()
4. License key activated via CLI: 3H0V-N9E3-XX0U-R3TF-32T6 → "Activated"
5. SDP 8.0 baseline installed: com.qnx.qnx800 → C:/QNX800 (4.7 GB) + QEMU support packages
6. `qcc -V` → 12.2.0 gcc_nto targets; mkifs / mkqnx6fsimg / mkqnximage all live
7. `mkqnximage --boot-mode=qemu --clean --force` → disk-qemu.vmdk + ifs.bin built
8. `qemu-system-x86_64 -kernel ifs.bin -drive disk-qemu.vmdk,if=ide` →
   **Startup complete — QNX noname 8.0.0 x86_64** (serial log + screenshot in docs/)

See docs/QNX-EVIDENCE.md — this is the same flow QNX Copilot automates.
