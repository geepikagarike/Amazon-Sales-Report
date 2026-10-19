# Database Schema & Indexing Architecture

## 1. Overview & Data Model Design

The **E-Commerce Order Management & Tracking API** utilizes MongoDB for flexible, high-throughput transactional order tracking and analytics. The schema represents individual order line items (`order_item_id` as primary unique key) linked to parent order transactions (`order_id`).

### Historical CSV Grain vs Managed API Record

| Attribute | Historical Cleaned CSV Grain | Managed API Order Record |
|---|---|---|
| **Primary Key** | `Order_Item_ID` (e.g. `ITEM-001`) | `order_item_id` (Unique string index) |
| **Parent Transaction** | `Order_ID` (may encompass multiple items) | `order_id` (Indexed for order group lookup) |
| **Lifecycle State** | Static snapshot (`Delivered`, `Shipped`, etc.) | Dynamic state-machine (`Pending` -> `Shipped` -> `Delivered`/`Returned`) |
| **Audit Timestamps** | Static calendar date (`Order_Date`) | `created_at` (creation) & `updated_at` (last modification) |
| **Deletion Model** | Hard deletion / absent records | Safe soft-deletion (`is_deleted: true`, `deleted_at`) |

---

## 2. Order Collection Schema (`orders`)

| Field Name | BSON Type | Required | Default | Description |
|---|---|:---:|---|---|
| `_id` | `ObjectId` | Yes | Auto | MongoDB internal document identifier. |
| `order_item_id` | `string` | Yes | `ITEM-${uuid}` | Unique business identifier for the order item. Unique index. |
| `order_id` | `string` | Yes | — | Parent order identifier. Indexed. |
| `customer_id` | `string` | Yes | — | Customer identifier. Indexed. |
| `product_id` | `string` | Yes | — | Product SKU identifier. Indexed. |
| `order_date` | `date` / `string` | Yes | Current Date | Transaction date in ISO format (`YYYY-MM-DD`). |
| `order_status` | `string` | Yes | `Pending` | Operational status description (e.g., `Shipped - In Transit`). |
| `order_status_group` | `string` | Yes | `Pending` | High-level status group (`Pending`, `Shipped`, `Delivered`, `Cancelled`, `Returned`). |
| `courier_status` | `string` | No | `Pending` | Carrier fulfillment progress. |
| `fulfilment_method` | `string` | No | `Amazon` | Channel (`Amazon` FBA or `Merchant`). |
| `fulfilled_by` | `string` | No | `null` | Specific fulfillment entity (e.g., `Amazon FBA`, `Easy Ship`). |
| `sales_channel` | `string` | No | `Amazon.in` | Sales portal. |
| `ship_service_level` | `string` | No | `Standard` | Delivery priority. |
| `quantity` | `int` | Yes | `1` | Ordered units (`>= 0`). |
| `unit_price` | `double` | No | `0.0` | Item price in INR. |
| `gross_amount` | `double` | No | `0.0` | Total transaction value (`unit_price * quantity`). |
| `net_sales` | `double` | No | `0.0` | Realized revenue (retained for `Delivered`/`Shipped`, 0 for `Cancelled`). |
| `cogs` | `double` | No | `0.0` | Cost of Goods Sold. |
| `gross_profit` | `double` | No | `0.0` | Gross profit margin amount. |
| `profit_margin_pct` | `double` | No | `0.0` | Margin percentage (0-100). |
| `is_b2b` | `bool` | No | `false` | B2B business transaction flag. |
| `ship_city` | `string` | No | `null` | Delivery destination city. |
| `ship_state` | `string` | No | `null` | Delivery destination state. |
| `region` | `string` | No | `null` | Geographic region (`North`, `South`, `East`, `West`, `Central`). |
| `ship_postal_code` | `int` | No | `null` | 6-digit postal code. |
| `is_deleted` | `bool` | Yes | `false` | Soft-deletion audit flag. |
| `deleted_at` | `date` | No | `null` | Timestamp when record was soft-deleted. |
| `created_at` | `date` | Yes | Auto | Record creation timestamp. |
| `updated_at` | `date` | Yes | Auto | Last modification timestamp. |

---

## 3. Index Architecture & Query Optimization

Indexes are aligned directly with high-frequency API query patterns:

```javascript
// 1. Primary Lookups & Uniqueness
db.orders.createIndex({ order_item_id: 1 }, { unique: true, name: "idx_order_item_id" });
db.orders.createIndex({ order_id: 1 }, { name: "idx_order_id" });

// 2. Foreign Key References
db.orders.createIndex({ customer_id: 1 }, { name: "idx_customer_id" });
db.orders.createIndex({ product_id: 1 }, { name: "idx_product_id" });

// 3. Chronological Sorting & Date Range Filtering
db.orders.createIndex({ order_date: -1 }, { name: "idx_order_date_desc" });

// 4. Status Filtering & Active Soft-Delete Queries
db.orders.createIndex({ is_deleted: 1, order_status_group: 1 }, { name: "idx_active_status" });
db.orders.createIndex({ is_deleted: 1, order_date: -1 }, { name: "idx_active_orders_date" });

// 5. Geographic & Logistics Lookups
db.orders.createIndex({ ship_city: 1 }, { name: "idx_ship_city" });
db.orders.createIndex({ courier_status: 1 }, { name: "idx_courier_status" });
```

### Performance Impact:
- **`idx_order_item_id`:** Enforces O(1) primary key uniqueness and fast single-record retrieval.
- **`idx_order_id`:** Enables sub-millisecond retrieval of all item lines belonging to an order.
- **`idx_active_orders_date`:** Satisfies `GET /api/orders` pagination queries with index-covered sorting, eliminating in-memory MongoDB sort operations (`Sort key: order_date: -1`).
- **`idx_active_status`:** Optimizes status funnel filtering for high-concurrency dashboards and analytical requests.

---

## 4. Complementary Collections in the Star Schema

For cross-functional reporting and BI analytics:
1. **`customers`:** Primary key `customer_id` (`idx_cust_id_pk`). Stores customer segment, total lifetime spend, order count.
2. **`products`:** Primary key `product_id` (`idx_prod_id_pk`). Stores product title, category, size, MSRP, revenue.
3. **`dates`:** Primary key `date_key` (`idx_date_key_pk`). Calendar dimension with ISO date, month name, quarter, weekend indicator.
