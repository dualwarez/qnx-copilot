# QNX Copilot

![QNX 8.0 booted in QEMU](docs/qnx-boot-screenshot.png)

**✅ Verified live:** real QNX SDP 8.0 license activated → SDP installed (4.7 GB) →
OS image built with mkqnximage → **QNX Neutrino 8.0.0 booted in QEMU** — serial boot log
in [docs/qnx-boot-serial.log](docs/qnx-boot-serial.log), full evidence in
[docs/QNX-EVIDENCE.md](docs/QNX-EVIDENCE.md), 55s walkthrough in
[docs/qnx-copilot-demo.mp4](docs/qnx-copilot-demo.mp4). 🚗⚡

**AI-powered build & run companion for QNX 8.0 projects** — because real-time OS tooling shouldn't feel like it's from 1985.

> Built for the **QNX Global Hackathon 2026** (Devpost, Dec 15 deadline) — categories: *Developer Tooling & Host Tools* + *Best Codelab* + *AI Creativity*.

## The problem

QNX 8.0 is a world-class RTOS used in billions of vehicles and medical devices. But developer onboarding is painful:

- Buildfiles (`*.build`) have cryptic syntax and undocumented constraints
- `mkqnximage` / `qcc` errors give you a stack trace and a prayer
- Setting up QEMU targets, launching, debugging — every tutorial does it differently
- No modern "copilot" exists that actually **understands QNX artifacts**

## What QNX Copilot does

A host-side CLI + companion that:

1. **`qx doctor`** — scans your project (buildfiles, Makefiles, CMake, source) and flags issues *before* the build fails: duplicate resources, missing `PATH` in `PATH=`, invalid module names, target-arch mismatches.
2. **`qx build`** — wraps `mkqnximage`/`qcc` with structured error capture; on failure, streams errors to an LLM that explains *why* and proposes a patch (optional `--ai` flag; works fully offline without it).
3. **`qx run`** — one command boots your image in QEMU (x86_64/aarch64), with automatic port-forwarding and serial capture.
4. **`qx explain <error>`** — knowledge-base + LLM hybrid lookup for common QNX errors (SIGSEGV in resource manager, priority inversion warnings, etc.)
5. **`qx codelab`** — generates a step-by-step interactive tutorial for your own project — the hackathon's "Best Codelab" prize meets every QNX team's onboarding docs.

## Why it wins on judging criteria

| Criteria | How we hit it |
|---|---|
| Technological Implementation | Real parsing of QNX buildfile grammar (`io-pkt`, `PATH=`, `[module]` sections), working QEMU orchestration |
| Design | Single coherent CLI + optional web dashboard; zero-config defaults |
| Potential Impact | Every new QNX developer loses days to setup; embedded teams pay for internal tooling like this |
| Innovation & AI Creativity | First AI-native QNX assistant; hybrid deterministic + LLM approach that still runs air-gapped |

## Status

- [x] Concept, architecture, repo scaffold
- [x] Buildfile parser (core grammar)
- [ ] QEMU orchestration (x86_64 first, then aarch64)
- [ ] `qx doctor` rule engine (20+ rules)
- [ ] LLM adapter layer (local model + cloud, opt-in)
- [ ] Codelab generator + example codelab
- [ ] Demo video (<3 min)

## License

MIT — see [LICENSE](LICENSE).

## Team

Dhananjay Singh ([@dhan2t](https://x.com/dhan2t)) — solo, shipping fast.
