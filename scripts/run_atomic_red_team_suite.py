#!/usr/bin/env python3
"""Execute curated Atomic Red Team scenarios and persist structured results."""
from __future__ import annotations

import argparse
import json
import logging
import os
import socket
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

try:
    from atomic_operator.atomic_operator import AtomicOperator
except ImportError as exc:  # pragma: no cover - dependency check
    logger.error(
        "atomic_operator is required. Install with 'pip install atomic-operator attrs click'."
    )
    raise

try:
    import yaml
except ImportError as exc:  # pragma: no cover - dependency check
    logger.error("PyYAML is required. Install with 'pip install pyyaml'.")
    raise

STATUS_ORDER = {"passed": 0, "skipped": 1, "failed": 2, "error": 3, "unknown": 4}
STATUS_TO_VALUE = {"passed": 0, "failed": 1, "skipped": 2, "error": 3, "unknown": 4}


@dataclass
class TestSpec:
    """Normalized test specification pulled from YAML or CLI input."""

    number: int
    description: Optional[str] = None
    arguments: Dict[str, str] = field(default_factory=dict)
    copy_source_files: Optional[bool] = None
    get_prereqs_before_run: bool = False


@dataclass
class ScenarioSpec:
    """Container describing a logical scenario composed of atomic tests."""

    id: str
    technique: str
    technique_name: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    detection: Optional[List[str]] = None
    supported_platforms: Optional[List[str]] = None
    tests: List[TestSpec] = field(default_factory=list)
    source: str = "scenarios"


@dataclass
class TestResult:
    guid: str
    number: int
    name: str
    executor: str
    supported_platforms: List[str]
    status: str
    return_code: Optional[int] = None
    start_timestamp: Optional[str] = None
    end_timestamp: Optional[str] = None
    command: Optional[str] = None
    output: Optional[str] = None
    error: Optional[str] = None


@dataclass
class ScenarioResult:
    spec: ScenarioSpec
    technique_name: Optional[str]
    tests: List[TestResult]
    status: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Atomic Red Team scenarios and persist results for metrics ingestion."
    )
    parser.add_argument(
        "--scenarios",
        default="atomic-red-team/scenarios.yaml",
        help="Path to a YAML file describing curated scenarios.",
    )
    parser.add_argument(
        "--technique",
        help="Run a specific technique instead of the scenario file.",
    )
    parser.add_argument(
        "--test-number",
        action="append",
        type=int,
        dest="test_numbers",
        help="Restrict execution to one or more Atomic test numbers (when using --technique).",
    )
    parser.add_argument(
        "--mode",
        choices=["run", "check", "prereqs", "cleanup"],
        default="run",
        help="Execution mode: run atomics, check prerequisites, download prerequisites, or cleanup.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Command timeout passed to atomic-operator (seconds).",
    )
    parser.add_argument(
        "--output",
        default="art-storage",
        help="Directory where JSON history and Prometheus metrics will be written.",
    )
    parser.add_argument(
        "--atomics-path",
        help="Path to an Atomic Red Team repository clone. If omitted a cache under ~/.cache is used.",
    )
    parser.add_argument(
        "--cache-dir",
        default="~/.cache/atomic-red-team",
        help="Location for downloading the Atomic Red Team repository when --atomics-path is not provided.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only resolve scenarios and emit metadata without executing any tests.",
    )
    return parser.parse_args()


def load_scenarios(args: argparse.Namespace) -> List[ScenarioSpec]:
    if args.technique:
        logger.info("Loading technique %s from CLI", args.technique)
        tests = []
        if args.test_numbers:
            for number in args.test_numbers:
                tests.append(TestSpec(number=number))
        scenario = ScenarioSpec(
            id=args.technique.lower(),
            technique=args.technique,
            name=f"Atomic technique {args.technique}",
            tests=tests,
            source="cli",
        )
        return [scenario]

    scenario_path = Path(args.scenarios)
    logger.info("Loading scenarios from %s", scenario_path)
    if not scenario_path.exists():
        logger.error("Scenario file not found: %s", scenario_path)
        raise FileNotFoundError(f"Scenario file {scenario_path} does not exist")
    with scenario_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    scenarios: List[ScenarioSpec] = []
    for entry in payload.get("scenarios", []):
        tests = entry.get("tests", [])
        normalized: List[TestSpec] = []
        for item in tests:
            if isinstance(item, int):
                normalized.append(TestSpec(number=item))
            elif isinstance(item, dict):
                normalized.append(
                    TestSpec(
                        number=int(item["number"]),
                        description=item.get("description"),
                        arguments=item.get("arguments", {}),
                        copy_source_files=item.get("copy_source_files"),
                        get_prereqs_before_run=item.get("get_prereqs_before_run", False),
                    )
                )
            else:
                raise ValueError(f"Unsupported test entry: {item}")
        scenarios.append(
            ScenarioSpec(
                id=str(entry.get("id") or entry.get("technique")),
                technique=str(entry["technique"]),
                technique_name=entry.get("technique_name"),
                name=entry.get("name"),
                description=entry.get("description"),
                detection=entry.get("detection"),
                supported_platforms=entry.get("supported_platforms"),
                tests=normalized,
            )
        )
    if not scenarios:
        logger.error("No scenarios found in %s", scenario_path)
        raise ValueError(f"No scenarios declared in {scenario_path}")
    logger.info("Loaded %d scenario(s)", len(scenarios))
    return scenarios


