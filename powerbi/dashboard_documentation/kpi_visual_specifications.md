# Power BI KPI & Visual Specifications

## 1. Visual Card Specifications

### Card 1: Net Realized Revenue
* **DAX Measure**: `[Net Revenue]`
* **Formatting**: Currency (`INR #,##0,,"M"` or `INR #,##0.00`)
* **Color**: Navy `#1F4E78`
* **Sub-text**: `[MoM Revenue Growth %]` with Dynamic Green `#548235` / Red `#C00000` conditional color formatting.

### Card 2: Total Orders
* **DAX Measure**: `[Total Orders]`
* **Formatting**: Whole Number with commas (`120,229`)
* **Sub-text**: "83.5% Successful Fulfillment"

### Card 3: Average Order Value (AOV)
* **DAX Measure**: `[Average Order Value (AOV)]`
* **Formatting**: Currency `INR 577.17`
* **Sub-text**: "Target: > INR 600"

### Card 4: Gross Profit Margin %
* **DAX Measure**: `[Gross Profit Margin %]`
* **Formatting**: Percentage `35.00%`
* **Sub-text**: "Gross Profit: INR 24.28M"

---

## 2. Interactive Slicer Specifications

1. **Date Slicer**:
   - Hierarchy: `dim_dates[Year]` -> `dim_dates[Quarter]` -> `dim_dates[Month_Name]`
   - Type: Between Date Range or Tile buttons.
2. **Category Slicer**:
   - Field: `dim_products[Category]`
   - Orientation: Horizontal tile ribbon.
3. **Region Slicer**:
   - Field: `dim_customers[Region]`
   - Dropdown multi-select with search.
4. **Fulfilment Slicer**:
   - Field: `fact_orders[Fulfilment_Method]` (`Amazon` vs `Merchant`).
5. **Customer Segment Slicer**:
   - Field: `dim_customers[Customer_Segment]` (`VIP Platinum`, `Loyal Gold`, `Regular Silver`, `Occasional Bronze`, `B2B Wholesale`).
