import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "process_pipeline.py"
SPEC = importlib.util.spec_from_file_location("process_pipeline", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

from src.data_quality import build_quality_report, validate_retail_dataset


def test_quality_report_tracks_core_metrics():
    df, _ = MODULE.load_and_clean_data()

    report = build_quality_report(df)

    assert report["rows"] > 120_000
    assert "missing_values" in report
    assert "invalid_quantity_rows" in report
    assert "negative_profit_rows" in report


def test_validation_passes_for_cleaned_dataset():
    df, _ = MODULE.load_and_clean_data()
    success, result = validate_retail_dataset(df)

    assert success is True
    assert result["report"]["rows"] == len(df)
