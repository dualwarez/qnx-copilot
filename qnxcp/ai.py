"""qx explain — hybrid error explainer.

Deterministic knowledge base first (works air-gapped, instant), optional LLM
enrichment second (`--ai` flag reads OPENAI_API_KEY / GEMINI_API_KEY).
"""

from __future__ import annotations

import os
import re
import urllib.request
import json as _json

KB: list[tuple[str, str, str]] = [
    (
        r"procnto.*segfault|SIGSEGV|signal 11",
        "procnto or your process took SIGSEGV — usually a NULL deref in a driver or "
        "resource-manager before its attach finished.",
        "Attach with gdb via qconn (pdebug): `qnx-gdb :8000` on host. Check "
        "dispatch_loop attach order; guard resource manager io_connect handlers "
        "until resmgr_attach returns.",
    ),
    (
        r"mkqnximage.*not found|mkqnximage: command not found",
        "mkqnximage lives in the host utilities, not in the target PATH.",
        "Source the QNX environment: on Windows run qnxsdp-env.bat from the SDP "
        "install; on Linux `. ~/qnx800/qnx-8.0.0/qnxsdp-env.sh`. Then re-run.",
    ),
    (
        r"no such file.*ifs|image.*0 bytes|mkifs.*error",
        "mkifs produced an empty/missing IFS — usually a missing {host source} "
        "block or wrong [search=...] so relative sources didn't resolve.",
        "Run `qx doctor` on the .build file; check every entry with a target path "
        "has {host/path} or is covered by [search=$QNX_TARGET/...].",
    ),
    (
        r"priority inversion|priority.*inherit",
        "QNX flags mutex priority inversion — real-time scheduling hazard.",
        "Set PTHREAD_PRIO_INHERIT on the mutex or align thread priorities; "
        "never hold a mutex across blocking I/O in time-critical paths.",
    ),
    (
        r"qconn|pdebug.*refused|:8000",
        "qconn debug agent isn't running on the target.",
        "Add `qconn` to your buildfile's PATH or launch `qconn port=8000 &` from "
        "an rc script; then connect with `qnx-gdb :8000`.",
    ),
    (
        r"undefined reference to `(__errno|errno_location)",
        "errno is thread-local in QNX — you can't link it as a normal symbol.",
        "Compile with the QNX toolchain headers (qcc), not plain gcc; include "
        "<errno.h> and use the macro, never an extern errno symbol.",
    ),
    (
        r"leaked file descriptor|SLAY.*could not|slay.*no such",
        "slay targets processes by name on the running target.",
        "Ensure the process is running on the target (ps -ef over ssh/serial) and "
        "slay comes from the target shell, not the host.",
    ),
]


def explain(error_text: str, use_ai: bool = False) -> str:
    out = ["qx explain — top matches:", ""]
    matched = 0
    for pattern, what, fix in KB:
        if re.search(pattern, error_text, re.IGNORECASE):
            matched += 1
            out.append(f"● {what}")
            out.append(f"  fix → {fix}")
            out.append("")
            if matched >= 3:
                break
    if not matched:
        out.append("No deterministic match in the offline knowledge base.")
        out.append("Re-run with `--ai` (needs OPENAI_API_KEY or GEMINI_API_KEY) for LLM analysis.")
    if use_ai:
        extra = _llm_explain(error_text)
        if extra:
            out.append("── LLM enrichment ──")
            out.append(extra)
    return "\n".join(out)


def _llm_explain(error_text: str) -> str | None:
    openai_key = os.environ.get("OPENAI_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    prompt = (
        "You are a QNX 8.0 RTOS expert. Explain this QNX build/run error concisely "
        "and give a concrete fix (max 120 words):\n\n" + error_text[:2000]
    )
    try:
        if openai_key:
            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=_json.dumps(
                    {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}]}
                ).encode(),
                headers={"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=20) as r:
                data = _json.load(r)
                return data["choices"][0]["message"]["content"].strip()
        if gemini_key:
            req = urllib.request.Request(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key="
                + gemini_key,
                data=_json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode(),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=20) as r:
                data = _json.load(r)
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:  # noqa: BLE001 - best effort enrichment only
        return f"(LLM call failed: {e})"
    return None
