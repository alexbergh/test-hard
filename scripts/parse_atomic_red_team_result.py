#!/usr/bin/env python3
import sys, json, os

# Заготовка: если у вас есть JSON-вывод из своего раннера — преобразуйте его.
# Ожидается распечатка строк в стиле Prometheus:
# art_test_result{host="host", test="Txxxx"} 0|1

def main(path):
    with open(path, "r") as f:
        data = json.load(f)
    host = data.get("host", os.uname().nodename)
    for t in data.get("tests", []):
        test_id = t.get("id", "unknown")
        result = 1 if t.get("passed", False) is False else 0
        print(f'art_test_result{{host="{host}",test="{test_id}"}} {result}')

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: parse_atomic_red_team_result.py <result.json>", file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1])
