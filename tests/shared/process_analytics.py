"""Утилиты для расчёта и сохранения метрик процессов hardening."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict

from time_utils import TimeSequencer


_METRIC_FIELDS = (
    "cycle_time_hours",
    "review_rounds",
    "review_comments",
    "incident_frequency",
    "mttr_hours",
    "p95_latency_ms",
    "error_budget_consumed",
)


def _round_value(name: str, value: float) -> float:
    if name in {"review_rounds", "review_comments"}:
        return float(int(round(value)))
    if name in {"cycle_time_hours", "mttr_hours"}:
        return round(value, 2)
    if name in {"p95_latency_ms"}:
        return round(value, 1)
    return round(value, 3)


@dataclass
class ProcessMetricSnapshot:
    cycle_time_hours: float
    review_rounds: float
    review_comments: float
    incident_frequency: float
    mttr_hours: float
    p95_latency_ms: float
    error_budget_consumed: float

    def clamp(self) -> "ProcessMetricSnapshot":
        data = {}
        for field_name in _METRIC_FIELDS:
            value = getattr(self, field_name)
            data[field_name] = max(0.0, float(value))
        return ProcessMetricSnapshot(**data)


@dataclass
class ProcessMetricReport:
    function: str
    family: str
    context: str | None
    generated_at: str
    baseline: ProcessMetricSnapshot
    observed: ProcessMetricSnapshot
    delta: Dict[str, float]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "function": self.function,
            "family": self.family,
            "context": self.context,
            "generated_at": self.generated_at,
            "baseline": {k: _round_value(k, v) for k, v in asdict(self.baseline).items()},
            "observed": {k: _round_value(k, v) for k, v in asdict(self.observed).items()},
            "delta": {k: _round_value(k, v) for k, v in self.delta.items()},
        }


class ProcessAnalytics:
    """Читает baseline-метрики и формирует отчёты по функциям."""

    def __init__(self, baseline_path: Path, *, time_provider: TimeSequencer | None = None):
        self.baseline_path = baseline_path
        self._baseline = self._load_baseline(baseline_path)
        self._time = time_provider or TimeSequencer()

    @staticmethod
    def _load_baseline(path: Path) -> Dict[str, ProcessMetricSnapshot]:
        if not path.exists():
            raise FileNotFoundError(f"Не найден baseline метрик: {path}")
        raw = json.loads(path.read_text(encoding="utf-8"))
        baseline: Dict[str, ProcessMetricSnapshot] = {}
        for key, values in raw.items():
            snapshot = ProcessMetricSnapshot(**{field: float(values[field]) for field in _METRIC_FIELDS})
            baseline[key] = snapshot
        return baseline

    def baseline_snapshot(self, key: str) -> ProcessMetricSnapshot:
        if key not in self._baseline:
            raise KeyError(f"Baseline для функции {key!r} не найден")
        return self._baseline[key]

    def evaluate(
        self,
        key: str,
        observed: ProcessMetricSnapshot,
        output_dir: Path,
        *,
        family: str | None = None,
        context: str | None = None,
    ) -> ProcessMetricReport:
        baseline = self.baseline_snapshot(key)
        observed = observed.clamp()
        delta = {field: getattr(observed, field) - getattr(baseline, field) for field in _METRIC_FIELDS}
        report = ProcessMetricReport(
            function=key,
            family=family or key,
            context=context,
            generated_at=self._time.next_iso(),
            baseline=baseline,
            observed=observed,
            delta=delta,
        )
        payload = report.as_dict()
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "process-impact.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )
        (output_dir / "process-impact.md").write_text(self._render_markdown(payload), encoding="utf-8")
        return report

    @staticmethod
    def _render_markdown(payload: Dict[str, Any]) -> str:
        lines = [
            "# Аналитика процесса",
            "",
            f"Функция: {payload['family']} ({payload['function']})",
        ]
        if payload.get("context"):
            lines.append(f"Контекст: {payload['context']}")
        lines.extend(
            [
                f"Отчёт сформирован: {payload['generated_at']}",
                "",
                "| Метрика | Базовое | Факт | Δ |",
                "|---------|---------|------|---|",
            ]
        )
        for field in _METRIC_FIELDS:
            base_value = payload["baseline"][field]
            observed_value = payload["observed"][field]
            delta_value = payload["delta"][field]
            lines.append(
                f"| {field} | {base_value} | {observed_value} | {delta_value:+} |"
            )
        return "\n".join(lines) + "\n"


__all__ = [
    "ProcessAnalytics",
    "ProcessMetricReport",
    "ProcessMetricSnapshot",
]
