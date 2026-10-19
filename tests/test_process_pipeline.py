import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "process_pipeline.py"
SPEC = importlib.util.spec_from_file_location("process_pipeline", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_load_and_clean_data_keeps_key_business_columns():
    df, _ = MODULE.load_and_clean_data()

    required_columns = {
        "Order_ID",
        "Order_Date",
        "Order_Status",
        "Quantity",
        "Gross_Amount",
        "Net_Sales",
        "Category",
        "Ship_State",
    }

    assert required_columns.issubset(df.columns)
    assert len(df) > 120_000
    assert df["Order_Date"].notna().all()
    assert df["Order_ID"].notna().all()
    assert df["Gross_Amount"].notna().all()


def test_create_star_schema_builds_expected_dimensions():
    df, _ = MODULE.load_and_clean_data()
    _, dim_customers, dim_products, dim_dates, fact_orders = MODULE.create_star_schema(
        df, {}
    )

    assert len(dim_customers) > 0
    assert len(dim_products) > 0
    assert len(dim_dates) > 0
    assert len(fact_orders) == len(df)

    assert {"Customer_ID", "Customer_Name"}.issubset(dim_customers.columns)
    assert {"Product_ID", "Product_Name", "Category"}.issubset(dim_products.columns)
    assert {"Order_Item_ID", "Order_ID", "Customer_ID", "Product_ID"}.issubset(fact_orders.columns)
