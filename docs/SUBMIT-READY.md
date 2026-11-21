# Devpost Submission — COPY-PASTE READY (QNX Hackathon)

**Hackathon:** https://qnxdevpost.devpost.com (QNX Hackathon $50K)
**Deadline:** Dec 15, 2026 2:00 PM EST
**Login:** Devpost → dualwarez@gmail.com → "Log in with GitHub" (user का GitHub logged है) या password

## Submit button flow
repo page पर "Submit to hackathon" → QNX Hackathon चुनो → form नीचे:

## Field 1: Project name
```
QNX Copilot
```

## Field 2: Tagline (60 chars)
```
AI-powered build, lint & run companion for QNX 8.0 projects
```

## Field 3: Built with (tags)
```
Python, QNX 8.0, QNX SDP, mkqnximage, QEMU, mkifs, GitHub Actions, pytest
```

## Field 4: GitHub repo URL
```
https://github.com/dualwarez/qnx-copilot
```

## Field 5: Video URL (YouTube upload के बाद डालो)
Video file: docs/qnx-copilot-demo.mp4 (55s) — YouTube पर upload करके link यहाँ।
अगर YouTube नहीं: gallery में mp4 + screenshots डालो और video field में
```
https://github.com/dualwarez/qnx-copilot/raw/main/docs/qnx-copilot-demo.mp4
```

## Field 6: Summary / About (सीधा paste)
```
QNX Copilot turns a QNX 8.0 buildfile from a 1985-era incantation into something a modern developer can ship in 20 minutes.

It parses the buildfile grammar, runs 20 deterministic lint rules (duplicate targets, orphan PATH entries, missing qconn, io-pkt→io-sock drift, priority ranges), wraps mkqnximage with structured failure diagnosis, boots the image in QEMU with one command, and explains errors with a hybrid offline knowledge base + optional LLM.

Everything in this submission is backed by a real, live QNX SDP 8.0 installation: we registered a myQNX account, accepted and deployed the non-commercial license (key 3H0V-N9E3-XX0U-R3TF-32T6, status "Activated"), installed SDP 8.0 (4.7 GB) via the Software Center CLI, built a full QNX 8.0 OS image with mkqnximage, and booted QNX Neutrino 8.0.0 in QEMU — "Startup complete — QNX noname 8.0.0 x86_64" (serial log + screenshot + 55s video in docs/).

The whole chain — myQNX registration → license acceptance → deployment → activation → SDP installation → image build → QEMU boot — was driven end-to-end by automation, which is exactly the developer experience QNX Copilot exists to give every QNX developer.
```

## Field 7: How to run (Build instructions)
```
# No QNX SDK needed for lint/explain/codelab:
pip install -e .
python -m pytest tests/ -q          # 3 passed
qx doctor examples/demo.build       # 20 rules, exit code 2 on errors
qx explain "undefined reference to \`__errno_location'"

# With QNX SDP 8.0 installed (free non-commercial license):
mkqnximage --boot-mode=qemu --clean --force     # builds disk-qemu.vmdk + ifs.bin
qemu-system-x86_64 -m 512 -smp 2 -cpu max \
    -drive file=output/disk-qemu.vmdk,if=ide \
    -kernel output/ifs.bin \
    -serial file:serial_out.txt
# → Startup complete — QNX noname 8.0.0 x86_64
```

## Field 8: Gallery images (इस order में)
1. docs/qnx-boot-screenshot.png (QEMU window)
2. tools/vidframes/f2_doctor.png (qx doctor output)
3. tools/vidframes/f3_license.png (license activated)
4. tools/vidframes/f4_build.png (mkqnximage build)
5. tools/vidframes/f5_boot.png (serial boot log)

## Field 9: Challenges (optional)
```
QNX 8.0's mkqnximage moved from classic buildfiles to a group/snippet system, and the
Windows host tools need MSYS-style paths. We patched three incompatibilities (cygdrive
path conversion, MKFS_PATH/IS_WINDOWS detection) and wrapped the whole flow so users
never see those errors — they get structured diagnosis instead.
```

## Checklist जब login हो:
- [ ] Submit form भरो (ऊपर के fields)
- [ ] Gallery 5 images
- [ ] Video (YouTube ya GitHub raw)
- [ ] **SUBMIT** — फिर confirmation screenshot
- [ ] Edits open रहेंगे deadline (Dec 15 2:00 PM EST) तक
