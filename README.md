# E-Commerce Sales Analytics

An end-to-end analytics project for exploring Amazon marketplace order-line data with a reproducible Python ETL, a dimensional CSV model, SQLite reporting, MongoDB integration, a Streamlit dashboard, a Node/Express API, and Power BI preparation materials.

## Business problem

The project organizes order-line data so sales, order volume, product/category performance, cancellations, fulfillment, and shipping geography can be analyzed consistently. Its purpose is analytical reporting and demonstration; its calculated costs and customer attributes should not be interpreted as audited financial or identity data.

## Dataset and provenance

- The ETL source is `data/raw/amazon_sales_raw.csv`; cleaned outputs are under `data/cleaned/`.
- The original project also contains files named `Amazon Sale Report.csv` and `raw_amazon_sale_report.csv` in the repository root.
- The exact upstream publisher, download URL, license, and right to redistribute the source data are not established in the project documentation. Confirm these details before publishing or redistributing the raw data.
- The supplied data represents order lines, not one row per order. The fact-table grain is one row per `Order_Item_ID`.

## Architecture

```text
data/raw/amazon_sales_raw.csv
        |
scripts/process_pipeline.py  (existing transformations)
        |
src/pipeline.py + src/data_quality.py
        +--> data/cleaned/fact_orders.csv
        +--> data/cleaned/dim_{customers,products,dates}.csv
        +--> data/quality/*.json
        |
        +--> src/sql_analytics.py --> data/sqlite/ecommerce_analytics.db
        +--> src/powerbi_preparation.py --> data/powerbi/*.csv
        +--> mongodb/import_data.py --> MongoDB (non-destructive key-based upserts)
        +--> app/streamlit_app.py
        +--> server/server.js --> MongoDB-backed REST endpoints
```

The original ETL remains the transformation source. `python -m src.run_pipeline --count 0` runs it without generating synthetic additions, but refreshes the cleaned/updated outputs and quality summaries. It does not write to `data/raw/`. The `--count` default remains 150 for compatibility; specify `--count 0` when only rebuilding from source.

## Cleaning, model, and business rules

- ETL removes duplicate rows, standardizes dates/categories/geography/statuses, and creates customer/product/date dimensions plus the order-line fact table.
- `Order_Status_Group` includes `Delivered`, `Shipped`, `Cancelled`, `Returned`, `Pending`, and `Other`.
- `Net_Sales` is the ETL's realized-sales measure: the amount is retained for `Delivered` and `Shipped`, and is zero for other status groups. SQL/Python sales sums retain the provided measure and do not impute missing amounts.
- `COGS` is estimated as 65% of `Net_Sales`; `Gross_Profit` and margin are therefore model estimates, not observed supplier costs.
- KPI definitions are documented in [docs/powerbi_kpi_definition.md](docs/powerbi_kpi_definition.md).

## Verified data snapshot

The current cleaned outputs contain 128,017 fact rows, 45 product rows, 14,813 customer rows, and 121 date rows. The current observed model check found unique dimension keys and no unmatched customer, product, or date foreign keys. A final comparison run confirmed the following Python/SQLite values within the documented tolerances:

| KPI | Verified value |
|---|---:|
| Total sales (`Net_Sales`) | INR 69,392,224.00 |
| Distinct nonblank orders | 120,229 |
| Units sold (`Delivered` + `Shipped` only) | 107,266 |
| Average order value | INR 577.17 |

The detailed row-by-row comparison is written to `data/validation/python_sqlite_comparison.csv`. Detailed validation findings across Python, SQLite, MongoDB, and the API are documented in [docs/final_validation_report.md](docs/final_validation_report.md) and [docs/antigravity_handoff.md](docs/antigravity_handoff.md).

## Python analytics and tests

- `src/sql_analytics.py` provides SQLite initialization and query functions for sales, orders, AOV, monthly trends, products, categories, order statuses, cancellations, and shipping geography.
- SQLite tables use the cleaned fact/dimension schema; repeated loads use key-based `INSERT OR IGNORE`, not a database reset.
- `src/analytics_validation.py` independently calculates Python aggregates and compares them to SQLite for total sales, distinct orders, units, AOV, monthly sales, category sales, and product sales. Mismatches appear as `FAIL`; the command exits nonzero.
- `src/data_quality.py` and the tests validate ETL and data quality behavior.
- Automated test suites verify 38 test cases (27 Python tests via `pytest` and 11 Node.js tests via `node --test`) across data transformations, schema integrity, and API boundaries.

## MongoDB integration

Collections map from the star schema as `orders` (fact), `products`, `customers`, and `dates`. The Python and Node importers use stable source keys and upserts. They do not clear collections; MongoDB documents whose keys no longer occur in the CSV remain until an operator separately handles them.

