from __future__ import annotations

import pandas as pd
import pytest

from src.analytics_validation import (
    _python_metrics,
    compare_python_and_sqlite,
    validate_star_schema_relationships,
)
from src.sql_analytics import initialize_sqlite_database


def fixture_tables():
    fact_df = pd.DataFrame(
        [
            {"Order_Item_ID": "I1", "Order_ID": "O1", "Product_ID": "P1", "Order_Date": "2024-01-02", "Order_Status_Group": "Delivered", "Quantity": 2, "Net_Sales": 100.0},
            {"Order_Item_ID": "I2", "Order_ID": "O1", "Product_ID": "P2", "Order_Date": "2024-01-03", "Order_Status_Group": "Shipped", "Quantity": 1, "Net_Sales": 50.0},
            {"Order_Item_ID": "I3", "Order_ID": "O2", "Product_ID": "P1", "Order_Date": "2024-02-01", "Order_Status_Group": "Shipped", "Quantity": 3, "Net_Sales": 60.0},
            {"Order_Item_ID": "I4", "Order_ID": "O3", "Product_ID": "P2", "Order_Date": "2024-02-12", "Order_Status_Group": "Cancelled", "Quantity": 5, "Net_Sales": 0.0},
            {"Order_Item_ID": "I5", "Order_ID": None, "Product_ID": "P3", "Order_Date": None, "Order_Status_Group": "Pending", "Quantity": 9, "Net_Sales": 5.0},
        ]
    )
    product_df = pd.DataFrame(
        [
            {"Product_ID": "P1", "Category": "A"},
            {"Product_ID": "P2", "Category": "B"},
        ]
    )
    return fact_df, product_df


def test_python_sqlite_comparison_covers_required_metrics(tmp_path):
    fact_df, product_df = fixture_tables()
    db_path = tmp_path / "comparison.db"
    initialize_sqlite_database(db_path, fact_df=fact_df, product_df=product_df)

    comparison = compare_python_and_sqlite(fact_df, product_df, db_path)

    assert not comparison.empty
    assert set(comparison["status"]) == {"PASS"}
    values = comparison.set_index("metric_name")
    assert values.loc["total_sales", "python_value"] == 215.0
    assert values.loc["distinct_orders", "python_value"] == 3
    assert values.loc["units_sold", "python_value"] == 6.0
    assert values.loc["average_order_value", "python_value"] == 70.0
    assert values.loc["monthly_sales:2024-01", "python_value"] == 150.0
    assert values.loc["category_sales:A", "python_value"] == 160.0
    assert values.loc["product_sales:P2", "python_value"] == 50.0
    assert values.loc["units_sold", "python_value"] != 15.0


def test_python_sqlite_comparison_reports_discrepancies(tmp_path):
    fact_df, product_df = fixture_tables()
    different_data = fact_df.iloc[:1].copy()
    db_path = tmp_path / "discrepancy.db"
    initialize_sqlite_database(db_path, fact_df=different_data, product_df=product_df)

    comparison = compare_python_and_sqlite(fact_df, product_df, db_path)

    assert (comparison["status"] == "FAIL").any()
    assert comparison.loc[comparison["metric_name"] == "total_sales", "difference"].notna().all()
    assert comparison.loc[comparison["difference"].isna(), "status"].eq("FAIL").all()


def test_empty_input_compares_as_zero_metrics(tmp_path):
    fact_df, product_df = fixture_tables()
    db_path = tmp_path / "empty.db"
    initialize_sqlite_database(
        db_path,
        fact_df=fact_df.iloc[:0],
        product_df=product_df.iloc[:0],
    )

    comparison = compare_python_and_sqlite(fact_df.iloc[:0], product_df.iloc[:0], db_path)

    assert (comparison["status"] == "PASS").all()
    assert comparison.loc[comparison["metric_name"] == "total_sales", "python_value"].iloc[0] == 0.0


