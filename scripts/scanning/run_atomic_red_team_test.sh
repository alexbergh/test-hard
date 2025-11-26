#!/usr/bin/env bash
set -euo pipefail

# Wrapper around run_atomic_red_team_suite.py for backwards compatibility.
# Usage examples:
#   ./scripts/run_atomic_red_team_test.sh                  # run curated scenarios
#   ./scripts/run_atomic_red_team_test.sh T1082 run         # run a single technique
#   ./scripts/run_atomic_red_team_test.sh --mode prereqs    # download prerequisites only

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_RUNNER="${SCRIPT_DIR}/run_atomic_red_team_suite.py"

if [[ ! -x "${PYTHON_RUNNER}" ]]; then
  echo "Runner ${PYTHON_RUNNER} is missing or not executable" >&2
  exit 1
fi

MODE="run"
SCENARIO_FILE="${SCENARIO_FILE:-atomic-red-team/scenarios.yaml}"
OUTPUT_DIR="${ART_RESULTS_DIR:-art-storage}"
ATOMICS_PATH="${ATOMICS_PATH:-}"
CACHE_DIR="${ART_CACHE_DIR:-${HOME}/.cache/atomic-red-team}"
TIMEOUT="60"
EXTRA_ARGS=()
POSITIONAL=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      MODE="$2"
      shift 2
      ;;
    --scenarios|--scenario)
      SCENARIO_FILE="$2"
      shift 2
      ;;
    --output|--output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --atomics-path)
      ATOMICS_PATH="$2"
      shift 2
      ;;
    --cache-dir)
      CACHE_DIR="$2"
      shift 2
      ;;
    --timeout)
      TIMEOUT="$2"
      shift 2
      ;;
    --dry-run)
      EXTRA_ARGS+=("--dry-run")
      shift
      ;;
    --help|-h)
      "$PYTHON_RUNNER" --help
      exit 0
      ;;
    --)
      shift
      while [[ $# -gt 0 ]]; do
        EXTRA_ARGS+=("$1")
        shift
      done
      ;;
    -* )
      EXTRA_ARGS+=("$1")
      shift
      ;;
    *)
      POSITIONAL+=("$1")
      shift
      ;;
  esac
done

TECHNIQUE=""
if [[ ${#POSITIONAL[@]} -ge 1 ]]; then
  TECHNIQUE="${POSITIONAL[0]}"
fi
if [[ ${#POSITIONAL[@]} -ge 2 ]]; then
  MODE="${POSITIONAL[1]}"
fi
if [[ ${#POSITIONAL[@]} -ge 3 ]]; then
  EXTRA_ARGS+=("--test-number" "${POSITIONAL[2]}")
fi

CMD=("${PYTHON_RUNNER}" "--mode" "${MODE}" "--timeout" "${TIMEOUT}" "--output" "${OUTPUT_DIR}" "--cache-dir" "${CACHE_DIR}")

if [[ -n "${ATOMICS_PATH}" ]]; then
  CMD+=("--atomics-path" "${ATOMICS_PATH}")
fi

if [[ -n "${TECHNIQUE}" ]]; then
  CMD+=("--technique" "${TECHNIQUE}")
else
  CMD+=("--scenarios" "${SCENARIO_FILE}")
fi

CMD+=("${EXTRA_ARGS[@]}")

exec "${CMD[@]}"