MongoDB configuration comes from `MONGO_URI` and `DB_NAME` environment variables; defaults target local MongoDB at `mongodb://localhost:27017` and database `ecommerce_analytics_db`. Configure credentials locally, never in source control. `src/mongo_validation.py` performs read-only count, required-field/type, index, and KPI checks against a reachable configured database. A `SKIPPED` result means no live claims were verified; a `FAIL` result reports observed discrepancies.

## SQL and Streamlit

The Streamlit app is [app/streamlit_app.py](app/streamlit_app.py); it reads the SQLite-backed summary and has Executive Overview, Product Analytics, Order Operations, and Market Basket Analysis sections. The Market Basket section reports an empty state unless actual rule exports are available. No verified Apriori/FP-Growth rules or benchmark results are currently included.

## Power BI preparation

Run `python -m src.powerbi_preparation` to create `data/powerbi/orders.csv`, `products.csv`, `customers.csv`, and `dates.csv` from actual cleaned inputs. Exact column types, query/table names, relationships, date-table setup, measures, and four-page report design are in:

- [powerbi/data_model/powerbi_final_setup_guide.md](powerbi/data_model/powerbi_final_setup_guide.md)
- [powerbi/measures/dax_measures_library.dax](powerbi/measures/dax_measures_library.dax)
- [powerbi/dashboard_documentation/powerbi_final_dashboard_spec.md](powerbi/dashboard_documentation/powerbi_final_dashboard_spec.md)

Power BI Desktop work is manual. No `.pbix` file was created or modified. The Market Basket report page must remain an explanatory empty state until real association rules and benchmark data are generated.

## E-Commerce Order Management & Tracking API (Node.js, Express & MongoDB)

The Express backend in `server/server.js` provides an enterprise-grade Order Management & Tracking REST API alongside MongoDB analytics routes:

- **Order CRUD & Search:** Full lifecycle support via `POST /api/orders`, `GET /api/orders` (multi-field filters, search, sorting, pagination), `GET /api/orders/:orderId`, `PATCH /api/orders/:orderId` (immutable field protection), and `DELETE /api/orders/:orderId` (safe soft-deletion policy with `?hard=true` purge).
- **Order Status State Machine:** Enforces valid lifecycle progression (`Pending` -> `Shipped` -> `Delivered`/`Returned`), preventing illegal terminal transitions.
- **CSV Order Importer:** `server/scripts/importOrders.js` validates schemas, converts data types, supports `--dry-run`, and performs non-destructive batch upserts (`bulkWrite`).
- **Resilience & Security:** Centralized error middleware, bounded query parameters, masked URI credentials, and graceful shutdown.
- **Detailed Specifications:**
  - [docs/api_documentation.md](docs/api_documentation.md): Complete OpenAPI-style endpoint and schema specification.
  - [docs/database_schema.md](docs/database_schema.md): Document structure, indexes, and performance architecture.
- **Automated Tests:** 30 unit and integration tests run offline without external database credentials (`npm test`).

## Setup and execution (Windows PowerShell)

### 1. Python Analytics Pipeline & Validation

```powershell
cd "C:\Users\garik\OneDrive\Documents\Desktop\amazon_mongo_project"

# Install Python requirements and run offline pipeline
python -m pip install -r requirements.txt
python -m src.run_pipeline --count 0
python -m src.analytics_validation
python -m src.powerbi_preparation
python -m pytest -q
```

### 2. Node.js Order Management API & Tests

```powershell
cd "C:\Users\garik\OneDrive\Documents\Desktop\amazon_mongo_project\server"

# Install dependencies and run 30 automated API tests (offline)
npm install
npm test

# Validate cleaned order dataset with CSV importer dry-run
npm run import-orders:dry-run

# Start the Order Management & Tracking API server
npm start
```

### 3. Optional MongoDB Live Operations (When Configured by User)

```powershell
# Read-only verification of configured database
python -m src.mongo_validation

# Non-destructive CSV import into MongoDB
npm run import-orders

# Run live API smoke check against running database
node scripts/live_api_smoke.js
```

To launch Streamlit:

```powershell
cd "C:\Users\garik\OneDrive\Documents\Desktop\amazon_mongo_project"
streamlit run app/streamlit_app.py
```

## Limitations and manual work

- Confirm upstream dataset attribution/license before redistribution.
- MongoDB results require a running configured instance; unit tests do not require Mongo credentials.
- Power BI relationships, report visuals, and `.pbix` saving are manual.
- Market Basket Analysis has no real rule/benchmark output yet.
- The COGS/profit measures are estimates based on the ETL's 65% rule.
- Use `npm audit` to review development dependency advisories; production dependencies were reported clean by `npm audit --omit=dev` at the Phase 5 validation.
