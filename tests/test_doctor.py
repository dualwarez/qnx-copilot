import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from qnxcp.parser import parse_buildfile
from qnxcp.doctor import diagnose

SAMPLE = """\
# sample buildfile
[image=usb ]
<bin>
PATH=/bin:/usr/bin
/etc/rc.d/rc.local={scripts/rc.local}
/bin/qn={source/bin/qn}
/bin/echo=[perms=rwxrwxrwx]
/usr/lib/libhello.so.1={build/libhello.so.1}
"""

BAD = """\
[image=usb]
<bin>
PATH=/bin:/nowhere
/bin/qn={a/qn}
/bin/qn={b/qn}
LD_LIBRARY_PATH=/usr/lib
"""


def test_doctor_flags_duplicates_and_missing_path():
    bf = parse_buildfile(BAD, "bad.build")
    f = diagnose(bf)
    msgs = [x.message for x in f]
    assert any("Duplicate target path" in m for m in msgs)
    assert any("'/nowhere'" in m for m in msgs)


def test_doctor_clean_sample_no_errors():
    bf = parse_buildfile(SAMPLE, "good.build")
    f = diagnose(bf)
    errs = [x for x in f if x.level == "ERROR"]
    assert errs == []
    assert any(x.level == "INFO" for x in f)  # search hint etc.


def test_parser_env_and_braces():
    bf = parse_buildfile(SAMPLE)
    entries = list(bf.all_entries)
    assert any(e.env_key == "PATH" for e in entries)
    assert any(e.host_source == "build/libhello.so.1" for e in entries)
    assert any(e.perms == "rwxrwxrwx" for e in entries)
