"""qx doctor — deterministic rule engine over a parsed buildfile.

Each rule returns a list of Finding(level, where, message, fix).
Levels: ERROR (build will fail), WARN (likely pain), INFO (best practice).
"""

from __future__ import annotations

from dataclasses import dataclass

from .parser import Buildfile, BuildEntry


@dataclass
class Finding:
    level: str
    where: str
    message: str
    fix: str


RULE_COUNT = 0


def _rule(fn):
    global RULE_COUNT
    RULE_COUNT += 1
    return fn


def _entry_label(bf: Buildfile, e: BuildEntry) -> str:
    mod = next((m.name for m in bf.modules if e in m.entries), "?")
    return f"{bf.path}:{e.lineno} (module <{mod}>)"


@_rule
def check_env_outside_module(bf: Buildfile):
    for err in bf.errors:
        if "outside a module" in err or "outside any" in err:
            yield Finding(
                "ERROR", bf.path, err,
                "Move PATH=/LD_LIBRARY_PATH= assignments inside a [image]/<module> section — "
                "top-level env vars are ignored by mkqnximage.",
            )


@_rule
def check_path_exists(bf: Buildfile):
    for e in bf.all_entries:
        if e.env_key == "PATH" and e.env_value:
            for p in e.env_value.split(":"):
                if not any(
                    t.target_path and t.target_path.rstrip("/").endswith(p.strip())
                    for t in bf.all_entries
                    if t.target_path
                ) and p.strip() not in (".", "$PATH"):
                    yield Finding(
                        "WARN", _entry_label(bf, e),
                        f"PATH contains '{p.strip()}' but no entry in the buildfile ships that directory.",
                        f"Either ship a binary at '{p.strip()}' or remove it from PATH.",
                    )


@_rule
def check_duplicate_target(bf: Buildfile):
    seen: dict[str, BuildEntry] = {}
    for e in bf.all_entries:
        if not e.target_path or e.env_key:
            continue
        t = e.target_path.rstrip("/")
        if t in seen:
            yield Finding(
                "ERROR", _entry_label(bf, e),
                f"Duplicate target path '{t}' (first at line {seen[t].lineno}).",
                "Keep one — mkqnximage silently overwrites, hiding which binary actually ships.",
            )
        seen[t] = e


@_rule
def check_missing_host_source(bf: Buildfile):
    for e in bf.all_entries:
        if e.target_path and e.target_path.startswith("/") and e.host_source is None and e.env_key is None:
            if e.perms and "c" not in (e.perms or ""):
                yield Finding(
                    "WARN", _entry_label(bf, e),
                    f"Target '{e.target_path}' has no { '{host source}' } block.",
                    "Add { host/path } so mkqnximage can find the file, or verify it comes from a library module.",
                )


@_rule
def check_search_path(bf: Buildfile):
    if not any("search" in (a or "").lower() for a in [*(bf.image_attrs.keys())]):
        yield Finding(
            "INFO", bf.path,
            "No [search=...] attribute set.",
            "Set [search=$QNX_TARGET/cpu/qnx/<arch>] so relative {host} sources resolve.",
        )


@_rule
def check_startup_or_rc(bf: Buildfile):
    targets = [e.target_path for e in bf.all_entries if e.target_path]
    if not any("etc/rc" in t or "sbin/init" in t for t in targets):
        yield Finding(
            "WARN", bf.path,
            "No /etc/rc.d startup script or init found in image.",
            "Add rc.d script via [type=file] entries so the target boots to a usable shell.",
        )


@_rule
def check_quotes_in_perms(bf: Buildfile):
    for e in bf.all_entries:
        if e.perms and ("+" in e.perms or "," in e.perms):
            yield Finding(
                "ERROR", _entry_label(bf, e),
                f"Perms '{e.perms}' contain '+' or ',' — mkqnximage expects plain rwxrwxrwx style.",
                "Rewrite as e.g. [perms=0755] or [type=link perms=rwxrwxrwx].",
            )


