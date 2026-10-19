/**
 * Automated API Tests for Order Management & Tracking API
 * Tests complete CRUD lifecycle, state transitions, search/filtering, and deletion policies.
 * Runs completely offline using in-memory mock database.
 */

const assert = require('node:assert/strict');
const http = require('node:http');
const test = require('node:test');

const app = require('../server');

let server;
let baseUrl;
let mockOrders = [];

function buildMockDatabase() {
    return {
        collection(name) {
            if (name !== 'orders') {
                return {
                    countDocuments: async () => 0,
                    find: () => ({ toArray: async () => [] })
                };
            }

            return {
                async countDocuments(filter = {}) {
                    return filterOrders(mockOrders, filter).length;
                },
                find(filter = {}) {
                    let results = filterOrders(mockOrders, filter);
                    let sortKey = 'order_date';
                    let sortDirection = -1;

                    return {
                        sort(sortObj) {
                            const [key, dir] = Object.entries(sortObj)[0] || ['order_date', -1];
                            sortKey = key;
                            sortDirection = dir;
                            return this;
                        },
                        skip(skipVal) {
                            this.skipVal = skipVal;
                            return this;
                        },
                        limit(limitVal) {
                            this.limitVal = limitVal;
                            return this;
                        },
                        async toArray() {
                            results.sort((a, b) => {
                                const va = a[sortKey] || 0;
                                const vb = b[sortKey] || 0;
                                return va > vb ? sortDirection : va < vb ? -sortDirection : 0;
                            });
                            const skip = this.skipVal || 0;
                            const limit = this.limitVal || results.length;
                            return results.slice(skip, skip + limit);
                        }
                    };
                },
                async findOne(filter) {
                    const matches = filterOrders(mockOrders, filter);
                    return matches[0] || null;
                },
                async insertOne(doc) {
                    const inserted = { _id: `id-${Date.now()}-${Math.random()}`, ...doc };
                    mockOrders.push(inserted);
                    return { insertedId: inserted._id };
                },
                async findOneAndUpdate(filter, update, options) {
                    const order = await this.findOne(filter);
                    if (!order) return { value: null };
                    Object.assign(order, update.$set || {});
                    return { value: order };
                },
                async updateOne(filter, update) {
                    const order = await this.findOne(filter);
                    if (!order) return { matchedCount: 0, modifiedCount: 0 };
                    Object.assign(order, update.$set || {});
                    return { matchedCount: 1, modifiedCount: 1 };
                },
                async deleteOne(filter) {
                    const idx = mockOrders.findIndex(o => o.order_id === filter.order_id || o._id === filter._id);
                    if (idx === -1) return { deletedCount: 0 };
                    mockOrders.splice(idx, 1);
                    return { deletedCount: 1 };
                }
            };
        }
    };
}

function filterOrders(orders, filter = {}) {
    return orders.filter(order => {
        if (filter._id && order._id !== filter._id) return false;
        if (filter.is_deleted && filter.is_deleted.$ne === true) {
            if (order.is_deleted === true) return false;
        }
        if (filter.order_id && order.order_id !== filter.order_id) return false;
        if (filter.order_item_id && order.order_item_id !== filter.order_item_id) return false;
        if (filter.order_status_group && order.order_status_group !== filter.order_status_group) return false;
        if (filter.region && order.region !== filter.region) return false;
        if (filter.customer_id && order.customer_id !== filter.customer_id) return false;
        if (filter.product_id && order.product_id !== filter.product_id) return false;
        if (filter.$or) {
            const orMatch = filter.$or.some(clause => {
                if (clause.order_id && clause.order_id.$regex) {
                    return new RegExp(clause.order_id.$regex, clause.order_id.$options).test(order.order_id);
                }
                if (clause.order_id) return order.order_id === clause.order_id;
                if (clause.order_item_id) return order.order_item_id === clause.order_item_id;
                return false;
            });
            if (!orMatch) return false;
        }
        return true;
    });
}

test.before(async () => {
    mockOrders = [
        {
            _id: '1',
            order_id: 'ORD-101',
            order_item_id: 'ITEM-101',
            customer_id: 'CUST-001',
            product_id: 'PROD-A',
            order_date: '2024-03-01',
            order_status_group: 'Pending',
            quantity: 2,
            unit_price: 50.0,
            gross_amount: 100.0,
            net_sales: 0.0,
            region: 'North',
            is_deleted: false
        },
        {
            _id: '2',
            order_id: 'ORD-102',
            order_item_id: 'ITEM-102',
            customer_id: 'CUST-002',
            product_id: 'PROD-B',
            order_date: '2024-03-05',
            order_status_group: 'Shipped',
            quantity: 1,
            unit_price: 150.0,
            gross_amount: 150.0,
            net_sales: 150.0,
            region: 'South',
            is_deleted: false
        },
        {
            _id: '3',
            order_id: 'ORD-103',
            order_item_id: 'ITEM-103',
            customer_id: 'CUST-003',
            product_id: 'PROD-C',
            order_date: '2024-03-10',
            order_status_group: 'Cancelled',
            quantity: 4,
            unit_price: 25.0,
            gross_amount: 100.0,
            net_sales: 0.0,
            region: 'West',
            is_deleted: false
        }
    ];

    app.locals.db = buildMockDatabase();
    server = http.createServer(app);
    await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
    baseUrl = `http://127.0.0.1:${server.address().port}`;
});

test.after(async () => {
    await new Promise((resolve, reject) => {
        server.close((err) => (err ? reject(err) : resolve()));
    });
});

