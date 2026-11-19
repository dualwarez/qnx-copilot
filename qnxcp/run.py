"""qx run — boot a buildfile-generated image in QEMU with sane defaults.

Supports x86_64 and aarch64 targets; auto-finds qnx-image files produced by
mkqnximage, wires up serial-to-stdio and a forwarded guest port.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

QEMU_BINARIES = {
    "x86_64": "qemu-system-x86_64",
    "aarch64": "qemu-system-aarch64",
}

# well-known mkqnximage outputs
IMAGE_CANDIDATES = [
    "qnx-image.img",
    "images/qnx-image.img",
    "ifs/qnx-image.img",
    "qnx-ifs",
    "ifs.bin",
]


def find_image(root: Path) -> Path | None:
    for name in IMAGE_CANDIDATES:
        p = root / name
        if p.is_file():
            return p
    hits = [p for p in root.rglob("*.img") if p.is_file()] + [
        p for p in root.rglob("*ifs*") if p.is_file() and p.stat().st_size > 100_000
    ]
    return hits[0] if hits else None


def qemu_binary(arch: str) -> str:
    qemu = shutil.which(QEMU_BINARIES.get(arch, QEMU_BINARIES["x86_64"]))
    if not qemu:
        raise SystemExit(
            f"qemu-system-{arch} not found on PATH.\n"
            "Install: Windows → https://qemu.weilnetz.de/ | Ubuntu → sudo apt install qemu-system-x86"
        )
    return qemu


def build_command(arch: str, image: Path, memory: str, forward: str | None, uefi: bool) -> list[str]:
    cmd = [
        qemu_binary(arch),
        "-m", memory,
        "-serial", "stdio",
        "-display", "none" if platform.system() != "Windows" else "sdl",
    ]
    if arch == "x86_64":
        cmd += ["-drive", f"file={image},format=raw,if=virtio"]
        cmd += ["-netdev", f"user,id=n0{',hostfwd=tcp::' + forward if forward else ''}", "-device", "virtio-net,netdev=n0"]
        if uefi:
            cmd += ["-bios", "OVMF.fd"]
    else:
        cmd += ["-M", "virt", "-cpu", "cortex-a57", "-nographic"]
        cmd += ["-drive", f"file={image},format=raw,if=virtio"]
        if forward:
            cmd += ["-netdev", f"user,id=n0,hostfwd=tcp::{forward}", "-device", "virtio-net-pci,netdev=n0"]
    return cmd


def run_image(root: Path, arch: str = "x86_64", memory: str = "512M", forward: str | None = None, uefi: bool = False):
    image = find_image(root)
    if not image:
        raise SystemExit(
            "No QNX image found. Run mkqnximage first (or set QNX_IMAGE env var).\n"
            "Tried: " + ", ".join(IMAGE_CANDIDATES)
        )
    print(f"[qx run] arch={arch} image={image}")
    cmd = build_command(arch, image, memory, forward, uefi)
    print("[qx run] " + " ".join(cmd))
    try:
        subprocess.run(cmd, check=False)
    except KeyboardInterrupt:
        print("\n[qx run] guest stopped.")
