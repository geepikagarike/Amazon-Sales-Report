from __future__ import annotations

import pandas as pd
import pytest

from src.mongo_integration import (
    POWERBI_DIR,
    POWERBI_REQUIRED_COLUMNS,
    build_mongo_documents,
    prepare_powerbi_exports,
    upsert_mongo_tables,
    validate_sqlite_against_cleaned_data,
)
from src.sql_analytics import initialize_sqlite_database


def build_synthetic_data():
    fact_df = pd.DataFrame(
        [
            {
                "Order_Item_ID": "ITEM-1",
                "Order_ID": "ORD-001",
                "Customer_ID": "CUST-1",
                "Product_ID": "PROD-1",
                "Order_Date": "2024-01-10",
                "Year": 2024,
                "Month_Name": "January",
                "Quarter": "2024Q1",
                "Order_Status": "Shipped - Delivered to Buyer",
                "Order_Status_Group": "Delivered",
                "Courier_Status": "Shipped",
                "Fulfilment_Method": "Amazon",
                "Fulfilled_By": "Amazon FBA",
                "Sales_Channel": "Amazon.in",
                "Ship_Service_Level": "Standard",
                "Quantity": 2,
                "Unit_Price": 100.0,
                "Gross_Amount": 200.0,
                "Net_Sales": 200.0,
                "COGS": 130.0,
                "Gross_Profit": 70.0,
                "Profit_Margin_Pct": 35.0,
                "Is_B2B": False,
                "Ship_City": "Bengaluru",
                "Ship_State": "Karnataka",
                "Region": "South",
                "Ship_Postal_Code": 560001,
                "Is_New_Record": False,
            },
            {
                "Order_Item_ID": "ITEM-2",
                "Order_ID": "ORD-002",
                "Customer_ID": "CUST-2",
                "Product_ID": "PROD-2",
                "Order_Date": "2024-02-15",
                "Year": 2024,
                "Month_Name": "February",
                "Quarter": "2024Q1",
                "Order_Status": "Cancelled",
                "Order_Status_Group": "Cancelled",
                "Courier_Status": "Cancelled",
                "Fulfilment_Method": "Merchant",
                "Fulfilled_By": "Merchant Easy Ship",
                "Sales_Channel": "Amazon.in",
                "Ship_Service_Level": "Standard",
                "Quantity": 1,
                "Unit_Price": 120.0,
                "Gross_Amount": 120.0,
                "Net_Sales": 0.0,
                "COGS": 0.0,
                "Gross_Profit": 0.0,
                "Profit_Margin_Pct": 0.0,
                "Is_B2B": False,
                "Ship_City": "Mumbai",
                "Ship_State": "Maharashtra",
                "Region": "West",
                "Ship_Postal_Code": 400001,
                "Is_New_Record": False,
            },
        ]
    )
    product_df = pd.DataFrame(
        [
            {"Product_ID": "PROD-1", "Product_Name": "Alpha Tee", "Category": "T-shirt", "Size": "M", "Unit_MSRP": 100.0, "Unit_Cost": 65.0, "Total_Units_Sold": 3, "Gross_Revenue": 200.0, "Net_Revenue": 200.0},
            {"Product_ID": "PROD-2", "Product_Name": "Beta Shirt", "Category": "Shirt", "Size": "L", "Unit_MSRP": 120.0, "Unit_Cost": 80.0, "Total_Units_Sold": 1, "Gross_Revenue": 120.0, "Net_Revenue": 0.0},
        ]
    )
    customer_df = pd.DataFrame(
        [
            {"Customer_ID": "CUST-1", "Customer_Name": "Customer One", "Customer_Segment": "Loyal Gold", "Is_B2B": False, "City": "Bengaluru", "State": "Karnataka", "Region": "South", "Postal_Code": 560001, "Total_Orders": 1, "Total_Spend": 200.0, "Gross_Spend": 200.0, "First_Order_Date": "2024-01-10", "Last_Order_Date": "2024-01-10"},
            {"Customer_ID": "CUST-2", "Customer_Name": "Customer Two", "Customer_Segment": "Occasional Bronze", "Is_B2B": False, "City": "Mumbai", "State": "Maharashtra", "Region": "West", "Postal_Code": 400001, "Total_Orders": 1, "Total_Spend": 0.0, "Gross_Spend": 120.0, "First_Order_Date": "2024-02-15", "Last_Order_Date": "2024-02-15"},
        ]
    )
    date_df = pd.DataFrame(
        [
            {"Date_Key": 20240110, "Full_Date": "2024-01-10", "Date_ISO": "2024-01-10", "Year": 2024, "Quarter": "2024Q1", "Month_Number": 1, "Month_Name": "January", "Year_Month": "2024-01", "Day_Of_Month": 10, "Day_Of_Week": "Wednesday", "Is_Weekend": 0},
            {"Date_Key": 20240215, "Full_Date": "2024-02-15", "Date_ISO": "2024-02-15", "Year": 2024, "Quarter": "2024Q1", "Month_Number": 2, "Month_Name": "February", "Year_Month": "2024-02", "Day_Of_Month": 15, "Day_Of_Week": "Thursday", "Is_Weekend": 0},
        ]
    )
    return fact_df, product_df, customer_df, date_df


