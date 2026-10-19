from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
CLEANED_DIR = DATA_DIR / "cleaned"
UPDATED_DIR = DATA_DIR / "updated"
QUALITY_DIR = DATA_DIR / "quality"
SQLITE_DIR = DATA_DIR / "sqlite"
POWERBI_DIR = DATA_DIR / "powerbi"
VALIDATION_DIR = DATA_DIR / "validation"
EXCEL_DIR = ROOT_DIR / "excel"
MONGODB_DIR = ROOT_DIR / "mongodb"
APP_DIR = ROOT_DIR / "app"

RAW_FILE = RAW_DIR / "amazon_sales_raw.csv"
CLEANED_CSV = CLEANED_DIR / "amazon_sales_cleaned.csv"
UPDATED_CSV = UPDATED_DIR / "amazon_sales_with_new_data.csv"
DIM_CUSTOMERS_CSV = CLEANED_DIR / "dim_customers.csv"
DIM_PRODUCTS_CSV = CLEANED_DIR / "dim_products.csv"
DIM_DATES_CSV = CLEANED_DIR / "dim_dates.csv"
FACT_ORDERS_CSV = CLEANED_DIR / "fact_orders.csv"
SQLITE_DB_PATH = SQLITE_DIR / "ecommerce_analytics.db"

QUALITY_REPORT_PATH = QUALITY_DIR / "cleaning_quality_report.json"
PIPELINE_SUMMARY_PATH = QUALITY_DIR / "pipeline_summary.json"


def ensure_project_directories() -> None:
    for path in (
        DATA_DIR, RAW_DIR, CLEANED_DIR, UPDATED_DIR, QUALITY_DIR, SQLITE_DIR,
        POWERBI_DIR, VALIDATION_DIR, EXCEL_DIR, APP_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)
