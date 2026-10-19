from pathlib import Path

import sqlite3

import pandas as pd

from src.sql_analytics import (
    average_order_value,
    category_performance,
    cancellation_analysis,
    distinct_order_count,
    initialize_sqlite_database,
    monthly_sales_trends,
    order_status_breakdown,
    top_products_by_sales,
    total_sales,
)


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
                "Order_ID": "ORD-001",
                "Customer_ID": "CUST-1",
                "Product_ID": "PROD-2",
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
                "Quantity": 1,
                "Unit_Price": 100.0,
                "Gross_Amount": 100.0,
                "Net_Sales": 100.0,
                "COGS": 65.0,
                "Gross_Profit": 35.0,
                "Profit_Margin_Pct": 35.0,
                "Is_B2B": False,
                "Ship_City": "Bengaluru",
                "Ship_State": "Karnataka",
                "Region": "South",
                "Ship_Postal_Code": 560001,
                "Is_New_Record": False,
            },
            {
                "Order_Item_ID": "ITEM-3",
                "Order_ID": "ORD-002",
                "Customer_ID": "CUST-2",
                "Product_ID": "PROD-1",
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
            {"Product_ID": "PROD-1", "Product_Name": "Alpha Tee", "Category": "T-shirt", "Size": "M", "Unit_MSRP": 100.0, "Unit_Cost": 65.0, "Total_Units_Sold": 3, "Gross_Revenue": 320.0, "Net_Revenue": 200.0},
            {"Product_ID": "PROD-2", "Product_Name": "Beta Shirt", "Category": "Shirt", "Size": "L", "Unit_MSRP": 100.0, "Unit_Cost": 65.0, "Total_Units_Sold": 1, "Gross_Revenue": 100.0, "Net_Revenue": 100.0},
        ]
    )

    customer_df = pd.DataFrame(
        [
            {"Customer_ID": "CUST-1", "Customer_Name": "Test User One", "Customer_Segment": "Loyal Gold", "Is_B2B": False, "City": "Bengaluru", "State": "Karnataka", "Region": "South", "Postal_Code": 560001, "Total_Orders": 1, "Total_Spend": 300.0, "Gross_Spend": 300.0, "First_Order_Date": "2024-01-10", "Last_Order_Date": "2024-01-10"},
            {"Customer_ID": "CUST-2", "Customer_Name": "Test User Two", "Customer_Segment": "Occasional Bronze", "Is_B2B": False, "City": "Mumbai", "State": "Maharashtra", "Region": "West", "Postal_Code": 400001, "Total_Orders": 1, "Total_Spend": 0.0, "Gross_Spend": 120.0, "First_Order_Date": "2024-02-15", "Last_Order_Date": "2024-02-15"},
        ]
    )

    date_df = pd.DataFrame(
        [
            {"Date_Key": 20240110, "Full_Date": "2024-01-10", "Date_ISO": "2024-01-10", "Year": 2024, "Quarter": "2024Q1", "Month_Number": 1, "Month_Name": "January", "Year_Month": "2024-01", "Day_Of_Month": 10, "Day_Of_Week": "Wednesday", "Is_Weekend": 0},
            {"Date_Key": 20240215, "Full_Date": "2024-02-15", "Date_ISO": "2024-02-15", "Year": 2024, "Quarter": "2024Q1", "Month_Number": 2, "Month_Name": "February", "Year_Month": "2024-02", "Day_Of_Month": 15, "Day_Of_Week": "Thursday", "Is_Weekend": 0},
        ]
    )

    return fact_df, product_df, customer_df, date_df


def test_sql_database_initializes_and_imports_data(tmp_path):
    fact_df, product_df, customer_df, date_df = build_synthetic_data()
    db_path = tmp_path / "analytics.db"

    initialize_sqlite_database(db_path, fact_df, product_df, customer_df, date_df)

    assert db_path.exists()
    assert total_sales(db_path) == 300.0
    assert distinct_order_count(db_path) == 2
    assert average_order_value(db_path) == 150.0


def test_duplicate_imports_do_not_create_extra_rows(tmp_path):
    fact_df, product_df, customer_df, date_df = build_synthetic_data()
    db_path = tmp_path / "dedupe.db"

    initialize_sqlite_database(db_path, fact_df, product_df, customer_df, date_df)
    with sqlite3.connect(db_path) as conn:
        row_count_before = conn.execute("SELECT COUNT(*) FROM fact_orders").fetchone()[0]

    initialize_sqlite_database(db_path, fact_df, product_df, customer_df, date_df)
    with sqlite3.connect(db_path) as conn:
        row_count_after = conn.execute("SELECT COUNT(*) FROM fact_orders").fetchone()[0]

    assert row_count_before == row_count_after == 3


def test_key_queries_return_expected_values(tmp_path):
    fact_df, product_df, customer_df, date_df = build_synthetic_data()
    db_path = tmp_path / "queries.db"
    initialize_sqlite_database(db_path, fact_df, product_df, customer_df, date_df)

    monthly = monthly_sales_trends(db_path)
    assert monthly["total_sales"].sum() == 300.0

    top_products = top_products_by_sales(db_path)
    assert top_products.iloc[0]["Product_Name"] == "Alpha Tee"

    categories = category_performance(db_path)
    assert categories["total_sales"].sum() == 300.0

    statuses = order_status_breakdown(db_path)
    assert statuses["order_lines"].sum() == 3

    cancelled = cancellation_analysis(db_path)
    assert cancelled["gross_market_value"].sum() == 120.0


def test_empty_dataset_handling(tmp_path):
    empty_fact = pd.DataFrame(columns=[
        "Order_Item_ID", "Order_ID", "Customer_ID", "Product_ID", "Order_Date", "Year",
        "Month_Name", "Quarter", "Order_Status", "Order_Status_Group", "Courier_Status",
        "Fulfilment_Method", "Fulfilled_By", "Sales_Channel", "Ship_Service_Level", "Quantity",
        "Unit_Price", "Gross_Amount", "Net_Sales", "COGS", "Gross_Profit", "Profit_Margin_Pct",
        "Is_B2B", "Ship_City", "Ship_State", "Region", "Ship_Postal_Code", "Is_New_Record",
    ])
    db_path = tmp_path / "empty.db"
    initialize_sqlite_database(db_path, empty_fact, pd.DataFrame(), pd.DataFrame(), pd.DataFrame())

    assert total_sales(db_path) == 0.0
    assert distinct_order_count(db_path) == 0
    assert average_order_value(db_path) == 0.0
    assert monthly_sales_trends(db_path).empty