def ensure_repo(operator: AtomicOperator, args: argparse.Namespace) -> Path:
    """Return a path containing Atomic Red Team test definitions."""

    if args.atomics_path:
        provided = Path(args.atomics_path).expanduser().resolve()
        logger.info("Using provided atomics path: %s", provided)
        resolved = find_atomics_root(provided)
        if resolved:
            logger.info("Found atomics directory at: %s", resolved)
            return resolved
        logger.error("Unable to locate atomics directory at: %s", provided)
        raise FileNotFoundError(
            f"Unable to locate an 'atomics' directory beneath {provided}."
        )

    cache_root = Path(os.path.expanduser(args.cache_dir)).resolve()
    cache_root.mkdir(parents=True, exist_ok=True)
    logger.info("Using cache directory: %s", cache_root)

    resolved = find_atomics_root(cache_root)
    if resolved:
        logger.info("Found existing atomics at: %s", resolved)
        return resolved

    logger.info("Downloading Atomic Red Team repository to cache")
    try:
        download_hint = operator.download_atomic_red_team_repo(str(cache_root))
    except Exception as exc:
        logger.error("Failed to download repository: %s", exc)
        raise
    
    resolved = find_atomics_root(cache_root, download_hint)
    if resolved:
        logger.info("Successfully downloaded atomics to: %s", resolved)
        return resolved
    
    logger.error("Failed to locate downloaded repository")
    raise FileNotFoundError(
        "Failed to download Atomic Red Team repository. Specify --atomics-path manually."
    )


def find_atomics_root(base: Path, hint: Optional[str] = None) -> Optional[Path]:
    """Locate a directory that contains the Atomic Red Team 'atomics' folder."""

    candidates: Iterable[Path]
    if hint:
        hint_path = Path(hint)
        if not hint_path.is_absolute():
            hint_path = base / hint_path
        candidates = [hint_path]
    else:
        candidates = [base]

    for candidate in candidates:
        if candidate.is_file():
            continue
        if (candidate / "atomics").is_dir():
            return candidate
        for child in candidate.iterdir():
            if child.is_dir() and (child / "atomics").is_dir():
                return child
    return None


def severity(status: str) -> int:
    return STATUS_ORDER.get(status, STATUS_ORDER["unknown"])


def combine_status(current: str, new: str) -> str:
    if severity(new) > severity(current):
        return new
    return current


def parse_response_payload(raw: Dict) -> Dict:
    payload = raw.get("response") if isinstance(raw, dict) else None
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, str):
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            return {"raw": payload}
    return {}


