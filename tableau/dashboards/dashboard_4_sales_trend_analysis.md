# Tableau Dashboard 4: Sales Trend & Logistics Analysis

## 1. Business Objective
Track multi-month sales trajectories, weekday/weekend purchasing patterns, fulfillment efficiency (Amazon FBA vs Merchant Easy Ship), and cancellation/return rates across geographic regions.

---

## 2. Calculated Fields in Tableau

```tableau
// 1. Day of Week Order Distribution
DATEPART('weekday', [Order Date])

// 2. Cancellation Impact INR
SUM(IF [Order Status Group] = "Cancelled" THEN [Gross Amount] ELSE 0 END)

// 3. FBA Revenue Share %
SUM(IF [Fulfilment Method] = "Amazon" THEN [Net Realized Revenue] ELSE 0 END) / SUM([Net Realized Revenue]) * 100
```

---

## 3. Visual Layout & Component Matrix

| Visual Component | Chart Type | Dimensions (Rows/Columns) | Measures (Marks) | Insights & Interactivity |
| :--- | :--- | :--- | :--- | :--- |
| **Weekly / Daily Sales Trajectory** | Continuous Area Chart | Columns: `DAY(Order Date)`<br>Rows: `SUM(Net Revenue)` | Detail: `Fulfilment Method`<br>Color: Fulfilment Channel | Visualizes daily order volatility and revenue peaks |
| **Day of Week Heatmap** | Highlight Table / Heatmap | Rows: `Day Of Week`<br>Columns: `Category` | Color: `COUNTD(Order ID)` | Identifies high-traffic shopping days (Weekends & Wednesdays) |
| **Fulfillment Funnel & Loss Analysis** | Stacked Bar Chart | Rows: `Region`<br>Columns: `SUM(Gross Amount)` | Color: `Order Status Group` (Delivered, Shipped, Cancelled, Returned) | Displays INR 6.89M GMV lost to cancellations across regions |
| **Fulfillment Channel Speed Comparison** | Box & Whisker / Bar Chart | Rows: `Fulfilment Method`<br>Columns: `Fulfillment Success Rate %` | Detail: `Courier Status` | Demonstrates higher customer delivery success rate for Amazon FBA |

---

## 4. Key Business Questions Answered
1. What are the seasonal peaks and month-over-month sales trends?
2. Which days of the week experience the highest checkout conversion?
3. How much revenue is lost to pre-delivery order cancellations?
4. How significantly does Amazon FBA outperform Merchant fulfillment in delivery rate?
