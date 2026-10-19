from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

from src.project_paths import (
    CLEANED_DIR,
    DIM_CUSTOMERS_CSV,
    DIM_DATES_CSV,
    DIM_PRODUCTS_CSV,
    FACT_ORDERS_CSV,
    SQLITE_DB_PATH,
)
from src.sql_analytics import initialize_from_project_files

SALES_STATUSES = ("Delivered", "Shipped")
DEFAULT_TOLERANCES = {
    "currency": 0.01,
    "count": 0.0,
}


def _number_sum(series: pd.Series) -> float:
    values = pd.to_numeric(series, errors="coerce")
    return float(values.sum(min_count=1)) if values.notna().any() else 0.0


def _normalize_grouped_values(values: dict[Any, Any]) -> dict[Any, Any]:
    normalized: dict[Any, Any] = {}
    for key, value in values.items():
        if pd.isna(key):
            key = None
        if hasattr(key, "item"):
            key = key.item()
        normalized[key] = None if pd.isna(value) else float(value)
    return normalized


def _python_metrics(fact_df: pd.DataFrame, product_df: pd.DataFrame) -> dict[str, Any]:
    required = {"Order_ID", "Net_Sales", "Quantity", "Order_Status_Group", "Order_Date", "Product_ID"}
    missing = required - set(fact_df.columns)
    if missing:
        raise ValueError(f"Fact table is missing required columns: {', '.join(sorted(missing))}")
    missing_product = {"Product_ID", "Category"} - set(product_df.columns)
    if missing_product:
        raise ValueError(
            f"Product dimension is missing required columns: {', '.join(sorted(missing_product))}"
        )

    fact = fact_df.copy()
    fact["Net_Sales"] = pd.to_numeric(fact["Net_Sales"], errors="coerce")
    fact["Quantity"] = pd.to_numeric(fact["Quantity"], errors="coerce")
    fact["Order_Date"] = pd.to_datetime(fact["Order_Date"], errors="coerce")
    eligible = fact["Order_Status_Group"].isin(SALES_STATUSES)

    total_sales = _number_sum(fact["Net_Sales"])
    order_count = int(fact["Order_ID"].nunique(dropna=True))
    units_sold = _number_sum(fact.loc[eligible, "Quantity"])
    aov_by_order = (
        fact.loc[fact["Order_ID"].notna()]
        .groupby("Order_ID")["Net_Sales"]
        .sum(min_count=1)
        .dropna()
    )
    aov = float(aov_by_order.mean()) if not aov_by_order.empty else 0.0

    valid_dates = fact["Order_Date"].notna()
    monthly = _normalize_grouped_values(
        (
        fact.loc[valid_dates]
        .assign(Month=fact.loc[valid_dates, "Order_Date"].dt.strftime("%Y-%m"))
        .groupby("Month", dropna=False)["Net_Sales"]
        .sum(min_count=1)
        .to_dict()
        )
    )

    product_cols = ["Product_ID", "Category"]
    product_lookup = product_df.loc[:, product_cols].drop_duplicates("Product_ID")
    fact = fact.merge(product_lookup, on="Product_ID", how="left")

    category_sales = _normalize_grouped_values(
        fact.groupby("Category", dropna=False)["Net_Sales"].sum(min_count=1).to_dict()
    )
    product_sales = _normalize_grouped_values(
        fact.groupby("Product_ID", dropna=False)["Net_Sales"].sum(min_count=1).to_dict()
    )

    return {
        "total_sales": total_sales,
        "distinct_orders": order_count,
        "units_sold": units_sold,
        "average_order_value": aov,
        "monthly_sales": monthly,
        "category_sales": category_sales,
        "product_sales": product_sales,
    }


def _sqlite_metrics(db_path: str | Path) -> dict[str, Any]:
    with sqlite3.connect(str(db_path)) as conn:
        total_sales = float(
            conn.execute("SELECT COALESCE(SUM(Net_Sales), 0.0) FROM fact_orders").fetchone()[0]
        )
        distinct_orders = int(
            conn.execute(
                "SELECT COUNT(DISTINCT Order_ID) FROM fact_orders WHERE Order_ID IS NOT NULL"
            ).fetchone()[0]
        )
        units_sold = float(
            conn.execute(
                "SELECT COALESCE(SUM(Quantity), 0.0) FROM fact_orders "
                "WHERE Order_Status_Group IN (?, ?)",
                SALES_STATUSES,
            ).fetchone()[0]
        )
        average_order_value = float(
            conn.execute(
                "SELECT COALESCE(AVG(order_net_value), 0.0) FROM ("
                "SELECT Order_ID, SUM(Net_Sales) AS order_net_value FROM fact_orders "
                "WHERE Order_ID IS NOT NULL GROUP BY Order_ID)"
            ).fetchone()[0]
        )
        monthly_sales = dict(
            conn.execute(
                "SELECT strftime('%Y-%m', Order_Date) AS month, SUM(Net_Sales) "
                "FROM fact_orders WHERE strftime('%Y-%m', Order_Date) IS NOT NULL "
                "GROUP BY strftime('%Y-%m', Order_Date)"
            ).fetchall()
        )
        category_sales = dict(
            conn.execute(
                "SELECT p.Category, SUM(f.Net_Sales) FROM fact_orders f "
                "LEFT JOIN dim_products p ON p.Product_ID = f.Product_ID "
                "GROUP BY p.Category"
            ).fetchall()
        )
        product_sales = dict(
            conn.execute(
                "SELECT Product_ID, SUM(Net_Sales) FROM fact_orders GROUP BY Product_ID"
            ).fetchall()
        )

    return {
        "total_sales": total_sales,
        "distinct_orders": distinct_orders,
        "units_sold": units_sold,
        "average_order_value": average_order_value,
        "monthly_sales": monthly_sales,
        "category_sales": category_sales,
        "product_sales": product_sales,
    }


