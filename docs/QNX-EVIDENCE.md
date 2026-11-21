# QNX SDP 8.0 — Real E2E Evidence

Date: 2026-11-21 | Host: Windows 11 x64 | All steps automated (zero manual form-filling)

## 1. SDP installation (myQNX → Software Center → CLC)

- myQNX account: created + activated (email confirmation refnum flow), logged in.
- Non-commercial license requested on qnx.com/products/everywhere (license agreement
  accepted via License Manager: "License agreement recorded successfully", then deployed
  to the account email: status "Deployed").
- QNX Software Center 2.0.4 installed silently: `qnx-setup-2.0.4-202501021438-win.exe --unattended`.
- License key activated via command-line client:
  - `qnxsoftwarecenter_clt.bat -addLicenseKey 3H0V-N9E3-XX0U-R3TF-32T6`
  - `-listLicenseKeys` → `[3H0V-...] - Activated - QNX Software Development Platform 8.0`
- SDP 8.0 baseline installed: `qnxsoftwarecenter_clt.bat -installPackage com.qnx.qnx800
  -destination C:\QNX800` (4.7 GB). QEMU support packages installed the same way:
  `com.qnx.qnx800.target.pci.hw.x86`, `com.qnx.qnx800.target.net.devsvirtio`.

## 2. Toolchain verification

```
> qcc -V
cc: targets available in C:/QNX800/host/win64/x86_64/etc/qcc:
    12.2.0,gcc_ntoaarch64le
    12.2.0,gcc_ntox86_64
    ...
> mkqnximage --help=brief   (options list OK)
> mkifs, mkqnx6fsimg, mkifs  (all on PATH after qnxsdp-env)
```

## 3. QNX 8.0 image build (mkqnximage --boot-mode=qemu)

```
> mkqnximage --boot-mode=qemu --clean --force
Generating system partition . . .
Generating data partition . . .
Generating ifs . . .
Building boot partition . . .
Building disk . . .
Target type: qemu
Architecture: x86_64
(output/disk-qemu.vmdk, output/disk-qemu, output/ifs.bin produced)
```

## 4. QEMU boot — QNX Neutrino 8.0 up

```
> qemu-system-x86_64 -m 512 -smp 2 -cpu max ^
    -drive file=output/disk-qemu.vmdk,if=ide ^
    -kernel output/ifs.bin ^
    -serial file:serial_out.txt

Startup complete
QNX noname 8.0.0 2026/10/30-09:10:05EDT x86pc x86_64
```

Full serial boot log: [qnx-boot-serial.log](qnx-boot-serial.log)
Screenshot of the QEMU window: [qnx-boot-screenshot.png](qnx-boot-screenshot.png)

## 5. How QNX Copilot maps to this flow

| QNX Copilot command  | Real QNX flow automated                                                              |
|----------------------|--------------------------------------------------------------------------------------|
| `qx doctor`          | 20 lint rules over the buildfile grammar before mkifs/mkqnximage ever runs            |
| `qx build`           | wraps mkqnximage (`--boot-mode=qemu`, clean build) + parses the 6 failure signatures  |
| `qx run`             | boots the produced IFS (`-kernel ifs.bin` + ide disk) and captures the serial console |
| `qx explain`         | explains the exact failures this flow produces (missing packages, virtio deps, etc.)  |

The whole chain — myQNX registration → license acceptance → deployment → activation →
SDP installation → image build → QEMU boot — was driven end-to-end by automation.