def execute_test(
    operator: AtomicOperator,
    repo_path: Path,
    technique_id: str,
    test_obj,
    spec: TestSpec,
    mode: str,
    timeout: int,
    dry_run: bool,
) -> TestResult:
    guid = getattr(test_obj, "auto_generated_guid")
    result_kwargs = dict(
        techniques=[technique_id],
        atomics_path=str(repo_path),
        test_guids=[guid],
        command_timeout=timeout,
    )
    if spec.arguments:
        result_kwargs["input_arguments"] = spec.arguments
    if spec.copy_source_files is not None:
        result_kwargs["copy_source_files"] = bool(spec.copy_source_files)

    if mode == "check":
        result_kwargs["check_prereqs"] = True
    elif mode == "prereqs":
        result_kwargs["get_prereqs"] = True
    elif mode == "cleanup":
        result_kwargs["cleanup"] = True

    status = "skipped" if dry_run else "unknown"
    response_data: Dict[str, Dict] = {}
    error_message: Optional[str] = None

    if dry_run:
        response = {}
    else:
        try:
            if spec.get_prereqs_before_run and mode == "run":
                operator.run(
                    techniques=[technique_id],
                    atomics_path=str(repo_path),
                    test_guids=[guid],
                    get_prereqs=True,
                    command_timeout=timeout,
                )
            response = operator.run(**result_kwargs) or {}
        except Exception as exc:  # pragma: no cover - runtime execution branch
            response = {}
            status = "error"
            error_message = str(exc)
            logger.error("Test %s execution error: %s", guid, exc)
        else:
            response_data = response.get(guid, {})
            payload = parse_response_payload(response_data)
            return_code = payload.get("return_code")
            if response_data.get("error"):
                status = "error"
                error_message = response_data["error"]
                logger.warning("Test %s reported error: %s", guid, error_message)
            elif return_code is None:
                status = "skipped"
                logger.debug("Test %s skipped", guid)
            elif return_code == 0:
                status = "passed"
                logger.info("Test %s passed", guid)
            else:
                status = "failed"
                logger.warning("Test %s failed with code %s", guid, return_code)

            response_data = payload

    return TestResult(
        guid=guid,
        number=spec.number,
        name=getattr(test_obj, "name", f"Test {spec.number}"),
        executor=getattr(getattr(test_obj, "executor", None), "name", "unknown"),
        supported_platforms=getattr(test_obj, "supported_platforms", []),
        status=status,
        return_code=response_data.get("return_code"),
        start_timestamp=response_data.get("start_timestamp"),
        end_timestamp=response_data.get("end_timestamp"),
        command=response_data.get("command"),
        output=response_data.get("output"),
        error=error_message or response_data.get("error"),
    )


def run_scenario(
    operator: AtomicOperator,
    repo_path: Path,
    scenario: ScenarioSpec,
    mode: str,
    timeout: int,
    dry_run: bool,
) -> ScenarioResult:
    logger.info("Running scenario: %s (technique: %s, mode: %s)", 
                scenario.name or scenario.id, scenario.technique, mode)
    
    tech_data = operator.run(
        techniques=[scenario.technique],
        atomics_path=str(repo_path),
        return_atomics=True,
    )
    if not tech_data:
        logger.error("Technique %s not found in repository", scenario.technique)
        raise ValueError(f"Technique {scenario.technique} not found in repository")
    technique = tech_data[0]

    tests_to_run: List[TestSpec]
    if scenario.tests:
        tests_to_run = scenario.tests
    else:
        tests_to_run = [TestSpec(number=index + 1) for index in range(len(technique.atomic_tests))]

    results: List[TestResult] = []
    scenario_status = "passed"
    for spec in tests_to_run:
        try:
            test_obj = technique.atomic_tests[spec.number - 1]
        except IndexError as exc:
            logger.error("Test number %d not found in technique %s", 
                        spec.number, scenario.technique)
            raise IndexError(
                f"Technique {scenario.technique} does not have test number {spec.number}"
            ) from exc

        test_result = execute_test(
            operator,
            repo_path,
            scenario.technique,
            test_obj,
            spec,
            mode,
            timeout,
            dry_run,
        )
        results.append(test_result)
        scenario_status = combine_status(scenario_status, test_result.status)

    logger.info("Scenario %s completed with status: %s", scenario.id, scenario_status)
    return ScenarioResult(
        spec=scenario,
        technique_name=getattr(technique, "display_name", None),
        tests=results,
        status=scenario_status,
    )


