# Excel & Python Data Cleaning and Preparation Methodology

## 1. Initial Data Inspection & Health Check

The raw Amazon Sales dataset contained **128,976 records and 21 columns**.

### Missing Values & Data Health Summary

| Raw Column Name | Non-Null Count | Null Count | % Missing | Issue Identified | Cleaning Action Taken | Justification |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `index` | 128,976 | 0 | 0.0% | Redundant serial index | **Dropped** | Index provides no business analytical value. |
| `New` | 0 | 128,976 | 100.0% | Completely empty column | **Dropped** | Entirely null artifact from data export. |
| `PendingS` | 0 | 128,976 | 100.0% | Completely empty column | **Dropped** | Entirely null artifact from data export. |
| `Amount` | 121,176 | 7,800 | 6.05% | Null transaction amount | **Imputed conditionally** | When Qty = 0 (7,676 rows), Amount = 0.00. When Qty > 0 (124 rows), imputed with median category unit price. |
| `currency` | 121,176 | 7,800 | 6.05% | Missing currency code | **Imputed as 'INR'** | All transactions in dataset are conducted in Indian Rupees (INR). |
| `ship-city` | 128,941 | 35 | 0.03% | Unspecified shipping city | **Imputed as 'Unknown'** | Preserves order count without fabricating fake location data. |
| `ship-state` | 128,941 | 35 | 0.03% | Inconsistent state names (69 variants) | **Standardized & Imputed** | Standardized 69 dirty variants into 36 clean official Indian States & UTs. |
| `ship-postal-code` | 128,941 | 35 | 0.03% | Missing PIN code | **Imputed as 0** | Cast to integer format. |
| `fulfilled-by` | 39,263 | 89,713 | 69.56% | Missing when Amazon FBA | **Imputed as 'Amazon FBA'** | Null corresponds to Fulfilled by Amazon; non-null represents Merchant Easy Ship. |

---

## 2. Step-by-Step Data Cleaning Operations

### A. Deduplication
* **Operation**: Identified 959 duplicate transaction records across all feature columns.
* **Action**: Removed duplicate rows using `drop_duplicates()`. Record count dropped from 128,976 to **128,017 clean records**.

### B. Standardizing Geographic Data (69 State Variants -> 36 Standard States/UTs)
* **Raw Inconsistencies**:
  - `Rajshthan`, `Rajsthan`, `RJ`, `rajasthan`, `RAJASTHAN` -> `Rajasthan`
  - `orissa`, `Orissa`, `ODISHA`, `Odisha` -> `Odisha`
  - `PB`, `Punjab/Mohali/Zirakpur`, `punjab`, `Punjab` -> `Punjab`
  - `delhi`, `New Delhi`, `Delhi`, `DELHI` -> `Delhi`
  - `NL`, `Nagaland`, `NAGALAND` -> `Nagaland`
  - `Pondicherry`, `Puducherry`, `PUDUCHERRY` -> `Puducherry`
  - `AR`, `Arunachal Pradesh`, `Arunachal pradesh` -> `Arunachal Pradesh`

### C. Standardizing Date Formats & Date Part Extractions
* Converted mixed date strings (`04-30-22` and `05-02-2022`) to ISO `YYYY-MM-DD`.
* Extracted analytical fields: `Year` (2022), `Quarter` (`2022Q2`), `Month_Name` (`April`, `May`, `June`), `Year_Month` (`2022-04`), `Day_Of_Week`, `Is_Weekend`.

### D. Financial & Revenue Metrics Calculation
* **Gross Merchandise Value (GMV)**: Quoted transaction amount before cancellations.
* **Net Realized Revenue**: Quoted amount for `Delivered` and `Shipped` orders, set to `0.00` for `Cancelled` and `Returned` orders.
* **COGS (Cost of Goods Sold)**: Modeled at standard 65% wholesale merchandise cost.
* **Gross Profit**: `Net_Sales - COGS` (35% margin).

---

## 3. Adding New Business Data (Updating Analytics Dataset)
* Generated **150 realistic newly added orders** for July 1-15, 2022.
* Maintained strict schema consistency with `Is_New_Record = TRUE`.
* Demonstrates the pipeline's capability to ingest new transactional batches into an active analytics data warehouse.
