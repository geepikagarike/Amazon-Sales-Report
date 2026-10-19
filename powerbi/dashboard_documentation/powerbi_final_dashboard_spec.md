# Power BI Final Dashboard Specification

This is an implementation specification for a manually built `.pbix` report, not a claim that a report file has been created. Use the table names, relationships, and measures in `powerbi/data_model/powerbi_final_setup_guide.md`. All sales figures are in INR as standardized by the ETL.

## Shared report design

- 16:9 canvas; restrained navy, blue, neutral gray, green, and red palette.
- Use INR currency and percentage formats from the DAX library. Do not hardcode sample KPI values in visuals.
- Keep dimension slicers on each page: `dim_dates[Year_Month]`, `dim_products[Category]`, `fact_orders[Order_Status_Group]`, and `fact_orders[Fulfilment_Method]`; sync date and category slicers where appropriate.
- Add a compact subtitle with the selected period and source refresh date. CSV exports have no refresh metadata, so display the file refresh date only if a report author records it separately; do not infer it from transaction dates.
- Use built-in tooltips with the measure value and the applicable category/product/status fields.

## Page 1 — Executive Overview

**Purpose:** Communicate realized sales, order volume, and product mix without treating every order as a completed sale.

- KPI cards: `Total Sales`, `Distinct Orders`, `Units Sold`, `Average Order Value`, `Gross Profit Margin`.
- Line chart: `dim_dates[Year_Month]` on axis, `Total Sales` as value; sort `Year_Month` ascending.
- Clustered bar chart: `dim_products[Category]` by `Total Sales`; optional tooltip for `Category Sales Share` and `Units Sold`.
- Horizontal bar chart: top 10 `dim_products[Product_Name]` by `Total Sales`, with `Product_ID` as a tooltip.
- Slicers: date/year-month, category, `Order_Status_Group`, fulfillment method.

## Page 2 — Product Analysis

**Purpose:** Compare product sales value and realized volume, with drill-through to SKU detail.

- Horizontal bar charts: top products by `Total Sales`, and top products by `Units Sold`.
- Category contribution: bar or donut by `dim_products[Category]` using `Category Sales Share`; retain the current filter context except the category filter in the measure.
- Product detail table: `Product_ID`, `Product_Name`, `Category`, `Size`, `Total Sales`, `Units Sold`, `Average Selling Price`, `Product Sales Rank`.
- Drill-through page or tooltip filtered by `Product_ID`; include order-status and date context in the detail view.
- Slicers: category, size, date/year-month, order status, fulfillment method.

## Page 3 — Order Operations

**Purpose:** Show order-state mix and operational differences supported by the cleaned fields.

- Stacked column or bar: `Order_Status_Group` by distinct-order measure; add order-line count only if explicitly labeled as line count.
- KPI cards: `Cancellation Rate`, `Cancelled Orders`, `Cancelled GMV`, `Return Rate`, `Fulfillment Success Rate`.
- Fulfillment comparison: `Fulfilment_Method` against `Total Sales`, `Distinct Orders`, and `Fulfillment Success Rate`.
- Geographic performance: bar chart by `Ship_State` or `Region` using `Total Sales`; label values as shipping geography, not customer home geography.
- Slicers: date/year-month, order status, fulfillment method, region/state.

## Page 4 — Market Basket Analysis

**Purpose:** Show association rules only when validated rule exports exist.

- Expected visual when rule output exists: table with antecedents, consequents, support, confidence, and lift; sort by lift/confidence and provide minimum-support/confidence filters.
- Apriori versus FP-Growth benchmark: compare runtime and rule counts only when benchmark files contain measured values, matching input data and parameters.
- Cross-selling recommendations must be derived from actual rule antecedents/consequents and documented thresholds; do not infer recommendations from product sales rankings.
- Current limitation: the repository has no validated Apriori/FP-Growth rule exports or benchmark measurements. Leave this page with an explanatory empty-state note until those outputs are produced. Do not create placeholder KPI values or simulated rules.

## KPI and relationship checks

Before publishing, use the measures in `powerbi/measures/dax_measures_library.dax` and validate the four headline metrics against `data/validation/python_sqlite_comparison.csv`. Confirm the relationships remain active `1:*`, dimension-to-fact single direction, and that `dim_dates[Date_ISO]` is the marked date column. The metric `Units Sold` includes quantities only for `Delivered` and `Shipped` status groups; cancellation rate counts distinct cancelled orders against all distinct nonblank order IDs.
