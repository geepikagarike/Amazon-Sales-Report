from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

from src.project_paths import (
    DIM_CUSTOMERS_CSV,
    DIM_DATES_CSV,
    DIM_PRODUCTS_CSV,
    FACT_ORDERS_CSV,
    SQLITE_DB_PATH,
)


TABLE_SCHEMAS = {
    "fact_orders": (
        "CREATE TABLE IF NOT EXISTS fact_orders ("
        "Order_Item_ID TEXT PRIMARY KEY, "
        "Order_ID TEXT, "
        "Customer_ID TEXT, "
        "Product_ID TEXT, "
        "Order_Date TEXT, "
        "Year INTEGER, "
        "Month_Name TEXT, "
        "Quarter TEXT, "
        "Order_Status TEXT, "
        "Order_Status_Group TEXT, "
        "Courier_Status TEXT, "
        "Fulfilment_Method TEXT, "
        "Fulfilled_By TEXT, "
        "Sales_Channel TEXT, "
        "Ship_Service_Level TEXT, "
        "Quantity INTEGER, "
        "Unit_Price REAL, "
        "Gross_Amount REAL, "
        "Net_Sales REAL, "
        "COGS REAL, "
        "Gross_Profit REAL, "
        "Profit_Margin_Pct REAL, "
        "Is_B2B INTEGER, "
        "Ship_City TEXT, "
        "Ship_State TEXT, "
        "Region TEXT, "
        "Ship_Postal_Code INTEGER, "
        "Is_New_Record INTEGER)"
    ),
    "dim_products": (
        "CREATE TABLE IF NOT EXISTS dim_products ("
        "Product_ID TEXT PRIMARY KEY, "
        "Product_Name TEXT, "
        "Category TEXT, "
        "Size TEXT, "
        "Unit_MSRP REAL, "
        "Unit_Cost REAL, "
        "Total_Units_Sold INTEGER, "
        "Gross_Revenue REAL, "
        "Net_Revenue REAL)"
    ),
    "dim_customers": (
        "CREATE TABLE IF NOT EXISTS dim_customers ("
        "Customer_ID TEXT PRIMARY KEY, "
        "Customer_Name TEXT, "
        "Customer_Segment TEXT, "
        "Is_B2B INTEGER, "
        "City TEXT, "
        "State TEXT, "
        "Region TEXT, "
        "Postal_Code INTEGER, "
        "Total_Orders INTEGER, "
        "Total_Spend REAL, "
        "Gross_Spend REAL, "
        "First_Order_Date TEXT, "
        "Last_Order_Date TEXT)"
    ),
    "dim_dates": (
        "CREATE TABLE IF NOT EXISTS dim_dates ("
        "Date_Key INTEGER PRIMARY KEY, "
        "Full_Date TEXT, "
        "Date_ISO TEXT, "
        "Year INTEGER, "
        "Quarter TEXT, "
        "Month_Number INTEGER, "
        "Month_Name TEXT, "
        "Year_Month TEXT, "
        "Day_Of_Month INTEGER, "
        "Day_Of_Week TEXT, "
        "Is_Weekend INTEGER)"
    ),
}

INDEX_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_fact_orders_date ON fact_orders(Order_Date)",
    "CREATE INDEX IF NOT EXISTS idx_fact_orders_product_id ON fact_orders(Product_ID)",
    "CREATE INDEX IF NOT EXISTS idx_fact_orders_category ON fact_orders(Order_ID)",
    "CREATE INDEX IF NOT EXISTS idx_fact_orders_status ON fact_orders(Order_Status_Group)",
    "CREATE INDEX IF NOT EXISTS idx_products_category ON dim_products(Category)",
    "CREATE INDEX IF NOT EXISTS idx_customers_region ON dim_customers(Region)",
    "CREATE INDEX IF NOT EXISTS idx_dates_year_month ON dim_dates(Year_Month)",
]


def _normalize_sql_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, (bool,)):
        return int(value)
    if hasattr(value, "item") and not isinstance(value, (str, bytes)):
        try:
            value = value.item()
        except ValueError:
            pass
    return value


def _read_csv_if_present(path: str | Path) -> pd.DataFrame:
    csv_path = Path(path)
    if not csv_path.exists():
        return pd.DataFrame()
    return pd.read_csv(csv_path)


def _ensure_db_path(db_path: str | Path | None) -> Path:
    resolved = Path(db_path) if db_path is not None else SQLITE_DB_PATH
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


