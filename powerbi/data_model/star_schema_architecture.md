# Power BI Star Schema Data Model Architecture

## 1. Architectural Overview

The analytical data model implements a **Kimball-style dimensional Star Schema** optimized for analytical reporting, aggregation speed, and enterprise scalability in Power BI.

The model segregates **business events (Transactions/Orders)** from **contextual entities (Customers, Products, Dates, Geography)**.

```mermaid
erDiagram
    dim_customers ||--o{ fact_orders : "Customer_ID (1 to Many)"
    dim_products ||--o{ fact_orders : "Product_ID (1 to Many)"
    dim_dates ||--o{ fact_orders : "Order_Date -> Date_ISO (1 to Many)"

    dim_customers {
        string Customer_ID PK
        string Customer_Name
        string Customer_Segment
        boolean Is_B2B
        string City
        string State
        string Region
        int Postal_Code
        int Total_Orders
        float Total_Spend
        date First_Order_Date
        date Last_Order_Date
    }

    dim_products {
        string Product_ID PK
        string Product_Name
        string Category
        string Size
        float Unit_MSRP
        float Unit_Cost
        int Total_Units_Sold
        float Gross_Revenue
        float Net_Revenue
    }

    dim_dates {
        int Date_Key PK
        date Date_ISO
        int Year
        string Quarter
        int Month_Number
        string Month_Name
        string Year_Month
        int Day_Of_Month
        string Day_Of_Week
        boolean Is_Weekend
    }

    fact_orders {
        string Order_Item_ID PK
        string Order_ID
        string Customer_ID FK
        string Product_ID FK
        date Order_Date FK
        string Order_Status
        string Order_Status_Group
        string Courier_Status
        string Fulfilment_Method
        string Fulfilled_By
        string Sales_Channel
        string Ship_Service_Level
        int Quantity
        float Unit_Price
        float Gross_Amount
        float Net_Sales
        float COGS
        float Gross_Profit
        float Profit_Margin_Pct
        boolean Is_B2B
        string Ship_City
        string Ship_State
        string Region
        int Ship_Postal_Code
        boolean Is_New_Record
    }
```

---

## 2. Table Specifications & Cardinalities

| From Table (Dimension) | Key Column | To Table (Fact) | Foreign Key Column | Cardinality | Cross-Filter Direction | Relationship Type |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`dim_customers`** | `Customer_ID` | **`fact_orders`** | `Customer_ID` | 1 to Many (`1:*`) | Single (Dim filters Fact) | Active |
| **`dim_products`** | `Product_ID` | **`fact_orders`** | `Product_ID` | 1 to Many (`1:*`) | Single (Dim filters Fact) | Active |
| **`dim_dates`** | `Date_ISO` | **`fact_orders`** | `Order_Date` | 1 to Many (`1:*`) | Single (Dim filters Fact) | Active |

---

## 3. Design Principles & Best Practices Applied

1. **Strict 1:Many Relationships**: Eliminates ambiguous many-to-many paths, avoiding Cartesian product inflation and performance bottlenecks.
2. **Single Direction Filtering**: All filters flow unidirectionally from Dimension tables to Fact tables, preventing circular filter dependencies.
3. **Surrogate Keys**: Tables are joined on lightweight, clean surrogate keys (`Customer_ID`, `Product_ID`, `Date_ISO`).
4. **Separation of Concerns**:
   - `fact_orders` holds all quantitative additive measures (`Quantity`, `Gross_Amount`, `Net_Sales`, `COGS`, `Gross_Profit`).
   - Dimension tables hold qualitative attributes for slicing, dicing, and grouping.
5. **Marked Date Table**: `dim_dates` is designated as the official Date Table in Power BI, enabling accurate time-intelligence DAX functions (`SAMEPERIODLASTYEAR`, `DATESMTD`, `DATEADD`).
