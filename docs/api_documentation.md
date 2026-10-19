# E-Commerce Order Management & Tracking API — Documentation

## Overview

The **E-Commerce Order Management & Tracking API** is a production-grade RESTful service built with **Node.js**, **Express.js**, and **MongoDB**. It provides full-lifecycle order management, schema validation, state-machine status progression, multi-criteria filtering, pagination, sorting, soft/hard deletion policies, and MongoDB-backed analytics.

---

## Base URL & Environment Configuration

- **Local Base URL:** `http://localhost:5000`
- **Configuration (`server/.env`):**
  ```env
  PORT=5000
  MONGO_URI=mongodb://localhost:27017
  DB_NAME=ecommerce_analytics_db
  ```

---

## Order Status State Machine

Orders follow strict lifecycle transition rules to prevent invalid operational states (e.g., cancelled orders cannot be delivered):

```
       +------------+
       |  Pending   |
       +-----+------+
             |
      +------+------+
      |             |
      v             v
+-----------+  +-----------+
|  Shipped  |  | Cancelled | (Terminal)
+-----+-----+  +-----------+
      |
  +---+---+
  |       |
  v       v
+-----------+  +-----------+
| Delivered |  | Returned  | (Terminal)
+-----+-----+  +-----------+
      |
      v
+-----------+
| Returned  | (Terminal)
+-----------+
```

| Current Status | Permitted Target Statuses | Notes |
|---|---|---|
| `Pending` | `Shipped`, `Cancelled` | Initial state upon creation. |
| `Shipped` | `Delivered`, `Returned`, `Cancelled` | Package in transit. |
| `Delivered` | `Returned` | Successfully delivered to buyer. |
| `Cancelled` | *(None — Terminal)* | Realized revenue (`Net_Sales`) set to 0.0. |
| `Returned` | *(None — Terminal)* | Return processed; realized revenue set to 0.0. |

---

## API Endpoints Reference

### 1. Health Check

#### `GET /health` or `GET /api/health`
Returns service availability and connected database identifier without leaking passwords or secrets.

- **Response (200 OK):**
  ```json
  {
    "status": "online",
    "service": "E-Commerce Order Management & Tracking API",
    "database": "ecommerce_analytics_db",
    "timestamp": "2026-10-19T14:30:00.000Z"
  }
  ```
- **Response when DB disconnected (200 OK):**
  ```json
  {
    "status": "database_unavailable",
    "service": "E-Commerce Order Management & Tracking API",
    "database": "ecommerce_analytics_db",
    "timestamp": "2026-10-19T14:30:00.000Z"
  }
  ```

---

### 2. Create Order

#### `POST /api/orders`
Creates a new order item record. Automatically generates a unique `order_item_id` (`ITEM-${uuid}`) and timestamps.

- **Headers:** `Content-Type: application/json`
- **Request Body:**
  ```json
  {
    "order_id": "ORD-2024-9901",
    "customer_id": "CUST-4819",
    "product_id": "PROD-TSH-L",
    "quantity": 2,
    "unit_price": 450.0,
    "order_status_group": "Pending",
    "fulfilment_method": "Amazon",
    "ship_city": "Bengaluru",
    "ship_state": "Karnataka",
    "region": "South",
    "is_b2b": false
  }
  ```
- **Validation Rules:**
  - `order_id`: Required string (1-200 chars).
  - `customer_id`: Required string (1-200 chars).
  - `product_id`: Required string (1-200 chars).
  - `quantity`: Required positive integer (`>= 1`).
  - `unit_price`: Finite non-negative number (`>= 0`).
  - Auto-calculated: `gross_amount = unit_price * quantity`, `net_sales` (set to 0 for non-sales statuses).
- **Response (201 Created):**
  ```json
  {
    "success": true,
    "message": "Order created successfully.",
    "data": {
      "_id": "6713a0...",
      "order_item_id": "ITEM-c4b8-...",
      "order_id": "ORD-2024-9901",
      "customer_id": "CUST-4819",
      "product_id": "PROD-TSH-L",
      "quantity": 2,
      "unit_price": 450.0,
      "gross_amount": 900.0,
      "net_sales": 0.0,
      "order_status_group": "Pending",
      "is_deleted": false,
      "created_at": "2026-10-19T14:30:00.000Z",
      "updated_at": "2026-10-19T14:30:00.000Z"
    }
  }
  ```

---

### 3. List & Search Orders

#### `GET /api/orders`
Retrieves a paginated list of orders with sorting and multi-criteria filters. Excludes soft-deleted records.

