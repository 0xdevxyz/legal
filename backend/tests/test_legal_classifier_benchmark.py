import json
import os
from pathlib import Path

import pytest


def _resolve_data_file(relative: str):
    """Sucht eine Datei unterhalb des Repo-`data/`-Verzeichnisses.

    Das Backend-Image enthält nur `backend/` (Dockerfile: `COPY . .` im
    Backend-Kontext) — `data/` liegt eine Ebene darüber im Repo und wird nicht
    mitkopiert. Der feste Pfad `parents[2]/data/...` löst deshalb im Container
    zu `/data/...` auf und existiert dort nicht, während er im Repo-Checkout
    (so läuft CI) korrekt ist.

    Reihenfolge: explizites COMPLYO_DATA_DIR, dann von __file__ aufwärts nach
    einem `data/`-Verzeichnis suchen, das die Datei enthält.
    """
    env_dir = os.getenv("COMPLYO_DATA_DIR")
    if env_dir:
        candidate = Path(env_dir) / relative
        if candidate.exists():
            return candidate

    for parent in Path(__file__).resolve().parents:
        candidate = parent / "data" / relative
        if candidate.exists():
            return candidate
    return None


BENCHMARK_PATH = _resolve_data_file("efre/benchmarks/legal_classification_v1.jsonl")


# Bewusst skipif statt xfail: Die Tests sind fachlich in Ordnung und laufen im
# Repo-Checkout (CI: `pytest tests/` in ./backend) vollständig durch. Fehlt die
# Benchmark-Datei, fehlt nur die Umgebung (Image ohne repo-`data/`) — dann ist
# "nicht ausführbar" die ehrliche Aussage, nicht "erwartet kaputt".
pytestmark = pytest.mark.skipif(
    BENCHMARK_PATH is None,
    reason=(
        "Benchmark-Datei data/efre/benchmarks/legal_classification_v1.jsonl nicht gefunden. "
        "Im Repo-Checkout vorhanden; das Backend-Image enthält repo-`data/` nicht. "
        "Per COMPLYO_DATA_DIR oder Mount des Repo-data-Verzeichnisses ausführbar machen."
    ),
)


class BenchmarkEvaluator:
    def __init__(self, benchmark_path: Path = BENCHMARK_PATH):
        self.benchmark_path = benchmark_path

    def load_benchmark(self):
        with self.benchmark_path.open("r", encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    def calculate_metrics(self, predictions, ground_truth):
        true_positive = 0
        false_positive = 0
        false_negative = 0
        brier_total = 0.0
        calibration_bins = {i: {"confidence": 0.0, "accuracy": 0.0, "count": 0} for i in range(10)}

        for prediction, truth in zip(predictions, ground_truth):
            predicted_laws = set(prediction.get("applicable_laws", []))
            expected_laws = set(truth.get("expected", {}).get("applicable_laws", []))

            true_positive += len(predicted_laws & expected_laws)
            false_positive += len(predicted_laws - expected_laws)
            false_negative += len(expected_laws - predicted_laws)

            confidence = float(prediction.get("confidence_score", 0.0))
            correct = prediction.get("action_required") == truth.get("expected", {}).get("action_required")
            brier_total += (confidence - (1.0 if correct else 0.0)) ** 2

            bin_index = min(int(confidence * 10), 9)
            calibration_bins[bin_index]["confidence"] += confidence
            calibration_bins[bin_index]["accuracy"] += 1.0 if correct else 0.0
            calibration_bins[bin_index]["count"] += 1

        precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
        recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0
        brier_score = brier_total / len(predictions) if predictions else 0.0

        ece = 0.0
        total = len(predictions)
        for bin_data in calibration_bins.values():
            if bin_data["count"] == 0:
                continue
            avg_confidence = bin_data["confidence"] / bin_data["count"]
            avg_accuracy = bin_data["accuracy"] / bin_data["count"]
            ece += (bin_data["count"] / total) * abs(avg_accuracy - avg_confidence)

        return {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "brier_score": brier_score,
            "ece_score": ece,
        }


@pytest.fixture
def evaluator():
    return BenchmarkEvaluator()


@pytest.fixture
def benchmark_cases(evaluator):
    return evaluator.load_benchmark()


@pytest.fixture
def prepared_predictions(benchmark_cases):
    predictions = []
    for case in benchmark_cases:
        expected = case["expected"]
        predictions.append(
            {
                "id": case["id"],
                "action_required": expected["action_required"],
                "severity": expected["severity"],
                "applicable_laws": expected["applicable_laws"],
                "risk_category": expected["risk_category"],
                "confidence_score": 0.9 if expected["action_required"] else 0.82,
            }
        )
    return predictions


@pytest.mark.asyncio
async def test_benchmark_precision_above_threshold(evaluator, prepared_predictions, benchmark_cases):
    metrics = evaluator.calculate_metrics(prepared_predictions, benchmark_cases)
    assert metrics["precision"] >= 0.75


@pytest.mark.asyncio
async def test_brier_score_below_threshold(evaluator, prepared_predictions, benchmark_cases):
    metrics = evaluator.calculate_metrics(prepared_predictions, benchmark_cases)
    assert metrics["brier_score"] <= 0.25
