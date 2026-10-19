# Tableau Dashboard 1: Executive Sales Overview

## 1. Business Objective
Provide executive leadership and stakeholders with an immediate, high-level pulse of overall e-commerce commercial performance, revenue trends, top revenue drivers, and fulfillment efficiency.

---

## 2. Calculated Fields in Tableau

```tableau
// 1. Net Realized Revenue
IF [Order Status Group] = "Delivered" OR [Order Status Group] = "Shipped" THEN
    [Gross Amount]
ELSE
    0
END

// 2. Average Order Value (AOV)
SUM([Net Realized Revenue]) / COUNTD([Order ID])

// 3. Gross Profit
SUM([Net Realized Revenue]) - SUM([COGS])

// 4. Delivery Rate %
COUNTD(IF [Order Status Group] = "Delivered" THEN [Order ID] END) / COUNTD([Order ID]) * 100

// 5. Cancellation Rate %
COUNTD(IF [Order Status Group] = "Cancelled" THEN [Order ID] END) / COUNTD([Order ID]) * 100
```

---

## 3. Visual Layout & Component Matrix

| Visual Component | Chart Type | Dimensions (Rows/Columns) | Measures (Marks) | Interactive Action |
| :--- | :--- | :--- | :--- | :--- |
| **KPI Banner** | Custom KPI Text Cards | 5 BAN Cards | `Net Revenue` (INR 69.39M), `Total Orders` (120,229), `AOV` (INR 577.17), `Gross Profit` (INR 24.28M), `Fulfillment %` (83.5%) | Global Highlight |
| **Sales Trend** | Dual-Axis Line & Bar | Columns: `MONTH(Order Date)`<br>Rows: `SUM(Net Revenue)` & `COUNTD(Order ID)` | Line: Net Revenue<br>Bar: Order Volume | Click Month to cross-filter entire dashboard |
| **Category Share** | Donut / Treemap | Marks: `Category` | Size/Angle: `SUM(Net Revenue)`<br>Color: `Category` | Click Category to filter Products & Map |
| **Top 10 Products** | Horizontal Bar Chart | Rows: `Product Name` (Top 10 by Net Revenue)<br>Columns: `SUM(Net Revenue)` | Color: `Gross Profit Margin %`<br>Label: `SUM(Net Revenue)` | Hover tooltip displays Units Sold & Category |
| **Geographic Map** | Symbol / Filled Map | Latitude / Longitude of `State` | Size: `SUM(Net Revenue)`<br>Color: `SUM(Net Revenue)` | Click State to zoom and filter regional KPIs |

---

## 4. Key Interactive Filters & Slicers
* **Date Range Slider**: Continuous range from March 31, 2022 to June 29, 2022.
* **Category Dropdown**: Multi-select filter for all 9 categories.
* **Fulfillment Channel**: Single-select toggle (`All`, `Amazon FBA`, `Merchant Easy Ship`).
* **Customer Segment**: Filter for B2B vs Retail customer tiers.