def _connect(db_path: str | Path | None = None) -> sqlite3.Connection:
    path = _ensure_db_path(db_path)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _insert_dataframe(conn: sqlite3.Connection, table_name: str, df: pd.DataFrame) -> int:
    if df.empty:
        return 0

    columns = [col for col in df.columns if col in _expected_columns(table_name)]
    if not columns:
        return 0

    df = df.loc[:, columns].copy()
    rows = df.to_dict(orient="records")
    insert_sql = (
        f"INSERT OR IGNORE INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(['?'] * len(columns))})"
    )
    inserted = 0
    for record in rows:
        values = tuple(_normalize_sql_value(record.get(col)) for col in columns)
        conn.execute(insert_sql, values)
        inserted += 1
    return inserted


def _expected_columns(table_name: str) -> list[str]:
    if table_name == "fact_orders":
        return [
            "Order_Item_ID", "Order_ID", "Customer_ID", "Product_ID", "Order_Date", "Year",
            "Month_Name", "Quarter", "Order_Status", "Order_Status_Group", "Courier_Status",
            "Fulfilment_Method", "Fulfilled_By", "Sales_Channel", "Ship_Service_Level",
            "Quantity", "Unit_Price", "Gross_Amount", "Net_Sales", "COGS", "Gross_Profit",
            "Profit_Margin_Pct", "Is_B2B", "Ship_City", "Ship_State", "Region", "Ship_Postal_Code",
            "Is_New_Record",
        ]
    if table_name == "dim_products":
        return [
            "Product_ID", "Product_Name", "Category", "Size", "Unit_MSRP", "Unit_Cost",
            "Total_Units_Sold", "Gross_Revenue", "Net_Revenue",
        ]
    if table_name == "dim_customers":
        return [
            "Customer_ID", "Customer_Name", "Customer_Segment", "Is_B2B", "City",
            "State", "Region", "Postal_Code", "Total_Orders", "Total_Spend",
            "Gross_Spend", "First_Order_Date", "Last_Order_Date",
        ]
    if table_name == "dim_dates":
        return [
            "Date_Key", "Full_Date", "Date_ISO", "Year", "Quarter", "Month_Number",
            "Month_Name", "Year_Month", "Day_Of_Month", "Day_Of_Week", "Is_Weekend",
        ]
    return []


def initialize_sqlite_database(
    db_path: str | Path | None = None,
    fact_df: pd.DataFrame | None = None,
    product_df: pd.DataFrame | None = None,
    customer_df: pd.DataFrame | None = None,
    date_df: pd.DataFrame | None = None,
) -> Path:
    """Initialize the SQLite analytic database and import cleaned datasets safely."""
    path = _ensure_db_path(db_path)
    conn = _connect(path)

    try:
        conn.execute("PRAGMA journal_mode = WAL")
        for table_name, schema_sql in TABLE_SCHEMAS.items():
            conn.execute(schema_sql)
        for index_sql in INDEX_SQL:
            conn.execute(index_sql)

        if fact_df is not None:
            _insert_dataframe(conn, "fact_orders", fact_df)
        if product_df is not None:
            _insert_dataframe(conn, "dim_products", product_df)
        if customer_df is not None:
            _insert_dataframe(conn, "dim_customers", customer_df)
        if date_df is not None:
            _insert_dataframe(conn, "dim_dates", date_df)

        conn.commit()
    finally:
        conn.close()

    return path


def initialize_from_project_files(db_path: str | Path | None = None) -> Path:
    """Load the real cleaned project outputs into the SQLite database."""
    return initialize_sqlite_database(
        db_path=db_path,
        fact_df=_read_csv_if_present(FACT_ORDERS_CSV),
        product_df=_read_csv_if_present(DIM_PRODUCTS_CSV),
        customer_df=_read_csv_if_present(DIM_CUSTOMERS_CSV),
        date_df=_read_csv_if_present(DIM_DATES_CSV),
    )


def _query_frame(sql: str, params: tuple[Any, ...] = (), db_path: str | Path | None = None) -> pd.DataFrame:
    conn = _connect(db_path)
    try:
        return pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()


def total_sales(db_path: str | Path | None = None) -> float:
    result = _query_frame(
        "SELECT COALESCE(SUM(Net_Sales), 0.0) AS total_sales FROM fact_orders",
        db_path=db_path,
    )
    return float(result.iloc[0]["total_sales"]) if not result.empty else 0.0


def distinct_order_count(db_path: str | Path | None = None) -> int:
    result = _query_frame(
        "SELECT COUNT(DISTINCT Order_ID) AS order_count FROM fact_orders WHERE Order_ID IS NOT NULL",
        db_path=db_path,
    )
    return int(result.iloc[0]["order_count"]) if not result.empty else 0


def monthly_sales_trends(db_path: str | Path | None = None) -> pd.DataFrame:
    return _query_frame(
        "SELECT strftime('%Y-%m', Order_Date) AS month, SUM(Net_Sales) AS total_sales, "
        "COUNT(DISTINCT Order_ID) AS order_count FROM fact_orders "
        "WHERE strftime('%Y-%m', Order_Date) IS NOT NULL "
        "GROUP BY strftime('%Y-%m', Order_Date) ORDER BY month",
        db_path=db_path,
    )


