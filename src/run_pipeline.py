from __future__ import annotations

import argparse

from src.pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the e-commerce ETL pipeline.")
    parser.add_argument(
        "--count",
        type=int,
        default=150,
        help="Number of synthetic new transactions to append when generating the updated fact table.",
    )
    args = parser.parse_args()

    result = run_pipeline(new_orders_count=args.count)
    print("Pipeline completed successfully.")
    print(f"Rows processed: {result['raw_rows_loaded']}")
    print(f"Customers: {result['unique_customers']}")
    print(f"Products: {result['product_skus']}")
    print(f"Updated fact rows: {result['updated_fact_rows']}")


if __name__ == "__main__":
    main()
