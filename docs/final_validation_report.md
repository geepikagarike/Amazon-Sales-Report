# Final Analytics & System Validation Report

## Executive Summary

This report documents the rigorous, cross-layer technical validation of the **Retail Sales & Market Basket Analytics / E-Commerce Analytics** platform. The system spans an end-to-end data stack including Python ETL pipelines, a SQLite dimensional reporting database, a MongoDB Atlas/local document store, an Express/Node.js REST API layer, Power BI semantic modeling, and a Streamlit executive dashboard.

All validation runs were conducted against the verified local dataset snapshot (`128,017` cleaned fact records, `45` product SKUs, `14,813` customers, and `121` calendar dates). No simulated metrics or hardcoded values were used.

---

## 1. Multi-Engine KPI Parity Analysis

Business metrics were computed independently across four separate execution engines:
1. **Python Pandas Engine** (`src/analytics_validation.py`)
2. **SQLite Query Engine** (`data/sqlite/ecommerce_analytics.db` via `src/sql_analytics.py`)
3. **MongoDB Aggregation Pipeline** (`mongodb/aggregation_queries.js` via `src/mongo_validation.py`)
4. **Node.js Express REST API** (`server/server.js` via `server/scripts/live_api_smoke.js`)

### Primary Executive KPI Comparison

| KPI Metric | Business Logic / Filter | Python Value | SQLite Value | MongoDB Value | Node.js API | Tolerance | Status |
|---|---|---:|---:|---:|---:|---:|:---:|
| **Total Realized Sales** | Sum of `Net_Sales` (`Delivered` + `Shipped`) | INR 69,392,224.00 | INR 69,392,224.00 | INR 69,392,224.00 | INR 69,392,224.00 | 0.01 | **PASS** |
| **Distinct Orders** | Distinct nonblank `Order_ID` | 120,229 | 120,229 | 120,229 | 120,229 | 0.00 | **PASS** |
| **Units Sold** | Sum of `Quantity` for `Delivered` & `Shipped` | 107,266 | 107,266 | 107,266 | 107,266 | 0.01 | **PASS** |
| **Average Order Value** | Total Realized Sales / Distinct Orders | INR 577.17 | INR 577.17 | INR 577.17 | INR 577.17 | 0.01 | **PASS** |

### Monthly Trend Validation (Sample Period)

| Month (`Year_Month`) | Python Sales (INR) | SQLite Sales (INR) | MongoDB Sales (INR) | Difference | Status |
|---|---:|---:|---:|---:|:---:|
| **2022-03** | 94,183.00 | 94,183.00 | 94,183.00 | 0.00 | **PASS** |
| **2022-04** | 25,526,873.00 | 25,526,873.00 | 25,526,873.00 | 0.00 | **PASS** |
| **2022-05** | 23,385,505.00 | 23,385,505.00 | 23,385,505.00 | 0.00 | **PASS** |
| **2022-06** | 20,385,663.00 | 20,385,663.00 | 20,385,663.00 | 0.00 | **PASS** |

### Top Product Sales Parity (Sample SKUs)

| Product SKU | Category | Python Net Sales | SQLite Net Sales | Difference | Status |
|---|---|---:|---:|---:|:---:|
| `PROD-TSH-M` | T-shirt | INR 6,390,468.00 | INR 6,390,468.00 | 0.00 | **PASS** |
| `PROD-TSH-L` | T-shirt | INR 5,613,732.00 | INR 5,613,732.00 | 0.00 | **PASS** |
| `PROD-TSH-XL` | T-shirt | INR 5,253,941.00 | INR 5,253,941.00 | 0.00 | **PASS** |
| `PROD-TSH-S` | T-shirt | INR 5,170,544.00 | INR 5,170,544.00 | 0.00 | **PASS** |
| `PROD-TSH-XXL` | T-shirt | INR 4,263,026.00 | INR 4,263,026.00 | 0.00 | **PASS** |
| `PROD-SHT-L` | Shirt | INR 3,291,955.00 | INR 3,291,955.00 | 0.00 | **PASS** |

The complete 61-row line-item comparison is preserved in `data/validation/python_sqlite_comparison.csv`.

---

## 2. Dimensional Model & Star Schema Integrity

Star schema relationships were formally audited using `validate_star_schema_relationships()` in `src/analytics_validation.py`:

| Relationship | Fact Key | Dimension Key | Cardinality | Unmatched Keys | Duplicate Dim Keys | Status |
|---|---|---|:---:|---:|---:|:---:|
| `fact_orders.Order_Item_ID` | `Order_Item_ID` | N/A (PK) | 1:1 | 0 | 0 | **PASS** |
| `fact_orders -> dim_customers` | `Customer_ID` | `Customer_ID` | N:1 | 0 | 0 | **PASS** |
| `fact_orders -> dim_products` | `Product_ID` | `Product_ID` | N:1 | 0 | 0 | **PASS** |
| `fact_orders -> dim_dates` | `Order_Date` | `Date_ISO` | N:1 | 0 | 0 | **PASS** |

- Total fact table records: `128,017`
- Unique customers in dimension: `14,813`
- Unique products in dimension: `45`
- Unique dates in dimension: `121`
- Orphan foreign keys: `0` across all relationships.

---

## 3. MongoDB Integration & Document Schema Audit

Live checks against the configured database (`ecommerce_analytics_db`) verified non-destructive, source-keyed data storage:

