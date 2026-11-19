"""qx codelab — generate a Markdown codelab skeleton for the current project."""

from __future__ import annotations

from pathlib import Path

TEMPLATE = """# {title} — a QNX 8.0 codelab

> Auto-generated skeleton by `qx codelab`. Fill the ⬛ placeholders.

## What you'll build

⬛ One paragraph: the outcome. What will a reader have running at the end?

## Prerequisites

- QNX SDP 8.0 (free non-commercial license) with `qnxsdp-env` sourced
- QEMU (system emulator) installed
- This repo checked out

## Step 1 — Understand the buildfile ⬛

Explain the buildfile sections this project uses, with a short annotated snippet.

## Step 2 — Build the image

```sh
source ~/qnx800/qnx-8.0.0/qnxsdp-env.sh
mkqnximage -o images/ -t x86_64 project.build
```

✅ Checkpoint: `images/qnx-image.img` exists and is > 1 MB.

## Step 3 — Run it in QEMU

```sh
qx run --arch x86_64 --forward 8000
```

✅ Checkpoint: you see the QNX login prompt on serial.

## Step 4 — ⬛ (the interesting part)

## What you learned

- ⬛
- ⬛

## Next steps

- Link to your `qx doctor` output for this project
- Where to file issues
"""


def generate(root: Path):
    out = root / "CODELAB.md"
    title = root.resolve().name.replace("-", " ").title()
    out.write_text(TEMPLATE.format(title=title), encoding="utf-8")
    print(f"[qx codelab] wrote {out}")
    print("Fill the ⬛ placeholders, then submit the codelab URL for the Best Codelab prize.")
