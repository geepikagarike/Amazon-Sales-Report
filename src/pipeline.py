from __future__ import annotations

from typing import Any

from scripts.process_pipeline import create_star_schema, generate_new_records, load_and_clean_data

from src.data_quality import build_quality_report, export_quality_report
from src.project_paths import (
    CLEANED_CSV,
    DIM_CUSTOMERS_CSV,
    DIM_DATES_CSV,
    DIM_PRODUCTS_CSV,
    FACT_ORDERS_CSV,
    QUALITY_DIR,
    UPDATED_CSV,
    ensure_project_directories,
)


def run_pipeline(new_orders_count: int = 150) -> dict[str, Any]:
    """Run the existing ETL flow in a modular way while preserving the project outputs."""
    ensure_project_directories()
    QUALITY_DIR.mkdir(parents=True, exist_ok=True)
    new_orders_count = max(0, int(new_orders_count))

    cleaned_df, category_median_prices = load_and_clean_data()
    quality_report = build_quality_report(cleaned_df, phase_name="post_cleaning")
    export_quality_report(quality_report, QUALITY_DIR / "cleaning_quality_report.json")

    _, dim_customers, dim_products, dim_dates, fact_orders = create_star_schema(
        cleaned_df, category_median_prices
    )

    if new_orders_count > 0:
        _, updated_fact_orders = generate_new_records(
            fact_orders,
            dim_customers,
            dim_products,
            count=new_orders_count,
        )
    else:
        updated_fact_orders = fact_orders.copy()

    cleaned_df.to_csv(CLEANED_CSV, index=False)
    dim_customers.to_csv(DIM_CUSTOMERS_CSV, index=False)
    dim_products.to_csv(DIM_PRODUCTS_CSV, index=False)
    dim_dates.to_csv(DIM_DATES_CSV, index=False)
    fact_orders.to_csv(FACT_ORDERS_CSV, index=False)
    updated_fact_orders.to_csv(UPDATED_CSV, index=False)

    summary = {
        "raw_rows_loaded": int(len(cleaned_df)),
        "unique_customers": int(dim_customers["Customer_ID"].nunique()),
        "product_skus": int(dim_products["Product_ID"].nunique()),
        "fact_rows": int(len(fact_orders)),
        "updated_fact_rows": int(len(updated_fact_orders)),
        "new_records_added": int(new_orders_count),
        "quality_report": quality_report,
    }
    export_quality_report(summary, QUALITY_DIR / "pipeline_summary.json")

    return summary
