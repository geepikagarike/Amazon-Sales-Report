from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

from src.project_paths import (
    DIM_CUSTOMERS_CSV,
    DIM_DATES_CSV,
    DIM_PRODUCTS_CSV,
    FACT_ORDERS_CSV,
    POWERBI_DIR,
    SQLITE_DB_PATH,
)
from src.sql_analytics import average_order_value, distinct_order_count, total_sales


def get_mongo_uri() -> str:
    return os.getenv("MONGO_URI", "mongodb://localhost:27017")


def get_db_name() -> str:
    return os.getenv("DB_NAME", "ecommerce_analytics_db")


COLLECTION_KEYS = {
    "orders": "order_item_id",
    "products": "product_id",
    "customers": "customer_id",
    "dates": "date_key",
}

POWERBI_REQUIRED_COLUMNS = {
    "orders": {
        "Order_Item_ID", "Order_ID", "Customer_ID", "Product_ID", "Order_Date", "Year",
        "Month_Name", "Quarter", "Order_Status", "Order_Status_Group", "Courier_Status",
        "Fulfilment_Method", "Fulfilled_By", "Sales_Channel", "Ship_Service_Level",
        "Quantity", "Unit_Price", "Gross_Amount", "Net_Sales", "COGS", "Gross_Profit",
        "Profit_Margin_Pct", "Is_B2B", "Ship_City", "Ship_State", "Region",
        "Ship_Postal_Code", "Is_New_Record",
    },
    "products": {
        "Product_ID", "Product_Name", "Category", "Size", "Unit_MSRP", "Unit_Cost",
        "Total_Units_Sold", "Gross_Revenue", "Net_Revenue",
    },
    "customers": {
        "Customer_ID", "Customer_Name", "Customer_Segment", "Is_B2B", "City", "State",
        "Region", "Postal_Code", "Total_Orders", "Total_Spend", "Gross_Spend",
        "First_Order_Date", "Last_Order_Date",
    },
    "dates": {
        "Full_Date", "Date_Key", "Date_ISO", "Year", "Quarter", "Month_Number",
        "Month_Name", "Year_Month", "Day_Of_Month", "Day_Of_Week", "Is_Weekend",
    },
}


def load_cleaned_tables() -> dict[str, pd.DataFrame]:
    files = {
        "orders": FACT_ORDERS_CSV,
        "products": DIM_PRODUCTS_CSV,
        "customers": DIM_CUSTOMERS_CSV,
        "dates": DIM_DATES_CSV,
    }
    loaded: dict[str, pd.DataFrame] = {}
    for name, path in files.items():
        csv_path = Path(path)
        if csv_path.exists():
            loaded[name] = pd.read_csv(csv_path)
        else:
            loaded[name] = pd.DataFrame()
    return loaded


