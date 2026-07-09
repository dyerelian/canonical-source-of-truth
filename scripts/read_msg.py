#!/usr/bin/env python3
"""Read a saved Outlook .msg file and print its headers + body as plain text.

Usage:
    & 'C:\\Program Files\\Python312\\python.exe' read_msg.py "<path-to.msg>"

Prints SUBJECT / FROM / TO / CC / DATE / ATTACHMENTS, then the body. Read-only.
Requires the `extract_msg` package:
    py -m pip install extract_msg --trusted-host pypi.org --trusted-host files.pythonhosted.org
(the corporate network needs --trusted-host for pip; `py`, not `python`).
"""
import sys


def main(argv):
    if len(argv) < 2:
        print("usage: read_msg.py <path-to.msg>", file=sys.stderr)
        return 2
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    try:
        import extract_msg
    except ImportError:
        print(
            "extract_msg not installed. Install with:\n"
            "  py -m pip install extract_msg --trusted-host pypi.org "
            "--trusted-host files.pythonhosted.org",
            file=sys.stderr,
        )
        return 3

    path = argv[1]
    m = extract_msg.Message(path)
    print("SUBJECT:", m.subject)
    print("FROM:", m.sender)
    print("TO:", m.to)
    print("CC:", m.cc)
    print("DATE:", m.date)
    try:
        names = [a.longFilename or a.shortFilename for a in m.attachments]
    except Exception:
        names = []
    print("ATTACHMENTS:", names)
    print("=" * 70)
    print(m.body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