- **Query Parameters:**
  | Parameter | Type | Default | Description |
  |---|---|---|---|
  | `page` | Integer | `1` | Page number (`1` to `1,000,000`). |
  | `limit` | Integer | `20` | Page size (`1` to `500`). |
  | `sortBy` | String | `order_date` | Permitted: `order_date`, `gross_amount`, `net_sales`, `quantity`, `order_id`, `created_at`. |
  | `order` | String | `desc` | Sort direction: `asc` or `desc`. |
  | `status` | String | — | Filter by `order_status_group` (e.g. `Delivered`, `Shipped`). |
  | `region` | String | — | Filter by region (`North`, `South`, `East`, `West`, `Central`). |
  | `customerId` | String | — | Filter by exact customer ID. |
  | `productId` | String | — | Filter by exact product SKU. |
  | `city` | String | — | Case-insensitive match on shipping city. |
  | `courier` | String | — | Filter by `courier_status`. |
  | `search` | String | — | Substring search across `order_id`, `product_id`, and `customer_id`. |
  | `startDate` | ISO Date | — | Lower bound date (`YYYY-MM-DD`). |
  | `endDate` | ISO Date | — | Upper bound date (`YYYY-MM-DD`). |

- **Example Request:**
  `GET /api/orders?page=1&limit=10&status=Delivered&region=South&sortBy=gross_amount&order=desc`

- **Response (200 OK):**
  ```json
  {
    "success": true,
    "pagination": {
      "page": 1,
      "limit": 10,
      "total": 5420,
      "total_pages": 542,
      "count": 10
    },
    "data": [
      {
        "_id": "6713a...",
        "order_item_id": "ITEM-101",
        "order_id": "ORD-001",
        "customer_id": "CUST-001",
        "product_id": "PROD-TSH-XL",
        "order_date": "2024-03-01",
        "order_status_group": "Delivered",
        "quantity": 3,
        "gross_amount": 1350.0,
        "net_sales": 1350.0,
        "region": "South"
      }
    ]
  }
  ```

---

### 4. Get Single Order Detail

#### `GET /api/orders/:orderId`
Looks up an active order by either `order_id` or `order_item_id`.

- **Response (200 OK):**
  ```json
  {
    "success": true,
    "data": {
      "_id": "6713a...",
      "order_id": "ORD-001",
      "order_item_id": "ITEM-101",
      "customer_id": "CUST-001",
      "product_id": "PROD-TSH-XL",
      "quantity": 3,
      "net_sales": 1350.0,
      "order_status_group": "Delivered"
    }
  }
  ```
- **Response if not found (404 Not Found):**
  ```json
  {
    "success": false,
    "error": "Order 'UNKNOWN-ID' was not found.",
    "message": "Order not found"
  }
  ```

---

### 5. Partial Update Order

#### `PATCH /api/orders/:orderId`
Updates mutable attributes of an order. Recalculates financial fields if quantity or unit price is changed.

- **Protected Immutable Fields:** `_id`, `order_item_id`, `created_at`, `is_deleted`. Attempting to modify these returns HTTP 400.
- **Request Body:**
  ```json
  {
    "quantity": 4,
    "unit_price": 400.0,
    "ship_city": "Mysuru"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "success": true,
    "message": "Order updated successfully.",
    "data": { ... }
  }
  ```

---

### 6. Update Order Status

#### `PATCH /api/orders/:orderId/status`
Advances an order along its verified lifecycle path.

- **Request Body:**
  ```json
  {
    "status": "Shipped"
  }
  ```
- **Valid Transition Example (`Pending` -> `Shipped`):**
  - Response (200 OK): status updated, `courier_status` updated to `Shipped`.
- **Invalid Transition Example (`Cancelled` -> `Delivered`):**
  - Response (400 Bad Request):
    ```json
    {
      "success": false,
      "error": "Cannot transition order status from 'Cancelled' to 'Delivered'. Allowed transitions: none (terminal state)."
    }
    ```

---

### 7. Delete Order (Soft vs Hard Deletion)

#### `DELETE /api/orders/:orderId`
- **Default Policy (Soft Delete):** Sets `is_deleted: true` and records `deleted_at: timestamp`. Order is hidden from list queries and single lookups, preserving financial audit trail.
- **Permanent Purge:** Append `?hard=true` (e.g. `DELETE /api/orders/:orderId?hard=true`). Permanently removes record from MongoDB.
- **Response (200 OK):**
  ```json
  {
    "success": true,
    "message": "Order deleted successfully (soft-deleted).",
    "data": {
      "deleted": true,
      "order_id": "ORD-001",
      "hard": false
    }
  }
  ```

---

## Error Handling Standards

All error responses adhere to standard JSON error formatting:

```json
{
  "success": false,
  "error": "Descriptive client error message."
}
```

| HTTP Status | Condition | Example |
|---|---|---|
| `400 Bad Request` | Validation failure, boundary violation, invalid status transition, malformed JSON. | `quantity must be a positive integer.` |
| `404 Not Found` | Target order does not exist or has been soft-deleted. | `Order 'ORD-999' was not found.` |
| `409 Conflict` | Unique identifier conflict (e.g. duplicate primary key). | `Order item with ID 'ITEM-X' already exists.` |
| `503 Service Unavailable` | MongoDB instance unreachable or disconnected. | `Database is not connected.` |
| `500 Internal Server Error` | Uncaught server exception; stack trace hidden. | `Internal server error.` |