def test_star_schema_validation_accepts_many_to_one_foreign_keys_and_detects_orphans():
    fact_df, product_df = fixture_tables()
    fact_df["Order_Date"] = ["2024-01-02", "2024-01-03", "2024-02-01", "2024-02-12", "2024-02-13"]
    product_df.loc[len(product_df)] = ["P3", None]
    customer_df = pd.DataFrame({"Customer_ID": ["C1", "C2", "C3"]})
    date_df = pd.DataFrame({"Date_ISO": ["2024-01-02", "2024-01-03", "2024-02-01", "2024-02-12", "2024-02-13"]})
    fact_df["Customer_ID"] = ["C1", "C1", "C2", "C3", "C3"]
    report = validate_star_schema_relationships(fact_df, customer_df, product_df, date_df)
    assert (report["status"] == "PASS").all()

    fact_df.loc[0, "Product_ID"] = "NO-DIMENSION"
    report = validate_star_schema_relationships(fact_df, customer_df, product_df, date_df)
    row = report.loc[report["relationship"].str.contains("Product_ID ->")].iloc[0]
    assert row["unmatched_fact_keys"] == 1
    assert row["status"] == "FAIL"


def test_python_metrics_validates_required_columns():
    fact_df, product_df = fixture_tables()
    with pytest.raises(ValueError, match="Fact table is missing required columns"):
        _python_metrics(fact_df.drop(columns=["Net_Sales"]), product_df)

    with pytest.raises(ValueError, match="Product dimension is missing required columns"):
        _python_metrics(fact_df, product_df.drop(columns=["Category"]))


def test_star_schema_validation_detects_duplicate_dimension_keys():
    fact_df, product_df = fixture_tables()
    fact_df["Order_Date"] = ["2024-01-02", "2024-01-03", "2024-02-01", "2024-02-12", "2024-02-13"]
    fact_df["Customer_ID"] = ["C1", "C1", "C2", "C2", "C2"]
    # Duplicate customer key
    customer_df = pd.DataFrame({"Customer_ID": ["C1", "C2", "C2"]})
    date_df = pd.DataFrame({"Date_ISO": ["2024-01-02", "2024-01-03", "2024-02-01", "2024-02-12", "2024-02-13"]})
    report = validate_star_schema_relationships(fact_df, customer_df, product_df, date_df)
    cust_row = report.loc[report["relationship"].str.contains("Customer_ID ->")].iloc[0]
    assert cust_row["duplicate_dimension_keys"] == 1
    assert cust_row["status"] == "FAIL"


def test_python_sqlite_comparison_with_null_and_mixed_sales_statuses(tmp_path):
    fact_df = pd.DataFrame(
        [
            {"Order_Item_ID": "I1", "Order_ID": "O1", "Product_ID": "P1", "Order_Date": "2024-03-01", "Order_Status_Group": "Delivered", "Quantity": 2, "Net_Sales": 100.0},
            {"Order_Item_ID": "I2", "Order_ID": "O2", "Product_ID": "P1", "Order_Date": "2024-03-02", "Order_Status_Group": "Returned", "Quantity": 1, "Net_Sales": 0.0},
            {"Order_Item_ID": "I3", "Order_ID": "O3", "Product_ID": "P2", "Order_Date": None, "Order_Status_Group": "Cancelled", "Quantity": None, "Net_Sales": None},
            {"Order_Item_ID": "I4", "Order_ID": None, "Product_ID": "P2", "Order_Date": "2024-03-03", "Order_Status_Group": "Shipped", "Quantity": 4, "Net_Sales": 80.0},
        ]
    )
    product_df = pd.DataFrame(
        [
            {"Product_ID": "P1", "Category": "Apparel"},
            {"Product_ID": "P2", "Category": "Footwear"},
        ]
    )
    db_path = tmp_path / "mixed_status.db"
    initialize_sqlite_database(db_path, fact_df=fact_df, product_df=product_df)

    comparison = compare_python_and_sqlite(fact_df, product_df, db_path)

    assert not comparison.empty
    assert (comparison["status"] == "PASS").all()
    values = comparison.set_index("metric_name")
    assert values.loc["total_sales", "python_value"] == 180.0
    assert values.loc["units_sold", "python_value"] == 6.0  # Delivered (2) + Shipped (4), Returned/Cancelled ignored
    assert values.loc["distinct_orders", "python_value"] == 3  # O1, O2, O3 (None dropped)