def test_build_mongo_documents_uses_mongo_field_names(tmp_path):
    fact_df, product_df, customer_df, date_df = build_synthetic_data()
    orders_docs = build_mongo_documents("orders", fact_df)
    products_docs = build_mongo_documents("products", product_df)
    customers_docs = build_mongo_documents("customers", customer_df)
    dates_docs = build_mongo_documents("dates", date_df)

    assert orders_docs[0]["order_id"] == "ORD-001"
    assert orders_docs[0]["order_status_group"] == "Delivered"
    assert products_docs[0]["product_id"] == "PROD-1"
    assert customers_docs[0]["customer_segment"] == "Loyal Gold"
    assert dates_docs[0]["date_iso"] == "2024-01-10"


def test_prepare_powerbi_exports_creates_files(tmp_path):
    fact_df, product_df, customer_df, date_df = build_synthetic_data()
    target = tmp_path / "powerbi_exports"
    source_files = {}
    for name, frame in {
        "orders": fact_df,
        "products": product_df,
        "customers": customer_df,
        "dates": date_df,
    }.items():
        source = tmp_path / f"{name}.csv"
        frame.to_csv(source, index=False)
        source_files[name] = source

    exports = prepare_powerbi_exports(target, source_files)

    assert set(exports) == {"orders", "products", "customers", "dates"}
    assert all(path.exists() for path in exports.values())
    assert "Order_ID" in pd.read_csv(exports["orders"]).columns


def test_powerbi_export_rejects_missing_sources_and_missing_columns(tmp_path):
    fact_df, product_df, customer_df, date_df = build_synthetic_data()
    source_files = {}
    for name, frame in {
        "orders": fact_df,
        "products": product_df,
        "customers": customer_df,
        "dates": date_df,
    }.items():
        source = tmp_path / f"{name}.csv"
        frame.to_csv(source, index=False)
        source_files[name] = source

    del source_files["dates"]
    try:
        prepare_powerbi_exports(tmp_path / "out", source_files)
    except ValueError as error:
        assert "missing source tables" in str(error)
    else:
        raise AssertionError("Missing table mapping must not be silently skipped.")

    source_files["dates"] = source_files["orders"]
    try:
        prepare_powerbi_exports(tmp_path / "out", source_files)
    except ValueError as error:
        assert "missing columns" in str(error)
    else:
        raise AssertionError("A table with the wrong schema must be rejected.")


def test_powerbi_export_supports_empty_tables_with_headers(tmp_path):
    fact_df, product_df, customer_df, date_df = build_synthetic_data()
    source_files = {}
    for name, frame in {
        "orders": fact_df.iloc[0:0],
        "products": product_df.iloc[0:0],
        "customers": customer_df.iloc[0:0],
        "dates": date_df.iloc[0:0],
    }.items():
        source = tmp_path / f"{name}.csv"
        frame.to_csv(source, index=False)
        source_files[name] = source

    exports = prepare_powerbi_exports(tmp_path / "empty_exports", source_files)
    assert all(pd.read_csv(path).empty for path in exports.values())


def test_validate_sqlite_against_cleaned_data_matches_sources(tmp_path):
    fact_df, product_df, customer_df, date_df = build_synthetic_data()
    db_path = tmp_path / "sqlite_validation.db"
    initialize_sqlite_database(db_path, fact_df, product_df, customer_df, date_df)

    validation = validate_sqlite_against_cleaned_data(db_path, fact_df)

    assert validation["total_sales_match"] is True
    assert validation["order_count_match"] is True
    assert validation["aov_match"] is True
    assert validation["expected_total_sales"] == 200.0