def build_mongo_documents(collection_name: str, df: pd.DataFrame) -> list[dict[str, Any]]:
    if collection_name not in COLLECTION_KEYS:
        raise ValueError(f"Unsupported MongoDB collection: {collection_name}")
    if df.empty:
        return []

    column_maps = {
        "orders": {
            "Order_Item_ID": "order_item_id", "Order_ID": "order_id", "Customer_ID": "customer_id",
            "Product_ID": "product_id", "Order_Date": "order_date", "Year": "year",
            "Month_Name": "month_name", "Quarter": "quarter", "Order_Status": "order_status",
            "Order_Status_Group": "order_status_group", "Courier_Status": "courier_status",
            "Fulfilment_Method": "fulfilment_method", "Fulfilled_By": "fulfilled_by",
            "Sales_Channel": "sales_channel", "Ship_Service_Level": "ship_service_level",
            "Quantity": "quantity", "Unit_Price": "unit_price", "Gross_Amount": "gross_amount",
            "Net_Sales": "net_sales", "COGS": "cogs", "Gross_Profit": "gross_profit",
            "Profit_Margin_Pct": "profit_margin_pct", "Is_B2B": "is_b2b", "Ship_City": "ship_city",
            "Ship_State": "ship_state", "Region": "region", "Ship_Postal_Code": "ship_postal_code",
            "Is_New_Record": "is_new_record",
        },
        "products": {
            "Product_ID": "product_id", "Product_Name": "product_name", "Category": "category",
            "Size": "size", "Unit_MSRP": "unit_msrp", "Unit_Cost": "unit_cost",
            "Total_Units_Sold": "total_units_sold", "Gross_Revenue": "gross_revenue",
            "Net_Revenue": "net_revenue",
        },
        "customers": {
            "Customer_ID": "customer_id", "Customer_Name": "customer_name",
            "Customer_Segment": "customer_segment", "Is_B2B": "is_b2b", "City": "city",
            "State": "state", "Region": "region", "Postal_Code": "postal_code",
            "Total_Orders": "total_orders", "Total_Spend": "total_spend",
            "Gross_Spend": "gross_spend", "First_Order_Date": "first_order_date",
            "Last_Order_Date": "last_order_date",
        },
        "dates": {
            "Date_Key": "date_key", "Full_Date": "full_date", "Date_ISO": "date_iso",
            "Year": "year", "Quarter": "quarter", "Month_Number": "month_number",
            "Month_Name": "month_name", "Year_Month": "year_month",
            "Day_Of_Month": "day_of_month", "Day_Of_Week": "day_of_week",
            "Is_Weekend": "is_weekend",
        },
    }
    normalized = df.rename(columns=column_maps[collection_name]).copy()
    numeric_fields = {
        "orders": {
            "year": "integer", "quantity": "integer", "ship_postal_code": "integer",
            "unit_price": "number", "gross_amount": "number", "net_sales": "number",
            "cogs": "number", "gross_profit": "number", "profit_margin_pct": "number",
        },
        "products": {
            "unit_msrp": "number", "unit_cost": "number", "total_units_sold": "integer",
            "gross_revenue": "number", "net_revenue": "number",
        },
        "customers": {
            "postal_code": "integer", "total_orders": "integer", "total_spend": "number",
            "gross_spend": "number",
        },
        "dates": {
            "date_key": "integer", "year": "integer", "month_number": "integer",
            "day_of_month": "integer",
        },
    }[collection_name]
    for column, kind in numeric_fields.items():
        if column in normalized.columns:
            values = pd.to_numeric(normalized[column], errors="coerce")
            normalized[column] = values.map(
                lambda value: None if pd.isna(value) else int(value) if kind == "integer" else float(value)
            )

    boolean_fields = {
        "orders": ("is_b2b", "is_new_record"),
        "customers": ("is_b2b",),
        "dates": ("is_weekend",),
        "products": (),
    }[collection_name]
    for column in boolean_fields:
        if column in normalized.columns:
            def to_bool(value: Any) -> bool | None:
                if pd.isna(value):
                    return None
                if isinstance(value, str):
                    if value.strip().lower() in {"true", "1"}:
                        return True
                    if value.strip().lower() in {"false", "0"}:
                        return False
                if value in (True, 1):
                    return True
                if value in (False, 0):
                    return False
                raise ValueError(f"Invalid boolean value for {column}: {value!r}")
            normalized[column] = normalized[column].map(to_bool)

    for column in ("order_date", "first_order_date", "last_order_date", "date_iso", "full_date"):
        if column in normalized.columns:
            parsed = pd.to_datetime(normalized[column], errors="coerce")
            normalized[column] = parsed.dt.strftime("%Y-%m-%d").where(parsed.notna(), None)
    return normalized.astype(object).where(pd.notna(normalized), None).to_dict(orient="records")


def upsert_mongo_tables(
    database: Any,
    tables: dict[str, pd.DataFrame] | None = None,
    batch_size: int = 1000,
    update_one_factory: Any = None,
) -> dict[str, int]:
    """Upsert source-keyed documents; never clears a MongoDB collection."""
    if batch_size < 1:
        raise ValueError("batch_size must be a positive integer")
    if update_one_factory is None:
        from pymongo import UpdateOne

        update_one_factory = UpdateOne
    source_tables = tables if tables is not None else load_cleaned_tables()
    index_definitions = {
        "orders": [
            ("order_item_id", True, "idx_order_item_id"),
            ("order_id", False, "idx_order_id"),
            ("product_id", False, "idx_product_id"),
            ("order_date", False, "idx_order_date"),
        ],
        "products": [("product_id", True, "idx_prod_id_pk")],
        "customers": [("customer_id", True, "idx_cust_id_pk")],
        "dates": [("date_key", True, "idx_date_key_pk")],
    }
    imported: dict[str, int] = {}
    for collection_name, key_field in COLLECTION_KEYS.items():
        frame = source_tables.get(collection_name, pd.DataFrame())
        documents = build_mongo_documents(collection_name, frame)
        operations = []
        for document in documents:
            key_value = document.get(key_field)
            if key_value is None or (isinstance(key_value, str) and not key_value.strip()):
                raise ValueError(f"{collection_name} row has no usable {key_field}")
            operations.append(
                update_one_factory({key_field: key_value}, {"$set": document}, upsert=True)
            )

        collection = database[collection_name]
        for index_field, unique, index_name in index_definitions[collection_name]:
            collection.create_index(index_field, unique=unique, name=index_name)
        for start in range(0, len(operations), batch_size):
            collection.bulk_write(operations[start : start + batch_size], ordered=False)
        imported[collection_name] = len(documents)
    return imported