def compare_python_and_sqlite(
    fact_df: pd.DataFrame,
    product_df: pd.DataFrame,
    db_path: str | Path,
    tolerances: dict[str, float] | None = None,
) -> pd.DataFrame:
    """Compare independently aggregated Python and SQLite metrics on the same input."""
    tolerance_by_type = {**DEFAULT_TOLERANCES, **(tolerances or {})}
    python_values = _python_metrics(fact_df, product_df)
    sqlite_values = _sqlite_metrics(db_path)
    comparison_rows: list[dict[str, Any]] = []

    def add_row(metric_name: str, python_value: Any, sqlite_value: Any, tolerance: float) -> None:
        if python_value is None or sqlite_value is None:
            difference = None
            passed = python_value is sqlite_value
        else:
            difference = float(python_value) - float(sqlite_value)
            passed = abs(difference) <= tolerance
        comparison_rows.append(
            {
                "metric_name": metric_name,
                "python_value": python_value,
                "sqlite_value": sqlite_value,
                "difference": difference,
                "tolerance": tolerance,
                "status": "PASS" if passed else "FAIL",
            }
        )

    for metric in ("total_sales", "distinct_orders", "units_sold", "average_order_value"):
        tolerance = tolerance_by_type["count"] if metric == "distinct_orders" else tolerance_by_type["currency"]
        add_row(metric, python_values[metric], sqlite_values[metric], tolerance)

    for metric in ("monthly_sales", "category_sales", "product_sales"):
        python_grouped = python_values[metric]
        sqlite_grouped = sqlite_values[metric]
        for key in sorted(set(python_grouped) | set(sqlite_grouped), key=lambda value: str(value)):
            add_row(
                f"{metric}:{key}",
                python_grouped.get(key),
                sqlite_grouped.get(key),
                tolerance_by_type["currency"],
            )
    return pd.DataFrame(
        comparison_rows,
        columns=["metric_name", "python_value", "sqlite_value", "difference", "tolerance", "status"],
    )


def validate_star_schema_relationships(
    fact_df: pd.DataFrame,
    customer_df: pd.DataFrame,
    product_df: pd.DataFrame,
    date_df: pd.DataFrame,
) -> pd.DataFrame:
    relationships = [
        ("fact_orders.Order_Item_ID", fact_df, "Order_Item_ID", None, None, True),
        ("fact_orders.Customer_ID -> dim_customers.Customer_ID", fact_df, "Customer_ID", customer_df, "Customer_ID", False),
        ("fact_orders.Product_ID -> dim_products.Product_ID", fact_df, "Product_ID", product_df, "Product_ID", False),
        ("fact_orders.Order_Date -> dim_dates.Date_ISO", fact_df, "Order_Date", date_df, "Date_ISO", False),
    ]
    rows = []
    for name, fact, fact_key, dimension, dimension_key, unique_fact_key in relationships:
        fact_values = fact[fact_key]
        missing_fact_keys = int(fact_values.isna().sum())
        duplicate_fact_keys = int(fact_values.duplicated().sum()) if unique_fact_key else 0
        duplicate_dimension_keys = 0
        missing_dimension_keys = 0
        unmatched_fact_keys = 0
        if dimension is not None and dimension_key is not None:
            dimension_values = dimension[dimension_key]
            duplicate_dimension_keys = int(dimension_values.duplicated().sum())
            missing_dimension_keys = int(dimension_values.isna().sum())
            allowed_values = set(dimension_values.dropna().astype(str))
            unmatched_fact_keys = int(
                (fact_values.notna() & ~fact_values.astype(str).isin(allowed_values)).sum()
            )
        valid = (
            missing_fact_keys == 0
            and duplicate_fact_keys == 0
            and duplicate_dimension_keys == 0
            and missing_dimension_keys == 0
            and unmatched_fact_keys == 0
        )
        rows.append(
            {
                "relationship": name,
                "fact_rows": len(fact),
                "missing_fact_keys": missing_fact_keys,
                "duplicate_fact_keys": duplicate_fact_keys,
                "duplicate_dimension_keys": duplicate_dimension_keys,
                "missing_dimension_keys": missing_dimension_keys,
                "unmatched_fact_keys": unmatched_fact_keys,
                "status": "PASS" if valid else "FAIL",
            }
        )
    return pd.DataFrame(rows)


def validate_project_data(
    fact_path: str | Path = FACT_ORDERS_CSV,
    product_path: str | Path = DIM_PRODUCTS_CSV,
    db_path: str | Path = SQLITE_DB_PATH,
    report_path: str | Path | None = None,
) -> pd.DataFrame:
    fact_df = pd.read_csv(fact_path)
    product_df = pd.read_csv(product_path)
    comparison = compare_python_and_sqlite(fact_df, product_df, db_path)
    if report_path is not None:
        output = Path(report_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        comparison.to_csv(output, index=False)
    return comparison


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare Python and SQLite project KPIs.")
    parser.add_argument(
        "--report",
        type=Path,
        default=CLEANED_DIR.parent / "validation" / "python_sqlite_comparison.csv",
        help="CSV path for the detailed metric comparison report.",
    )
    args = parser.parse_args()

    db_path = initialize_from_project_files()
    report = validate_project_data(db_path=db_path, report_path=args.report)
    print(report.to_string(index=False))
    print(f"Comparison report written to: {args.report}")
    return 0 if not report.empty and (report["status"] == "PASS").all() else 1


if __name__ == "__main__":
    raise SystemExit(main())
