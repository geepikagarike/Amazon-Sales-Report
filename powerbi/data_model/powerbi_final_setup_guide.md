# Power BI Final Setup Guide

## Data source and verified grain

Run `python -m src.powerbi_preparation` from the project root. It writes four cleaned CSV exports to `data/powerbi/`:

| Export file | Power BI table name | Grain | Key |
|---|---|---|---|
| `orders.csv` | `fact_orders` | One row per order line | `Order_Item_ID` |
| `products.csv` | `dim_products` | One row per product SKU | `Product_ID` |
| `customers.csv` | `dim_customers` | One row per customer record | `Customer_ID` |
| `dates.csv` | `dim_dates` | One row per calendar date | `Date_ISO` (also has `Date_Key`) |

The exports copy the existing cleaned CSVs and retain their PascalCase column names. No `.pbix` file is generated or modified by this project code.

## Import steps

1. In Power BI Desktop select **Get data > Text/CSV** and load `data/powerbi/orders.csv`, `products.csv`, `customers.csv`, and `dates.csv`.
2. In Power Query rename the queries to exactly `fact_orders`, `dim_products`, `dim_customers`, and `dim_dates`. DAX in `powerbi/measures/dax_measures_library.dax` expects these table names.
3. Set the column types below, then select **Close & Apply**.

## Column types

### `fact_orders`
- Text: `Order_Item_ID`, `Order_ID`, `Customer_ID`, `Product_ID`, `Month_Name`, `Quarter`, `Order_Status`, `Order_Status_Group`, `Courier_Status`, `Fulfilment_Method`, `Fulfilled_By`, `Sales_Channel`, `Ship_Service_Level`, `Ship_City`, `Ship_State`, `Region`
- Date: `Order_Date`
- Whole number: `Year`, `Quantity`, `Ship_Postal_Code`
- Decimal number / currency: `Unit_Price`, `Gross_Amount`, `Net_Sales`, `COGS`, `Gross_Profit`
- Decimal number / percentage: `Profit_Margin_Pct` (stored in the source as 0-100; format as percentage after dividing by 100 in Power Query, or leave as a 0-100 number)
- True/false: `Is_B2B`, `Is_New_Record`

### `dim_products`
- Text: `Product_ID`, `Product_Name`, `Category`, `Size`
- Whole number: `Total_Units_Sold`
- Decimal number / currency: `Unit_MSRP`, `Unit_Cost`, `Gross_Revenue`, `Net_Revenue`

### `dim_customers`
- Text: `Customer_ID`, `Customer_Name`, `Customer_Segment`, `City`, `State`, `Region`
- True/false: `Is_B2B`
- Whole number: `Postal_Code`, `Total_Orders`
- Decimal number / currency: `Total_Spend`, `Gross_Spend`
- Date: `First_Order_Date`, `Last_Order_Date`

### `dim_dates`
- Date: `Full_Date`, `Date_ISO`
- Whole number: `Date_Key`, `Year`, `Month_Number`, `Day_Of_Month`
- True/false: `Is_Weekend`
- Text: `Quarter`, `Month_Name`, `Year_Month`, `Day_Of_Week`

Set monetary columns to the INR currency format. The ETL standardizes the source currency to INR; the fact export does not contain a row-level `Currency` column.

## Relationships

In **Model view**, create the following active, one-to-many relationships with single-direction filtering from dimension to fact:

1. `dim_customers[Customer_ID]` (1) -> `fact_orders[Customer_ID]` (*)
2. `dim_products[Product_ID]` (1) -> `fact_orders[Product_ID]` (*)
3. `dim_dates[Date_ISO]` (1) -> `fact_orders[Order_Date]` (*)

Do not create additional relationships from customer geography fields to the fact's shipping geography; `fact_orders` already contains `Ship_State` and `Region`, and parallel paths can create ambiguous filtering.

Select `dim_dates[Date_ISO]`, confirm its type is **Date** and values are unique/nonblank, then choose **Table tools > Mark as date table > Date_ISO**. Sort `dim_dates[Month_Name]` by `dim_dates[Month_Number]`; use `Year_Month` for chronological month axes.

## Measures

Create a measure table named `_Measures` (Home > Enter data, then remove its placeholder column) and add the expressions in `powerbi/measures/dax_measures_library.dax` one measure at a time. Set formats:

- Currency (INR): `Total Sales`, `Gross Merchandise Value`, `Total Gross Profit`, `Cancelled GMV`, fulfillment sales, `Average Order Value`, `Average Selling Price`, `Prior Month Sales`, and `Month-over-Month Sales Change`.
- Percentage: `Gross Profit Margin`, `Cancellation Rate`, `Return Rate`, `Fulfillment Success Rate`, `Category Sales Share`, and `Month-over-Month Sales Change %`.
- Whole number: order/customer/units counts and product ranks.

## Validation before publishing

1. In Power Query confirm headers match the source CSV headers (including case and underscores).
2. In Model view verify each dimension key is unique and the three relationships have `1:*` cardinality.
3. Run `python -m src.analytics_validation` and confirm every comparison row is `PASS`.
4. Compare Power BI cards for `Total Sales`, `Distinct Orders`, `Units Sold`, and `Average Order Value` with the Python/SQLite report at `data/validation/python_sqlite_comparison.csv`.
5. Do not treat a missing amount as zero during Power Query cleanup. The ETL's explicit financial rules produce `Net_Sales`; preserve nulls if any appear in future inputs.
6. Save a `.pbix` manually to a location of your choice. No Power BI Desktop automation or `.pbix` is included in the repository changes.