| Collection | Expected Documents | Live Count | Missing / Null Fields | Type Discrepancies | Verified Indexes | Status |
|---|---:|---:|---:|---:|---|:---:|
| `orders` | 128,017 | 128,017 | 0 | 0 | `idx_order_item_id`, `idx_order_id`, `idx_product_id`, `idx_order_date` | **PASS** |
| `products` | 45 | 45 | 0 | 0 | `idx_prod_id_pk` | **PASS** |
| `customers` | 14,813 | 14,813 | 0 | 0 | `idx_cust_id_pk` | **PASS** |
| `dates` | 121 | 121 | 0 | 0 | `idx_date_key_pk` | **PASS** |

- **Safe repeated imports:** Verified through tests and source code that imports execute idempotent `updateOne(..., { $set: doc }, { upsert: true })` without deleting collections or dropping unassociated documents.

---

## 4. Node.js Express REST API Validation

The REST API in `server/server.js` was evaluated using automated unit test fixtures (mock DB) and live integration smoke tests:

### Unit Test Suite (`node --test`)
- **Total Tests:** 11 passing tests.
- **Input Bounds:** Validated pagination limits (`page >= 1`, `limit <= 500`).
- **Validation Rules:** Verified `POST /api/orders` enforces non-empty strings, positive integer quantities, finite non-negative currency amounts, boolean `is_b2b`, and strips client-provided primary keys/timestamps.
- **Resilience:** Confirmed internal database errors return generic 500 without leaking stack traces or credentials; disconnected database returns 503; missing records return 404.
- **Aggregation Endpoints Verified:**
  - `GET /api/analytics/kpis`
  - `GET /api/analytics/monthly-sales`
  - `GET /api/analytics/category-performance`
  - `GET /api/analytics/top-products`
  - `GET /api/analytics/top-customers`
  - `GET /api/analytics/customer-segments`
  - `GET /api/analytics/order-status`
  - `GET /api/analytics/regional-sales`
  - `GET /api/analytics/fulfilment-analysis`

### Live API Smoke Test Result
- `node server/scripts/live_api_smoke.js`
- Response: HTTP 200 OK
- Data: `net_realized_revenue: 69392224`, `total_orders_count: 120229`, `total_items_sold: 107266`, `average_order_value: 577.17`.

---

## 5. Power BI Preparation & Semantic Layer

1. **Cleaned CSV Exports (`data/powerbi/`):**
   - `orders.csv` (`30,330,871` bytes, 128,017 rows)
   - `products.csv` (`5,030` bytes, 45 rows)
   - `customers.csv` (`1,762,603` bytes, 14,813 rows)
   - `dates.csv` (`9,256` bytes, 121 rows)
   - Verified that column headers, types, and primary/foreign keys directly mirror the star schema.
2. **DAX Measures Library (`powerbi/measures/dax_measures_library.dax`):**
   - Contains 26 production-grade measures covering realized sales, GMV, COGS, gross margin %, distinct orders, units sold, AOV, cancellation rates, return rates, fulfillment channel share, MoM sales variances, and dense product rankings.
3. **Four-Page Dashboard Blueprint (`powerbi/dashboard_documentation/powerbi_final_dashboard_spec.md`):**
   - **Page 1: Executive Overview** (KPI cards, monthly trend line, category bars, top 10 products).
   - **Page 2: Product & Category Analysis** (Volume vs. value charts, category sales share, SKU drill-through table).
   - **Page 3: Order & Fulfillment Operations** (Status funnel, cancellation GMV, Amazon vs Merchant fulfillment, shipping state breakdown).
   - **Page 4: Market Basket Analysis** (Association rules blueprint, antecedents/consequents, support/confidence/lift matrix).
4. **Manual Setup Step:** As `.pbix` binary files require interactive Power BI Desktop authoring, manual modeling instructions are documented in `powerbi/data_model/powerbi_final_setup_guide.md`.

---

## 6. Automated Test Suite Summary

| Test Module | Framework | Test Count | Status |
|---|---|---:|:---:|
| `tests/test_analytics_validation.py` | `pytest` | 7 | **PASS** |
| `tests/test_data_quality.py` | `pytest` | 2 | **PASS** |
| `tests/test_mongo_integration.py` | `pytest` | 10 | **PASS** |
| `tests/test_mongo_validation.py` | `pytest` | 2 | **PASS** |
| `tests/test_process_pipeline.py` | `pytest` | 2 | **PASS** |
| `tests/test_sql_analytics.py` | `pytest` | 4 | **PASS** |
| **Python Total** | | **27** | **100% PASS** |
| `server/test/api.test.js` | `node --test` | 9 | **PASS** |
| `server/test/mongo_import.test.js` | `node --test` | 2 | **PASS** |
| **Node.js Total** | | **11** | **100% PASS** |
| **Combined Total** | | **38** | **100% PASS** |

---

## 7. Known Scope Limitations & Operational Guidance

1. **Market Basket Association Rules:** The repository currently has an empty state for association rules on Page 4 of the Streamlit and Power BI specifications because no offline Apriori or FP-Growth models have been persisted. The system explicitly communicates this state rather than generating fictitious association rules.
2. **COGS & Profit Margins:** As observed in the ETL code, COGS is modeled at 65% of Net Sales. Cost and margin metrics reflect this financial heuristic and should be disclosed as estimates.
3. **Power BI Report Authoring:** Generating the visual layout and saving `.pbix` remains a manual step performed in Power BI Desktop using the prepared CSVs and DAX library.
