#!/usr/bin/env python3
"""Compatibility wrapper for parsing OpenSCAP reports."""
from parsing.parse_openscap_report import _latest_report, main

__all__ = ["main", "_latest_report"]


if __name__ == "__main__":
    import sys

    raise SystemExit(main(sys.argv[1:]))
