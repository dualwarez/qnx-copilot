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
    "output/ifs.bin",          # mkqnximage --boot-mode=qemu output
    "ifs.bin",
    "output/disk-qemu.vmdk",   # ide disk paired with the IFS
    "disk-qemu.vmdk",
]

DISK_CANDIDATES = [
    "output/disk-qemu.vmdk",
    "disk-qemu.vmdk",
    "output/disk-qemu",
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
        "-smp", "2",
        "-cpu", "max",
    ]
    if arch == "x86_64":
        # Verified live QNX 8.0 boot recipe (see docs/QNX-EVIDENCE.md):
        #   -kernel <ifs.bin>  (multiboot IFS is the boot payload)
        #   -drive disk-qemu.vmdk,if=ide  (system/data partitions)
        cmd += ["-kernel", str(image)]
        disk = find_disk(image.parent)
        if disk:
            cmd += ["-drive", f"file={disk},if=ide"]
        cmd += ["-display", "none" if platform.system() != "Windows" else "sdl"]
        cmd += ["-serial", "file:serial_out.txt" if platform.system() == "Windows" else "stdio"]
        if forward:
            cmd += ["-netdev", f"user,id=n0,hostfwd=tcp::{forward}", "-device", "virtio-net-pci,netdev=n0"]
        if uefi:
            cmd += ["-bios", "OVMF.fd"]
    else:
        cmd += ["-M", "virt", "-cpu", "cortex-a57", "-nographic"]
        cmd += ["-kernel", str(image)]
        if forward:
            cmd += ["-netdev", f"user,id=n0,hostfwd=tcp::{forward}", "-device", "virtio-net-pci,netdev=n0"]
    return cmd


def find_disk(root: Path) -> Path | None:
    for name in DISK_CANDIDATES:
        p = root / name if not name.startswith("output/") else root.parent / name
        if p.is_file():
            return p
        p2 = root / name
        if p2.is_file():
            return p2
    return None


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
