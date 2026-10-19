# Analytics API Reference

The Node/Express API reads the MongoDB collections and starts only when a MongoDB connection is available. Route tests use an in-memory mock database and do not validate live MongoDB availability or live aggregation results.

Base URL: `http://localhost:5000`

## Health

`GET /api/health`

Returns service status and configured database name. The database name is configuration metadata, not a MongoDB credential.

```json
{
  "status": "online",
  "service": "E-Commerce Data Analytics API",
  "database": "ecommerce_analytics_db",
  "timestamp": "<server-generated-ISO-timestamp>"
}
```

## Order listing

`GET /api/orders?page=1&limit=20&status=Delivered&region=South&customer_id=<customer-id>`

- `page`: optional positive integer, default `1`, maximum `1000000`.
- `limit`: optional positive integer, default `20`, maximum `500`.
- `status`, `region`, `customer_id`: optional exact-match string filters (up to 100 characters).

Response shape:

```json
{
  "success": true,
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 0,
    "total_pages": 0
  },
  "data": []
}
```

The numeric values above illustrate the empty-response shape and are not a claim about a live database result.

## Order lookup

`GET /api/orders/:id` looks up the first order-line document whose `order_id` equals `:id`. It returns `404` with `{"success":false,"message":"Order not found"}` when no matching line exists.

## Add an order line

`POST /api/orders`

Required JSON fields:
- `order_id`, `customer_id`, `product_id`: non-empty strings.
- `quantity`: positive integer.

Optional fields use the actual Mongo/ETL schema: status, fulfillment, channel, amount/profit, B2B, and shipping fields. Monetary values, when provided, must be finite non-negative numbers. Server-generated `order_item_id`, `order_date`, and `is_new_record` values cannot be supplied by the caller.

Example request:

```json
{
  "order_id": "<order-id>",
  "customer_id": "<customer-id>",
  "product_id": "<product-id>",
  "quantity": 1,
  "order_status_group": "Pending"
}
```

The API does not calculate `Net_Sales` from client input. New records should be reconciled through the ETL/business rules before being treated as validated analytics facts.

## Analytics endpoints

All paths are `GET` routes and return `{ "success": true, "data": ... }`:

| Path | MongoDB source | Result |
|---|---|---|
| `/api/analytics/kpis` | `orders` | Executive KPI aggregation |
| `/api/analytics/monthly-sales` | `orders` | Monthly sales groups |
| `/api/analytics/category-performance` | `orders`, joined to `products` | Category totals |
| `/api/analytics/top-products` | `orders`, joined to `products` | Top products by sales |
| `/api/analytics/top-customers` | `orders`, joined to `customers` | Top customer rows |
| `/api/analytics/customer-segments` | `customers` | Customer segment totals |
| `/api/analytics/order-status` | `orders` | Order-line status totals |
| `/api/analytics/regional-sales` | `orders` | Region/state totals |
| `/api/analytics/fulfilment-analysis` | `orders` | Fulfillment-method totals |
| `/api/analytics/underperforming-products` | `orders`, joined to `products` | Bottom product rows |

Invalid query or body input returns HTTP `400`; database-not-connected responses return `503`; internal failures return a generic `500` body and do not expose database exception details.