@_rule
def check_shadow_host_slashes(bf: Buildfile):
    for e in bf.all_entries:
        if e.host_source and e.host_source.startswith("/"):
            yield Finding(
                "INFO", _entry_label(bf, e),
                f"Host source '{e.host_source}' is absolute.",
                "Prefer paths relative to [search=...] so the image builds on any checkout.",
            )


@_rule
def check_welcome_missing(bf: Buildfile):
    targets = [e.target_path for e in bf.all_entries if e.target_path]
    if any(t.endswith("/etc/rc.d/rc.local") for t in targets) and not any(
        "welcome" in t for t in targets
    ):
        yield Finding(
            "INFO", bf.path,
            "rc.local present but no welcome/message file — QEMU boot looks empty.",
            "Ship /usr/share/welcome or echo a banner from rc.local for nicer demos.",
        )


@_rule
def check_qconn_for_debug(bf: Buildfile):
    targets = " ".join(e.target_path or "" for e in bf.all_entries)
    if "qconn" not in targets and ("rc.d" in targets or "rc.local" in targets):
        yield Finding(
            "WARN", bf.path,
            "Startup script present but qconn (debug agent) is not shipped.",
            "Add /sbin/qconn={QNX_TARGET/<arch>/sbin/qconn} — without it `gdb` attach "
            "and IDE debugging can't reach the target.",
        )


@_rule
def check_devcon_conflict(bf: Buildfile):
    for e in bf.all_entries:
        if e.target_path and "devc-ser" in e.target_path:
            yield Finding(
                "INFO", _entry_label(bf, e),
                "Serial driver devc-ser* present — QEMU x86_64 needs `-serial stdio` "
                "matched to devc-ser8250 with the right IRQ/port.",
                "Default QEMU serial works with: devc-ser8250 -b 115200 -c 0x3f8 -i4 &",
            )


@_rule
def check_io_pkt_variant(bf: Buildfile):
    for e in bf.all_entries:
        if e.target_path and "io-pkt" in e.target_path:
            yield Finding(
                "INFO", _entry_label(bf, e),
                "io-pkt network stack detected.",
                "QNX 8.0 prefers io-sock (BSD stack). If targeting 8.0, consider "
                "migrating to io-sock — io-pkt is legacy and unsupported on some boards.",
            )


@_rule
def check_libc_hardcode(bf: Buildfile):
    for e in bf.all_entries:
        if e.target_path and "libc.so" in e.target_path and e.host_source and "QNX_TARGET" not in e.host_source:
            yield Finding(
                "WARN", _entry_label(bf, e),
                "libc.so.5 copied from a non-QNX_TARGET source — risks version drift.",
                "Reference {QNX_TARGET/<arch>/lib/libc.so.5} so the image always "
                "matches the SDK you compiled against.",
            )


@_rule
def check_empty_module(bf: Buildfile):
    for m in bf.modules:
        if not m.entries:
            yield Finding(
                "WARN", f"{bf.path}:{m.lineno} (module <{m.name}>)",
                f"Module <{m.name}> is empty.",
                "Remove it or add entries — empty modules confuse image diffing and "
                "cost a few bytes in the IFS header.",
            )


@_rule
def check_absolute_host_not_search(bf: Buildfile):
    has_search = any("search" in (k or "").lower() for k in bf.image_attrs)
    abs_sources = sum(
        1
        for e in bf.all_entries
        if e.host_source and e.host_source.startswith("/") and "QNX_TARGET" not in e.host_source
    )
    if abs_sources >= 3 and not has_search:
        yield Finding(
            "WARN", bf.path,
            f"{abs_sources} absolute host-source paths and no [search=...] attribute.",
            "Add [search=<checkout path>] and make {host} sources relative — "
            "builds then work on any machine without edits.",
        )


