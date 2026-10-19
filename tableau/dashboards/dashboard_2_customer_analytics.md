# Tableau Dashboard 2: Customer Analytics & Purchasing Behavior

## 1. Business Objective
Deep-dive into customer segmentation, spending behavior, customer lifetime value (CLV), purchase frequency, and revenue concentration to uncover high-value buyers and retention opportunities.

---

## 2. Calculated Fields in Tableau

```tableau
// 1. Customer Spending Tier
IF [Total Spend] >= 5000 THEN "VIP Platinum"
ELSEIF [Total Spend] >= 2000 THEN "Loyal Gold"
ELSEIF [Total Spend] >= 800 THEN "Regular Silver"
ELSE "Occasional Bronze"
END

// 2. Repeat Customer Flag
IF [Total Orders] > 1 THEN "Repeat Customer"
ELSE "One-Time Buyer"
END

// 3. Customer Revenue Contribution %
SUM([Net Revenue]) / TOTAL(SUM([Net Revenue])) * 100
```

---

## 3. Visual Layout & Component Matrix

| Visual Component | Chart Type | Dimensions (Rows/Columns) | Measures (Marks) | Insights & Interactivity |
| :--- | :--- | :--- | :--- | :--- |
| **Customer Segment Split** | Packed Bubble / Treemap | Marks: `Customer Segment` | Size: `SUM(Total Spend)`<br>Color: `Customer Segment`<br>Label: Segment, Count, % Rev | Shows that **VIP Platinum** (16.1% of accounts) generates **78.93%** of revenue |
| **Top Customers Ranking** | Horizontal Bar Chart with Ranking | Rows: `Customer Name` (Top 15)<br>Columns: `SUM(Total Spend)` | Color: `Customer Segment`<br>Detail: `City, State` | Identifies specific high-net-worth customer accounts |
| **Order Frequency Distribution** | Histogram / Column Chart | Columns: `Total Orders` (1, 2, 3, 4, 5+)<br>Rows: `COUNTD(Customer ID)` | Color: `Repeat Customer Flag` | Visualizes conversion from 1-time buyer to repeat buyer |
| **Customer CLV vs Orders Matrix** | Scatter Plot | Columns: `Total Orders`<br>Rows: `Average Spend Per Order` | Circle Size: `Total Lifetime Spend`<br>Color: `Customer Segment` | Quadrant analysis: High Value / High Frequency vs High Value / Low Frequency |
| **B2B Wholesale Contribution** | Donut Chart | Marks: `Is B2B` | Angle: `SUM(Net Revenue)`<br>Color: `Is B2B` | Evaluates enterprise wholesale channel performance |

---

## 4. Key Business Questions Answered
1. Who are our top 10 highest-value customers, and where are they located?
2. What percentage of total revenue relies on our top customer segment?
3. How many customers are repeat purchasers vs one-time buyers?
4. Which customer groups are ideal candidates for VIP loyalty reward programs?