def validate_sqlite_against_cleaned_data(
    db_path: str | Path | None = SQLITE_DB_PATH,
    fact_df: pd.DataFrame | None = None,
) -> dict[str, Any]:
    expected_total = 0.0
    expected_orders = 0
    expected_aov = 0.0

    if fact_df is not None:
        expected_total = float(fact_df["Net_Sales"].sum()) if "Net_Sales" in fact_df.columns else 0.0
        expected_orders = 0 if fact_df.empty else int(fact_df["Order_ID"].nunique(dropna=True))
        expected_aov = expected_total / expected_orders if expected_orders else 0.0
    else:
        source_csv = Path(FACT_ORDERS_CSV)
        if source_csv.exists():
            source_df = pd.read_csv(source_csv)
            expected_total = float(source_df["Net_Sales"].sum()) if "Net_Sales" in source_df.columns else 0.0
            expected_orders = 0 if source_df.empty else int(source_df["Order_ID"].nunique(dropna=True))
            expected_aov = expected_total / expected_orders if expected_orders else 0.0
        else:
            with sqlite3.connect(db_path) as conn:
                expected_total = float(conn.execute("SELECT COALESCE(SUM(Net_Sales), 0) FROM fact_orders").fetchone()[0])
                expected_orders = int(conn.execute("SELECT COUNT(DISTINCT Order_ID) FROM fact_orders WHERE Order_ID IS NOT NULL").fetchone()[0])
                expected_aov = float(conn.execute("SELECT COALESCE(AVG(order_net_value), 0) FROM (SELECT Order_ID, SUM(Net_Sales) AS order_net_value FROM fact_orders GROUP BY Order_ID)").fetchone()[0])

    sqlite_total = total_sales(db_path)
    sqlite_orders = distinct_order_count(db_path)
    sqlite_aov = average_order_value(db_path)
    return {
        "expected_total_sales": expected_total,
        "expected_distinct_orders": int(expected_orders),
        "expected_average_order_value": expected_aov,
        "sqlite_total_sales": sqlite_total,
        "sqlite_distinct_orders": sqlite_orders,
        "sqlite_average_order_value": sqlite_aov,
        "total_sales_match": abs(expected_total - sqlite_total) < 1e-9,
        "order_count_match": int(expected_orders) == sqlite_orders,
        "aov_match": abs(expected_aov - sqlite_aov) < 1e-9,
    }


def prepare_powerbi_exports(
    output_dir: str | Path | None = None,
    source_files: dict[str, str | Path] | None = None,
) -> dict[str, Path]:
    target_dir = Path(output_dir) if output_dir is not None else POWERBI_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    mapping = {
        "orders": FACT_ORDERS_CSV,
        "products": DIM_PRODUCTS_CSV,
        "customers": DIM_CUSTOMERS_CSV,
        "dates": DIM_DATES_CSV,
    }
    if source_files is not None:
        mapping = source_files
    missing_tables = set(POWERBI_REQUIRED_COLUMNS) - set(mapping)
    if missing_tables:
        raise ValueError(f"Power BI exports are missing source tables: {', '.join(sorted(missing_tables))}")
    outputs: dict[str, Path] = {}
    for name, source_path in mapping.items():
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"Power BI source table {name!r} was not found: {source}")
        df = pd.read_csv(source)
        missing_columns = POWERBI_REQUIRED_COLUMNS[name] - set(df.columns)
        if missing_columns:
            raise ValueError(
                f"Power BI source table {name!r} is missing columns: "
                f"{', '.join(sorted(missing_columns))}"
            )
        destination = target_dir / f"{name}.csv"
        df.to_csv(destination, index=False)
        outputs[name] = destination
    return outputs
