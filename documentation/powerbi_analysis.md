# Power BI Data Modeling & Analytical Architecture

## 1. Architectural Role of Power BI
Power BI serves as the **Data Modeling, Calculation Engine, and Operational Dashboard layer**. It ingests the MongoDB-backed star-schema model, defines formal 1-to-many relationships, and calculates 35+ DAX measures.

---

## 2. Star Schema Modeling in Power BI

```
+-----------------------------------------------------------------------------------+
|                                 POWER BI DATA MODEL                               |
+-----------------------------------------------------------------------------------+
|  [ dim_customers ] (1)  ----<  ( * ) [ fact_orders ]  >----  (1) [ dim_products ] |
|  - Customer_ID (PK)                  - Customer_ID (FK)          - Product_ID (PK)|
|  - Customer_Name                     - Product_ID (FK)           - Category       |
|  - Customer_Segment                  - Order_Date (FK)           - Size           |
|                                            ^                                      |
|                                            | ( * )                                |
|                                            |                                      |
|                                     (1) [ dim_dates ]                             |
|                                     - Date_ISO (PK)                               |
|                                     - Month_Name, Quarter                         |
+-----------------------------------------------------------------------------------+
```

---

## 3. Core DAX Formulations

### A. Net Revenue & Profitability
```dax
Net Revenue = SUM(fact_orders[Net_Sales])

Total COGS = SUM(fact_orders[COGS])

Total Gross Profit = [Net Revenue] - [Total COGS]

Gross Profit Margin % = DIVIDE([Total Gross Profit], [Net Revenue], 0) * 100
```

### B. Time Intelligence & MoM Growth
```dax
Prior Month Net Revenue = 
CALCULATE([Net Revenue], PREVIOUSMONTH(dim_dates[Date_ISO]))

MoM Revenue Growth % = 
VAR CurrentRev = [Net Revenue]
VAR PriorRev = [Prior Month Net Revenue]
RETURN
    IF(ISBLANK(PriorRev) || PriorRev = 0, BLANK(), DIVIDE(CurrentRev - PriorRev, PriorRev, 0) * 100)
```

### C. Operational & Fulfillment KPIs
```dax
Delivery Success Rate % = 
DIVIDE(
    CALCULATE([Total Orders], fact_orders[Order_Status_Group] IN { "Delivered", "Shipped" }),
    [Total Orders],
    0
) * 100

Order Cancellation Rate % = 
DIVIDE(
    CALCULATE([Total Orders], fact_orders[Order_Status_Group] = "Cancelled"),
    [Total Orders],
    0
) * 100
```
