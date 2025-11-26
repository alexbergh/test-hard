#!/usr/bin/env python3
"""Compatibility wrapper for parsing Lynis reports."""
from parsing.parse_lynis_report import parse_lynis_report

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: parse_lynis_report.py <path_to_lynis_json_report>", file=sys.stderr)
        sys.exit(1)
    parse_lynis_report(sys.argv[1])
