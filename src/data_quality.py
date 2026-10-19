from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def build_quality_report(df: pd.DataFrame, phase_name: str = "cleaned") -> dict[str, Any]:
    """Return a compact quality summary suitable for auditing and validation."""
    required_fields = {"Order_ID", "Order_Date", "Quantity", "Gross_Amount", "Category"}
    missing_required = sorted(required_fields - set(df.columns))

    report = {
        "phase": phase_name,
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "duplicate_rows": int(df.duplicated().sum()),
        "null_rows": int(df.isna().all(axis=1).sum()),
        "missing_required_fields": missing_required,
        "missing_values": {
            column: int(value)
            for column, value in df.isna().sum().items()
            if value > 0
        },
    }

    q_series = df["Quantity"] if "Quantity" in df.columns else pd.Series([], dtype="float64")
    amount_series = df["Gross_Amount"] if "Gross_Amount" in df.columns else pd.Series([], dtype="float64")
    report["invalid_quantity_rows"] = int((q_series.fillna(0) < 0).sum())
    report["invalid_amount_rows"] = int((amount_series.fillna(0) < 0).sum())
    report["negative_net_sales_rows"] = int((df["Net_Sales"].fillna(0) < 0).sum()) if "Net_Sales" in df.columns else 0
    report["negative_profit_rows"] = int((df["Gross_Profit"].fillna(0) < 0).sum()) if "Gross_Profit" in df.columns else 0

    return report


def export_quality_report(report: dict[str, Any], output_path: str | Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return output_path


def validate_retail_dataset(df: pd.DataFrame) -> tuple[bool, dict[str, Any]]:
    """Return a boolean validation result and a quality summary."""
    report = build_quality_report(df, phase_name="validation")
    errors = []

    if report["missing_required_fields"]:
        errors.append(f"Missing required columns: {report['missing_required_fields']}")
    if report["invalid_quantity_rows"] > 0:
        errors.append(f"Negative or invalid quantities detected: {report['invalid_quantity_rows']}")
    if report["invalid_amount_rows"] > 0:
        errors.append(f"Negative or invalid gross amounts detected: {report['invalid_amount_rows']}")

    is_valid = not errors
    return is_valid, {"report": report, "errors": errors}
