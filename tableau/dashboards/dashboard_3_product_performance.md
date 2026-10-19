# Tableau Dashboard 3: Product & Inventory Performance

## 1. Business Objective
Evaluate product SKU performance, merchandise categories, sizing demand distribution, and identify both top-grossing star products and low-performing inventory tail items requiring promotional markdown or delisting.

---

## 2. Calculated Fields in Tableau

```tableau
// 1. Average Selling Price Per Unit
SUM([Net Realized Revenue]) / SUM([Quantity])

// 2. Product Revenue Contribution %
SUM([Net Realized Revenue]) / TOTAL(SUM([Net Realized Revenue])) * 100

// 3. Performance Classification
IF [Product Revenue Rank] <= 10 THEN "Star Performer (Top 10)"
ELSEIF [Product Revenue Rank] <= 30 THEN "Core Performer"
ELSE "Underperforming Tail"
END
```

---

## 3. Visual Layout & Component Matrix

| Visual Component | Chart Type | Dimensions (Rows/Columns) | Measures (Marks) | Insights & Interactivity |
| :--- | :--- | :--- | :--- | :--- |
| **Category Matrix** | Heatmap Matrix | Rows: `Category`<br>Columns: `Size` | Color: `SUM(Quantity Sold)`<br>Label: `SUM(Net Revenue)` | Highlights highest-demand size curves (M, L, XL drive 50.5% of apparel volume) |
| **Top 10 vs Bottom 10 SKUs** | Diverging / Paired Bar Chart | Rows: `Product Name`<br>Columns: `SUM(Net Revenue)` | Color: `Performance Classification` | Juxtaposes star items (T-shirt M: INR 7.82M) against bottom items (Watch: INR 610) |
| **Price vs Volume Matrix** | Scatter Plot (Bubble) | Columns: `Average Selling Price`<br>Rows: `Total Units Sold` | Size: `SUM(Net Revenue)`<br>Color: `Category` | Identifies high-volume/low-price vs low-volume/high-price product positioning |
| **Gross Profit Margin by Category** | Bullet Graph / Bar Chart | Rows: `Category`<br>Columns: `Gross Profit Margin %` | Reference Line: Target Margin (35%) | Evaluates category gross profitability contributions |

---

## 4. Key Business Questions Answered
1. Which products and apparel sizes generate 80% of company sales?
2. Which categories have high unit sales but lower price points?
3. Which product lines suffer from zero/low traction and should be phased out?
4. What is the optimal inventory allocation across apparel sizes (S, M, L, XL, XXL)?
