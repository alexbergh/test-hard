#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: parse_atomic_red_team_result.py <result.json>", file=sys.stderr)
        sys.exit(1)

    result_path = Path(sys.argv[1])
    if not result_path.exists():
        print(f"Result file {result_path} does not exist", file=sys.stderr)
        sys.exit(1)

    with result_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    host = data.get("host", os.uname().nodename)
    for test in data.get("tests", []):
        test_id = test.get("id", "unknown")
        result = 1 if not test.get("passed", False) else 0
        print(f"art_test_result{{host=\"{host}\",test=\"{test_id}\"}} {result}")


if __name__ == "__main__":
    main()