def top_products_by_sales(db_path: str | Path | None = None, limit: int = 10) -> pd.DataFrame:
    return _query_frame(
        "SELECT p.Product_Name, p.Category, SUM(f.Net_Sales) AS total_sales, "
        "SUM(CASE WHEN f.Order_Status_Group IN ('Delivered', 'Shipped') THEN f.Quantity ELSE 0 END) AS total_quantity "
        "FROM fact_orders f LEFT JOIN dim_products p ON p.Product_ID = f.Product_ID "
        "GROUP BY p.Product_ID, p.Product_Name, p.Category ORDER BY total_sales DESC LIMIT ?",
        (limit,),
        db_path=db_path,
    )


def top_products_by_quantity(db_path: str | Path | None = None, limit: int = 10) -> pd.DataFrame:
    return _query_frame(
        "SELECT p.Product_Name, p.Category, SUM(f.Quantity) AS total_quantity, SUM(f.Net_Sales) AS total_sales "
        "FROM fact_orders f LEFT JOIN dim_products p ON p.Product_ID = f.Product_ID "
        "WHERE f.Order_Status_Group IN ('Delivered', 'Shipped') "
        "GROUP BY p.Product_ID, p.Product_Name, p.Category ORDER BY total_quantity DESC LIMIT ?",
        (limit,),
        db_path=db_path,
    )


def category_performance(db_path: str | Path | None = None) -> pd.DataFrame:
    return _query_frame(
        "SELECT p.Category, SUM(f.Net_Sales) AS total_sales, "
        "SUM(CASE WHEN f.Order_Status_Group IN ('Delivered', 'Shipped') THEN f.Quantity ELSE 0 END) AS total_quantity, "
        "COUNT(DISTINCT f.Order_ID) AS order_count "
        "FROM fact_orders f LEFT JOIN dim_products p ON p.Product_ID = f.Product_ID "
        "GROUP BY p.Category ORDER BY total_sales DESC",
        db_path=db_path,
    )


def average_order_value(db_path: str | Path | None = None) -> float:
    result = _query_frame(
        "SELECT COALESCE(AVG(order_net_value), 0.0) AS aov FROM ( "
        "SELECT Order_ID, SUM(Net_Sales) AS order_net_value FROM fact_orders "
        "WHERE Order_ID IS NOT NULL GROUP BY Order_ID) t",
        db_path=db_path,
    )
    return float(result.iloc[0]["aov"]) if not result.empty else 0.0


def geographic_sales(db_path: str | Path | None = None) -> pd.DataFrame:
    return _query_frame(
        "SELECT Ship_State AS state, Region, SUM(Net_Sales) AS total_sales, COUNT(DISTINCT Order_ID) AS order_count "
        "FROM fact_orders WHERE Ship_State IS NOT NULL GROUP BY Ship_State, Region ORDER BY total_sales DESC",
        db_path=db_path,
    )


def order_status_breakdown(db_path: str | Path | None = None) -> pd.DataFrame:
    return _query_frame(
        "SELECT Order_Status_Group AS status_group, COUNT(*) AS order_lines, "
        "SUM(Gross_Amount) AS gross_amount, SUM(Net_Sales) AS realized_sales "
        "FROM fact_orders GROUP BY Order_Status_Group ORDER BY order_lines DESC",
        db_path=db_path,
    )


def cancellation_analysis(db_path: str | Path | None = None) -> pd.DataFrame:
    return _query_frame(
        "SELECT Order_Status_Group AS status_group, COUNT(*) AS order_lines, "
        "SUM(Gross_Amount) AS gross_market_value, SUM(Net_Sales) AS realized_sales "
        "FROM fact_orders WHERE Order_Status_Group IN ('Cancelled', 'Returned', 'Pending') "
        "GROUP BY Order_Status_Group ORDER BY gross_market_value DESC",
        db_path=db_path,
    )


def dashboard_summary(db_path: str | Path | None = None) -> dict[str, Any]:
    db_path = _ensure_db_path(db_path)
    return {
        "db_path": str(db_path),
        "total_sales": total_sales(db_path),
        "distinct_order_count": distinct_order_count(db_path),
        "average_order_value": average_order_value(db_path),
        "monthly_sales": monthly_sales_trends(db_path),
        "category_performance": category_performance(db_path),
        "top_products": top_products_by_sales(db_path, limit=8),
        "top_products_quantity": top_products_by_quantity(db_path, limit=8),
        "order_status": order_status_breakdown(db_path),
        "geographic_sales": geographic_sales(db_path),
        "cancellation_analysis": cancellation_analysis(db_path),
    }