def write_outputs(
    output_dir: Path,
    hostname: str,
    mode: str,
    repo_path: Path,
    scenario_results: List[ScenarioResult],
) -> Path:
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    history_dir = output_dir / "history"
    prom_dir = output_dir / "prometheus"
    history_dir.mkdir(parents=True, exist_ok=True)
    prom_dir.mkdir(parents=True, exist_ok=True)

    summary = {"passed": 0, "failed": 0, "skipped": 0, "error": 0, "unknown": 0, "total": 0}
    serialisable_results = []
    prom_lines = [
        "# HELP art_test_result Atomic Red Team test status (0=passed,1=failed,2=skipped,3=error,4=unknown)",
        "# TYPE art_test_result gauge",
    ]
    prom_scenario_lines = [
        "# HELP art_scenario_status Atomic Red Team scenario status (0=passed,1=failed,2=skipped,3=error,4=unknown)",
        "# TYPE art_scenario_status gauge",
    ]

    for scenario in scenario_results:
        scenario_entry = {
            "id": scenario.spec.id,
            "name": scenario.spec.name,
            "technique": scenario.spec.technique,
            "technique_name": scenario.technique_name,
            "supported_platforms": scenario.spec.supported_platforms,
            "status": scenario.status,
            "tests": [],
            "source": scenario.spec.source,
        }
        for test in scenario.tests:
            summary["total"] += 1
            summary[test.status] = summary.get(test.status, 0) + 1
            scenario_entry["tests"].append({
                "guid": test.guid,
                "number": test.number,
                "name": test.name,
                "executor": test.executor,
                "supported_platforms": test.supported_platforms,
                "status": test.status,
                "return_code": test.return_code,
                "start_timestamp": test.start_timestamp,
                "end_timestamp": test.end_timestamp,
                "command": test.command,
                "output": test.output,
                "error": test.error,
            })

            labels = {
                "host": hostname,
                "scenario": scenario.spec.id,
                "technique": scenario.spec.technique,
                "test": f"{scenario.spec.technique}-{test.number}",
                "status": test.status,
                "executor": test.executor,
            }
            if test.supported_platforms:
                labels["platforms"] = ",".join(test.supported_platforms)
            prom_lines.append(render_metric("art_test_result", labels, STATUS_TO_VALUE.get(test.status, 4)))

        serialisable_results.append(scenario_entry)
        prom_scenario_lines.append(
            render_metric(
                "art_scenario_status",
                {
                    "host": hostname,
                    "scenario": scenario.spec.id,
                    "technique": scenario.spec.technique,
                    "status": scenario.status,
                },
                STATUS_TO_VALUE.get(scenario.status, 4),
            )
        )

    document = {
        "host": hostname,
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "mode": mode,
        "atomics_path": str(repo_path),
        "summary": summary,
        "scenarios": serialisable_results,
    }

    history_path = history_dir / f"{timestamp}.json"
    logger.info("Writing results to %s", history_path)
    with history_path.open("w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2)

    latest_path = output_dir / "latest.json"
    with latest_path.open("w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2)

    prom_path = prom_dir / "art_results.prom"
    logger.info("Writing Prometheus metrics to %s", prom_path)
    with prom_path.open("w", encoding="utf-8") as handle:
        handle.write("\n".join(prom_lines + prom_scenario_lines) + "\n")

    latest_prom = output_dir / "latest.prom"
    with latest_prom.open("w", encoding="utf-8") as handle:
        handle.write("\n".join(prom_lines + prom_scenario_lines) + "\n")

    logger.info("Results written successfully")
    return history_path


def _escape_label_value(value: str) -> str:
    """Return a Prometheus-safe label value."""

    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def render_metric(name: str, labels: Dict[str, str], value: int) -> str:
    encoded_labels = ",".join(
        f"{key}=\"{_escape_label_value(val)}\"" for key, val in sorted(labels.items())
    )
    return f"{name}{{{encoded_labels}}} {value}"


def main() -> None:
    args = parse_args()
    
    # Set log level from args if available
    if hasattr(args, 'verbose') and args.verbose:
        logger.setLevel(logging.DEBUG)
    
    logger.info("Starting Atomic Red Team execution (mode: %s, dry_run: %s)", 
                args.mode, args.dry_run)
    
    try:
        scenarios = load_scenarios(args)
        operator = AtomicOperator()
        repo_path = ensure_repo(operator, args)
        hostname = socket.gethostname()
        output_dir = Path(args.output).expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Output directory: %s", output_dir)

        results: List[ScenarioResult] = []
        for scenario in scenarios:
            try:
                results.append(
                    run_scenario(
                        operator=operator,
                        repo_path=repo_path,
                        scenario=scenario,
                        mode=args.mode,
                        timeout=args.timeout,
                        dry_run=args.dry_run,
                    )
                )
            except Exception as exc:
                logger.error("Failed to run scenario %s: %s", scenario.id, exc)
                raise

        history_path = write_outputs(
            output_dir=output_dir,
            hostname=hostname,
            mode=args.mode,
            repo_path=repo_path,
            scenario_results=results,
        )

        logger.info("✓ Atomic Red Team execution completed successfully")
        print(f"Wrote Atomic Red Team results to {history_path}")
    
    except Exception as exc:
        logger.error("Fatal error: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
