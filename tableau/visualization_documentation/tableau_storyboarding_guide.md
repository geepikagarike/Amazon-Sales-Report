# Tableau Storyboarding & Visualization Guide

## 1. Connecting Tableau to the Analytical Dataset

### Step 1: Connect to MongoDB / Exported Star Schema
1. Open Tableau Desktop / Tableau Public.
2. Under **Connect** -> **To a Server**, choose **MongoDB BI Connector** (or connect directly to `data/cleaned/fact_orders.csv` under **To a File** -> **Text File**).
3. Set up relationships / joins between:
   - `fact_orders.Customer_ID` = `dim_customers.Customer_ID`
   - `fact_orders.Product_ID` = `dim_products.Product_ID`
   - `fact_orders.Order_Date` = `dim_dates.Date_ISO`

---

## 2. Storyboard Navigation & Flow

A professional data analytics presentation in Tableau should be organized into a cohesive **5-Story Story Point Narrative**:

```
[ Story Point 1: Executive Sales Overview ]
       ↓
[ Story Point 2: Customer Segmentation & CLV Concentration ]
       ↓
[ Story Point 3: Product Performance & Category 80/20 Rule ]
       ↓
[ Story Point 4: Logistics, Fulfillment & Cancellation Analysis ]
       ↓
[ Story Point 5: Actionable Business Recommendations & Growth Strategy ]
```

---

## 3. Formatting & Aesthetic Standards

* **Dashboard Sizing**: Fixed 1366 × 768 px (Standard Laptop) or Automatic.
* **Color Hierarchy**:
  - Main Data Marks: Deep Blue `#1F4E78`
  - Highlighting / Callouts: Amber `#ED7D31`
  - Positive Trends: Forest Green `#548235`
  - Alerts / Drop-offs: Coral Red `#C00000`
* **Typography**:
  - Title: Tableau Bold, 16pt, `#1F4E78`
  - Subtitle: Tableau Book, 10pt, `#595959`
  - Chart Headers: Tableau Medium, 12pt, `#262626`
  - Tooltips: Formatted with bold metric labels and clean number formatting (`INR <SUM(Net Revenue)>`).