def test_mongo_import_uses_upserts_without_deleting_existing_records():
    fact_df, product_df, customer_df, date_df = build_synthetic_data()

    class FakeCollection:
        def __init__(self):
            self.writes = []
            self.indexes = []

        def create_index(self, field, unique, name):
            self.indexes.append((field, unique, name))

        def bulk_write(self, operations, ordered):
            assert ordered is False
            self.writes.extend(operations)

    class FakeDatabase:
        def __init__(self):
            self.collections = {}

        def __getitem__(self, name):
            return self.collections.setdefault(name, FakeCollection())

    database = FakeDatabase()
    tables = {
        "orders": fact_df,
        "products": product_df,
        "customers": customer_df,
        "dates": date_df,
    }

    def fake_update_one(query, update, upsert):
        return {"query": query, "update": update, "upsert": upsert}

    first = upsert_mongo_tables(database, tables, batch_size=1, update_one_factory=fake_update_one)
    second = upsert_mongo_tables(database, tables, batch_size=1, update_one_factory=fake_update_one)

    assert first == second == {"orders": 2, "products": 2, "customers": 2, "dates": 2}
    order_ops = database["orders"].writes
    assert len(order_ops) == 4
    assert all(operation["upsert"] is True for operation in order_ops)
    assert all("order_item_id" in operation["query"] for operation in order_ops)
    assert ("order_item_id", True, "idx_order_item_id") in database["orders"].indexes


def test_build_mongo_documents_preserves_missing_amounts_and_rejects_unknown_collection():
    frame = pd.DataFrame([{"Order_Item_ID": "I1", "Net_Sales": None, "Order_Date": None}])
    document = build_mongo_documents("orders", frame)[0]
    assert document["net_sales"] is None
    assert document["order_date"] is None

    try:
        build_mongo_documents("unknown", frame)
    except ValueError as error:
        assert "Unsupported" in str(error)
    else:
        raise AssertionError("Unknown collections must be rejected.")


def test_build_mongo_documents_handles_boolean_variants_and_invalid_values():
    frame = pd.DataFrame([
        {"Customer_ID": "C1", "Is_B2B": "true"},
        {"Customer_ID": "C2", "Is_B2B": "False"},
        {"Customer_ID": "C3", "Is_B2B": 1},
        {"Customer_ID": "C4", "Is_B2B": 0},
        {"Customer_ID": "C5", "Is_B2B": None},
    ])
    docs = build_mongo_documents("customers", frame)
    assert docs[0]["is_b2b"] is True
    assert docs[1]["is_b2b"] is False
    assert docs[2]["is_b2b"] is True
    assert docs[3]["is_b2b"] is False
    assert docs[4]["is_b2b"] is None

    invalid_frame = pd.DataFrame([{"Customer_ID": "C6", "Is_B2B": "maybe"}])
    with pytest.raises(ValueError, match="Invalid boolean value"):
        build_mongo_documents("customers", invalid_frame)


def test_upsert_mongo_tables_validates_batch_size_and_handles_missing_keys():
    fact_df, product_df, customer_df, date_df = build_synthetic_data()
    tables = {
        "orders": fact_df,
        "products": product_df,
        "customers": customer_df,
        "dates": date_df,
    }

    class DummyDb:
        pass

    with pytest.raises(ValueError, match="batch_size must be a positive integer"):
        upsert_mongo_tables(DummyDb(), tables, batch_size=0)

    # Missing primary key in a row
    bad_orders = fact_df.copy()
    bad_orders.loc[0, "Order_Item_ID"] = "   "
    bad_tables = dict(tables)
    bad_tables["orders"] = bad_orders
    with pytest.raises(ValueError, match="has no usable order_item_id"):
        upsert_mongo_tables(DummyDb(), bad_tables, batch_size=10)


def test_actual_powerbi_exports_schema_integrity():
    if not POWERBI_DIR.exists():
        pytest.skip("Power BI directory does not exist yet")

    for table_name, required_cols in POWERBI_REQUIRED_COLUMNS.items():
        file_path = POWERBI_DIR / f"{table_name}.csv"
        if not file_path.exists():
            pytest.skip(f"Power BI export {file_path.name} not found")
        df = pd.read_csv(file_path)
        assert not df.empty, f"{file_path.name} should not be empty"
        missing = required_cols - set(df.columns)
        assert not missing, f"{file_path.name} is missing columns: {missing}"

        # Check dimension key uniqueness
        if table_name == "products":
            assert df["Product_ID"].duplicated().sum() == 0
        elif table_name == "customers":
            assert df["Customer_ID"].duplicated().sum() == 0
        elif table_name == "dates":
            assert df["Date_ISO"].duplicated().sum() == 0

