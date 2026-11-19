"""QNX buildfile grammar parser.

Parses QNX 8.0 system-builder buildfiles (*.build) into a structured model so
rules can be checked deterministically. Covers the commonly used grammar:

  [image=...] [search=...] [perms=...]     # image attributes
  <module>                                 # named module sections
  NAME=[perms attr] /path/on/target { /host/source } optional_suffix
  PATH=... LD_LIBRARY_PATH=...             # env assignments (inside .file)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class BuildEntry:
    """One line inside an image section."""
    lineno: int
    raw: str
    target_path: str | None = None
    host_source: str | None = None
    perms: str | None = None
    attrs: list[str] = field(default_factory=list)
    env_key: str | None = None
    env_value: str | None = None


@dataclass
class Module:
    name: str
    lineno: int
    attrs: dict[str, str] = field(default_factory=dict)
    entries: list[BuildEntry] = field(default_factory=list)


@dataclass
class Buildfile:
    path: str
    image_attrs: dict[str, str] = field(default_factory=dict)
    modules: list[Module] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def all_entries(self):
        for m in self.modules:
            yield from m.entries


# --- grammar helpers -------------------------------------------------------

_LINE_SECTION = re.compile(r"^\[([^\]]+)\]\s*(.*)$")
_MODULE = re.compile(r"^<\s*([A-Za-z0-9_+\-]+)\s*>$")
_ENTRY = re.compile(r"^([^=\s\[]+)\s*=\s*(.+)$")
_ENV = re.compile(r"^([A-Z_][A-Z0-9_]*)\s*=\s*(.*)$")
_BRACES = re.compile(r"\{([^}]*)\}")
_PERMS = re.compile(r"\[?([\-a-zA-Z]+)(?:\s+([0-9]+))?\]?$")


def parse_buildfile(text: str, path: str = "<memory>") -> Buildfile:
    bf = Buildfile(path=path)
    current: Module | None = None

    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.rstrip()
        stripped = line.strip()

        # skip comments / blank
        if not stripped or stripped.startswith("#") or stripped.startswith("//"):
            continue

        m = _MODULE.match(stripped)
        if m:
            current = Module(name=m.group(1), lineno=lineno)
            bf.modules.append(current)
            continue

        # [attr=value ...] prefix — either top-level image attrs or per-line attrs
        rest = stripped
        while True:
            m = _LINE_SECTION.match(rest)
            if not m:
                break
            for pair in m.group(1).split(","):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    if current is None:
                        bf.image_attrs[k.strip()] = v.strip()
                    else:
                        current.attrs[k.strip()] = v.strip()
                elif current is not None:
                    current.attrs[pair.strip()] = ""
            rest = m.group(2).strip()
            if not rest:
                break

        if not rest:
            continue

        if rest.startswith("PATH=") or _ENV.match(rest) and current is not None and rest.split("=", 1)[0].isupper() and " " not in rest.split("=", 1)[0]:
            m = _ENV.match(rest)
            if m:
                if current is None:
                    bf.errors.append(f"line {lineno}: env var {m.group(1)} outside a module")
                else:
                    current.entries.append(
                        BuildEntry(lineno=lineno, raw=raw, env_key=m.group(1), env_value=m.group(2))
                    )
                continue

        if current is None:
            bf.errors.append(f"line {lineno}: entry outside any [image]/<module> section: {stripped[:60]}")
            continue

        # normal file entry: NAME[=perms/attrs] target { source }
        entry = BuildEntry(lineno=lineno, raw=raw)
        if "{" in rest and "}" in rest:
            m = _BRACES.search(rest)
            if m:
                entry.host_source = m.group(1).strip()
                rest = rest[: m.start()] + rest[m.end():].strip()

        # bracket attrs: NAME=[perms=rwx type=link] or [perms=0755]
        br = re.search(r"\[([^\]]+)\]\s*(.*)$", rest)
        if br:
            for pair in br.group(1).split():
                if pair.lower().startswith("perms="):
                    entry.perms = pair.split("=", 1)[1]
            before, after = rest[: br.start()], rest[br.end():]
            rest = (before + " " + after).strip().rstrip("=").strip()

        m = _ENTRY.match(rest)
        if m:
            left, right = m.group(1).strip(), m.group(2).strip()
            pm = _PERMS.match(right)
            if pm and not right.startswith("/"):
                entry.perms = entry.perms or pm.group(1)
                candidate = right[len(pm.group(0)):].strip()
            else:
                candidate = right
            entry.target_path = candidate.rstrip("=").strip() or left.rstrip("=").strip()
            entry.attrs.append(left.rstrip("=").strip())
        else:
            entry.target_path = rest.rstrip("=").strip()

        current.entries.append(entry)

    return bf