@_rule
def check_no_interpreter_scripts(bf: Buildfile):
    targets = [e.target_path or "" for e in bf.all_entries]
    if any(t.endswith(".sh") for t in targets) and not any(
        "/bin/sh" in t or "/bin/esh" in t or "ksh" in t for t in targets
    ):
        yield Finding(
            "ERROR", bf.path,
            "Shell scripts (.sh) shipped but no shell binary (/bin/sh or esh) in the image.",
            "Add /bin/esh={QNX_TARGET/<arch>/bin/esh} — scripts won't execute otherwise.",
        )


@_rule
def check_su_commander(bf: Buildfile):
    targets = " ".join(e.target_path or "" for e in bf.all_entries)
    if "passwd" in targets and "sudo" not in targets and "su" not in targets:
        yield Finding(
            "INFO", bf.path,
            "passwd file shipped — consider shipping su or setting root login policy.",
            "Default QNX images boot as root; document it in the codelab if intended.",
        )


@_rule
def check_large_files_no_compress(bf: Buildfile):
    if any("compress" in (k or "").lower() for k in bf.image_attrs.values()):
        return
    big = [
        e
        for e in bf.all_entries
        if e.host_source and any(e.host_source.endswith(ext) for ext in (".so.5", ".so.4", ".a"))
    ]
    if len(big) >= 5:
        yield Finding(
            "INFO", bf.path,
            f"{len(big)} shared libraries shipping uncompressed.",
            "Add [compress=true] (or mkqnximage --compress) to shrink the IFS — "
            "boot time drops on slow storage.",
        )


@_rule
def check_dup_module_name(bf: Buildfile):
    seen = set()
    for m in bf.modules:
        if m.name in seen:
            yield Finding(
                "ERROR", f"{bf.path}:{m.lineno}",
                f"Duplicate module <{m.name}> — second definition overrides entries "
                "in ways that are hard to trace.",
                "Merge the entries into one module block.",
            )
        seen.add(m.name)


@_rule
def check_perf_priority_values(bf: Buildfile):
    for e in bf.all_entries:
        for a in e.attrs:
            if a.startswith("pri="):
                try:
                    pri = int(a.split("=", 1)[1])
                    if pri > 63 or pri < 0:
                        yield Finding(
                            "ERROR", _entry_label(bf, e),
                            f"Priority {pri} out of range (0-63 for adaptive; 255 reserved).",
                            "Use 10 (idle-ish) to 63 (critical). procnto itself runs at 255.",
                        )
                except ValueError:
                    pass


ALL_RULES = [
    check_env_outside_module,
    check_path_exists,
    check_duplicate_target,
    check_missing_host_source,
    check_search_path,
    check_startup_or_rc,
    check_quotes_in_perms,
    check_shadow_host_slashes,
    check_welcome_missing,
    check_qconn_for_debug,
    check_devcon_conflict,
    check_io_pkt_variant,
    check_libc_hardcode,
    check_empty_module,
    check_absolute_host_not_search,
    check_no_interpreter_scripts,
    check_su_commander,
    check_large_files_no_compress,
    check_dup_module_name,
    check_perf_priority_values,
]


def diagnose(bf: Buildfile) -> list[Finding]:
    out: list[Finding] = []
    for rule in ALL_RULES:
        out.extend(rule(bf))
    return out


def summarize(findings: list[Finding]) -> str:
    errors = [f for f in findings if f.level == "ERROR"]
    warns = [f for f in findings if f.level == "WARN"]
    infos = [f for f in findings if f.level == "INFO"]
    lines = [
        f"qx doctor: {len(errors)} errors, {len(warns)} warnings, {len(infos)} tips",
        "",
    ]
    for f in errors + warns + infos:
        mark = {"ERROR": "✗", "WARN": "!", "INFO": "•"}[f.level]
        lines.append(f"{mark} [{f.level}] {f.where}")
        lines.append(f"   {f.message}")
        if f.fix:
            lines.append(f"   → {f.fix}")
        lines.append("")
    return "\n".join(lines)