test('POST /api/orders creates a valid order with 201 status and generated order_item_id', async () => {
    const res = await fetch(`${baseUrl}/api/orders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            order_id: 'ORD-201',
            customer_id: 'CUST-100',
            product_id: 'PROD-Z',
            quantity: 3,
            unit_price: 40.0,
            order_status_group: 'Pending'
        })
    });

    assert.equal(res.status, 201);
    const body = await res.json();
    assert.equal(body.success, true);
    assert.equal(body.data.order_id, 'ORD-201');
    assert.equal(body.data.quantity, 3);
    assert.equal(body.data.gross_amount, 120.0);
    assert.ok(body.data.order_item_id.startsWith('ITEM-'));
    assert.equal(body.data.is_deleted, false);
});

test('GET /api/orders returns paginated order list with pagination metadata', async () => {
    const res = await fetch(`${baseUrl}/api/orders?page=1&limit=2`);
    assert.equal(res.status, 200);
    const body = await res.json();
    assert.equal(body.success, true);
    assert.equal(body.pagination.page, 1);
    assert.equal(body.pagination.limit, 2);
    assert.ok(body.pagination.total >= 3);
    assert.equal(body.data.length, 2);
});

test('GET /api/orders applies multi-criteria status and region filters', async () => {
    const res = await fetch(`${baseUrl}/api/orders?status=Shipped&region=South`);
    assert.equal(res.status, 200);
    const body = await res.json();
    assert.equal(body.success, true);
    assert.ok(body.data.every(o => o.order_status_group === 'Shipped' && o.region === 'South'));
});

test('GET /api/orders/:orderId returns single order detail by order_id or order_item_id', async () => {
    const byOrderId = await fetch(`${baseUrl}/api/orders/ORD-101`);
    assert.equal(byOrderId.status, 200);
    const body1 = await byOrderId.json();
    assert.equal(body1.data.order_id, 'ORD-101');

    const byItemId = await fetch(`${baseUrl}/api/orders/ITEM-102`);
    assert.equal(byItemId.status, 200);
    const body2 = await byItemId.json();
    assert.equal(body2.data.order_item_id, 'ITEM-102');
});

test('GET /api/orders/:orderId returns 404 for non-existent order', async () => {
    const res = await fetch(`${baseUrl}/api/orders/NON-EXISTENT-ID`);
    assert.equal(res.status, 404);
    const body = await res.json();
    assert.equal(body.success, false);
    assert.match(body.error, /not found/i);
});

test('PATCH /api/orders/:orderId updates mutable fields and recalculates amounts', async () => {
    const res = await fetch(`${baseUrl}/api/orders/ORD-101`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            quantity: 5,
            unit_price: 60.0
        })
    });

    assert.equal(res.status, 200);
    const body = await res.json();
    assert.equal(body.success, true);
    assert.equal(body.data.quantity, 5);
    assert.equal(body.data.gross_amount, 300.0);
});

test('PATCH /api/orders/:orderId rejects modifications to immutable fields', async () => {
    const res = await fetch(`${baseUrl}/api/orders/ORD-101`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            order_item_id: 'HACKED-ITEM-ID'
        })
    });

    assert.equal(res.status, 400);
    const body = await res.json();
    assert.equal(body.success, false);
    assert.match(body.error, /immutable/i);
});

test('PATCH /api/orders/:orderId/status allows permitted transition: Pending -> Shipped', async () => {
    const res = await fetch(`${baseUrl}/api/orders/ORD-101/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'Shipped' })
    });

    assert.equal(res.status, 200);
    const body = await res.json();
    assert.equal(body.success, true);
    assert.equal(body.data.order_status_group, 'Shipped');
    assert.equal(body.data.courier_status, 'Shipped');
});

test('PATCH /api/orders/:orderId/status rejects invalid transition from terminal Cancelled state', async () => {
    const res = await fetch(`${baseUrl}/api/orders/ORD-103/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'Delivered' })
    });

    assert.equal(res.status, 400);
    const body = await res.json();
    assert.equal(body.success, false);
    assert.match(body.error, /Cannot transition order status from 'Cancelled'/i);
});

test('DELETE /api/orders/:orderId performs soft-delete and subsequent lookup returns 404', async () => {
    const delRes = await fetch(`${baseUrl}/api/orders/ORD-102`, {
        method: 'DELETE'
    });
    assert.equal(delRes.status, 200);
    const delBody = await delRes.json();
    assert.equal(delBody.success, true);
    assert.equal(delBody.data.hard, false);

    // Subsequent retrieval returns 404
    const getRes = await fetch(`${baseUrl}/api/orders/ORD-102`);
    assert.equal(getRes.status, 404);
});

test('DELETE /api/orders/:orderId?hard=true purges order from database', async () => {
    const res = await fetch(`${baseUrl}/api/orders/ORD-103?hard=true`, {
        method: 'DELETE'
    });
    assert.equal(res.status, 200);
    const body = await res.json();
    assert.equal(body.data.hard, true);

    const getRes = await fetch(`${baseUrl}/api/orders/ORD-103`);
    assert.equal(getRes.status, 404);
});

test('GET /health returns health info without exposing credentials', async () => {
    const res = await fetch(`${baseUrl}/health`);
    assert.equal(res.status, 200);
    const body = await res.json();
    assert.equal(body.status, 'online');
    assert.equal(body.service, 'E-Commerce Order Management & Tracking API');
    assert.ok(body.timestamp);
    assert.strictEqual(body.credentials, undefined);
    assert.strictEqual(body.password, undefined);
});
