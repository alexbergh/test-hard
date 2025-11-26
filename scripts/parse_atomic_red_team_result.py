#!/usr/bin/env python3
"""Compatibility wrapper for parsing Atomic Red Team results."""
from parsing.parse_atomic_red_team_result import main

# Re-export for backward compatibility
__all__ = ["main"]


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: parse_atomic_red_team_result.py <result.json>", file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1])
