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
