# Project Overview: End-to-End E-Commerce Data Analytics

## 1. Project Mission & Objectives
This project upgrades an existing Node.js & MongoDB e-commerce order tracker into a **full-stack, end-to-end Data Analytics project**. It bridges the gap between software engineering, transactional database architecture, business intelligence, and executive data storytelling.

### Core Business Objective:
> **Analyze customer purchases, sales, products, order behavior, and revenue to understand what is happening in the business, identify important patterns, and provide actionable recommendations to improve sales, customer retention, product performance, and overall business growth.**

---

## 2. End-to-End Analytics Workflow

```
[ 1. Raw Dataset (Kaggle Amazon Sales) ]
       ↓
[ 2. Excel & Python Data Cleaning & Validation ]
       ↓
[ 3. Dimensional Modeling (Star Schema: Dim & Fact Tables) ]
       ↓
[ 4. MongoDB Atlas (Collections, Compound Indexes, Aggregation Pipelines) ]
       ↓
[ 5. Power BI (Data Modeling, Relationships, 35+ DAX Measures, KPIs) ]
       ↓
[ 6. Tableau (4 Interactive Story Dashboards & Visual Storytelling) ]
       ↓
[ 7. Business Insights (4-Stage Framework: Observation → Reason → Impact → Action) ]
       ↓
[ 8. Strategic Executive Recommendations ]
```

---

## 3. Technology Stack & Tool Matrix

| Layer / Skill | Tool / Technology | Specific Role in Project |
| :--- | :--- | :--- |
| **Data Cleaning** | **Microsoft Excel & Python (Pandas)** | Missing value imputation, deduplication, state standardization, type casting, calculated columns |
| **Database** | **MongoDB Atlas / MongoDB Driver** | Document storage, compound indexing, 10+ analytical aggregation pipelines |
| **Application / API** | **Node.js & Express.js** | RESTful API server exposing analytical aggregations & order tracking CRUD |
| **Data Modeling** | **Power BI Desktop & DAX** | Star schema architecture, 1-to-many relationships, dynamic DAX measures, time-intelligence |
| **Visualization** | **Tableau Desktop / Tableau Public** | Interactive executive sales overview, customer RFM segmentation, product matrix, logistics diagnostics |
| **Modeling Format** | **Star Schema (Kimball Methodology)** | `fact_orders`, `dim_customers`, `dim_products`, `dim_dates` |

---

## 4. Key Metrics Summary

* **Analyzed Orders**: 120,229 distinct orders (128,017 transaction lines)
* **Net Realized Revenue**: INR 69,392,224.00
* **Gross Merchandise Value (GMV)**: INR 78,278,727.88
* **Gross Profit**: INR 24,287,278.40 (35.00% Margin)
* **Unique Customers**: 14,813 accounts
* **Average Order Value (AOV)**: INR 577.17
* **Delivery Fulfillment Rate**: 83.53%
* **Order Cancellation Rate**: 14.10% (INR 6.89M GMV lost)
