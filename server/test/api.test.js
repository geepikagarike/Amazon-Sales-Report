const assert = require('node:assert/strict');
const http = require('node:http');
const test = require('node:test');

const app = require('../server');

let server;
let baseUrl;
let originalDb;
let observedQuery;
let observedOrder;
let observedAggregatePipeline = null;
let failAggregate = false;

function buildMockDatabase() {
    return {
        collection(name) {
            return {
                async countDocuments(query) {
                    observedQuery = query;
                    return 1;
                },
                find(query) {
                    observedQuery = query;
                    return {
                        sort(value) {
                            this.sortValue = value;
                            return this;
                        },
                        skip(value) {
                            this.skipValue = value;
                            return this;
                        },
                        limit(value) {
                            this.limitValue = value;
                            return this;
                        },
                        async toArray() {
                            return [];
                        }
                    };
                },
                async findOne(query) {
                    observedQuery = query;
                    const matchOrder = query && (
                        query.order_id === 'EXISTING-ORD' ||
                        (query.$or && query.$or.some(c => c.order_id === 'EXISTING-ORD'))
                    );
                    if (matchOrder) {
                        return { order_id: 'EXISTING-ORD', customer_id: 'C1', product_id: 'P1', quantity: 1, net_sales: 100 };
                    }
                    return null;
                },
                async insertOne(document) {
                    observedOrder = document;
                    return { insertedId: 'mock-id' };
                },
                aggregate(pipeline) {
                    observedAggregatePipeline = pipeline;
                    return {
                        async toArray() {
                            if (failAggregate) throw new Error('sensitive connection details');
                            return [{ total_orders_count: 10, net_realized_revenue: 5000 }];
                        }
                    };
                }
            };
        }
    };
}

test.before(async () => {
    originalDb = app.locals.db;
    app.locals.db = buildMockDatabase();
    server = http.createServer(app);
    await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
    baseUrl = `http://127.0.0.1:${server.address().port}`;
});

test.after(async () => {
    await new Promise((resolve, reject) => {
        server.close((error) => error ? reject(error) : resolve());
    });
    app.locals.db = originalDb;
});

test('orders endpoint validates pagination and applies bounded filters', async () => {
    const invalid = await fetch(`${baseUrl}/api/orders?page=0`);
    assert.equal(invalid.status, 400);
    assert.deepEqual(await invalid.json(), {
        success: false,
        error: 'page must be a positive integer.'
    });

    const valid = await fetch(`${baseUrl}/api/orders?page=2&limit=25&status=Delivered&region=South`);
    assert.equal(valid.status, 200);
    const result = await valid.json();
    assert.equal(result.pagination.page, 2);
    assert.equal(result.pagination.limit, 25);
    assert.equal(observedQuery.order_status_group, 'Delivered');
    assert.equal(observedQuery.region, 'South');
});

test('orders endpoint rejects oversized page sizes', async () => {
    const response = await fetch(`${baseUrl}/api/orders?limit=501`);
    assert.equal(response.status, 400);
    assert.match((await response.json()).error, /must not exceed 500/);
});

test('POST order validates input and ignores caller-supplied generated fields', async () => {
    const invalid = await fetch(`${baseUrl}/api/orders`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ order_id: 'O1', customer_id: 'C1', product_id: 'P1', quantity: 0 })
    });
    assert.equal(invalid.status, 400);

    const response = await fetch(`${baseUrl}/api/orders`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
            order_id: 'O1',
            customer_id: 'C1',
            product_id: 'P1',
            quantity: 1,
            order_item_id: 'CALLER-CONTROLLED',
            order_date: 'not-a-date',
            net_sales: 10
        })
    });
    assert.equal(response.status, 201);
    assert.notEqual(observedOrder.order_item_id, 'CALLER-CONTROLLED');
    assert.ok(observedOrder.order_item_id.startsWith('ITEM-'));
    assert.ok(observedOrder.order_date instanceof Date);
    assert.equal(observedOrder.net_sales, 10);
});

test('API hides internal database errors behind a consistent response', async () => {
    failAggregate = true;
    const response = await fetch(`${baseUrl}/api/analytics/kpis`);
    failAggregate = false;
    assert.equal(response.status, 500);
    assert.deepEqual(await response.json(), {
        success: false,
        error: 'Internal server error.'
    });
});

test('database-dependent API endpoints report unavailable database clearly', async () => {
    app.locals.db = undefined;
    try {
        const response = await fetch(`${baseUrl}/api/analytics/kpis`);
        assert.equal(response.status, 503);
        assert.deepEqual(await response.json(), {
            success: false,
            error: 'Database is not connected.'
        });
    } finally {
        app.locals.db = buildMockDatabase();
    }
});

test('health endpoint reports service status accurately', async () => {
    const online = await fetch(`${baseUrl}/api/health`);
    assert.equal(online.status, 200);
    const onlineBody = await online.json();
    assert.equal(onlineBody.status, 'online');
    assert.equal(onlineBody.service, 'E-Commerce Order Management & Tracking API');

    app.locals.db = undefined;
    try {
        const offline = await fetch(`${baseUrl}/api/health`);
        assert.equal(offline.status, 200);
        const offlineBody = await offline.json();
        assert.equal(offlineBody.status, 'database_unavailable');
    } finally {
        app.locals.db = buildMockDatabase();
    }
});

test('GET /api/orders/:id returns order if found or 404 if absent', async () => {
    const notFound = await fetch(`${baseUrl}/api/orders/UNKNOWN-ID`);
    assert.equal(notFound.status, 404);
    const notFoundBody = await notFound.json();
    assert.equal(notFoundBody.success, false);
    assert.match(notFoundBody.message || notFoundBody.error, /not found/i);

    const found = await fetch(`${baseUrl}/api/orders/EXISTING-ORD`);
    assert.equal(found.status, 200);
    const body = await found.json();
    assert.equal(body.success, true);
    assert.equal(body.data.order_id, 'EXISTING-ORD');
});

test('all analytics aggregation endpoints return successful responses', async () => {
    const endpoints = [
        '/api/analytics/monthly-sales',
        '/api/analytics/category-performance',
        '/api/analytics/top-products',
        '/api/analytics/top-customers',
        '/api/analytics/customer-segments',
        '/api/analytics/order-status',
        '/api/analytics/regional-sales',
        '/api/analytics/fulfilment-analysis'
    ];
    for (const endpoint of endpoints) {
        const response = await fetch(`${baseUrl}${endpoint}`);
        assert.equal(response.status, 200, `Expected 200 from ${endpoint}`);
        const body = await response.json();
        assert.equal(body.success, true);
        assert.ok(Array.isArray(body.data));
    }
});

test('POST /api/orders rejects invalid field types and boundaries', async () => {
    // Missing required fields
    const missingField = await fetch(`${baseUrl}/api/orders`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ order_id: 'O1', product_id: 'P1', quantity: 1 })
    });
    assert.equal(missingField.status, 400);
    assert.match((await missingField.json()).error, /customer_id is required/);

    // Negative unit price
    const negPrice = await fetch(`${baseUrl}/api/orders`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ order_id: 'O1', customer_id: 'C1', product_id: 'P1', quantity: 1, unit_price: -10 })
    });
    assert.equal(negPrice.status, 400);
    assert.match((await negPrice.json()).error, /unit_price must be a finite non-negative number/);

    // Non-boolean is_b2b
    const badBool = await fetch(`${baseUrl}/api/orders`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ order_id: 'O1', customer_id: 'C1', product_id: 'P1', quantity: 1, is_b2b: 'yes' })
    });
    assert.equal(badBool.status, 400);
    assert.match((await badBool.json()).error, /is_b2b must be a boolean/);

    // Non-integer postal code
    const badPostal = await fetch(`${baseUrl}/api/orders`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ order_id: 'O1', customer_id: 'C1', product_id: 'P1', quantity: 1, ship_postal_code: '560001' })
    });
    assert.equal(badPostal.status, 400);
    assert.match((await badPostal.json()).error, /ship_postal_code must be an integer/);
});

test('analytics KPI endpoint excludes soft-deleted orders from aggregation pipeline', async () => {
    observedAggregatePipeline = null;
    const response = await fetch(`${baseUrl}/api/analytics/kpis`);
    assert.equal(response.status, 200);
    const body = await response.json();
    assert.equal(body.success, true);
    assert.ok(Array.isArray(observedAggregatePipeline), 'Aggregation pipeline must be passed to db');
    // First stage MUST match non-deleted records
    assert.deepEqual(observedAggregatePipeline[0], {
        $match: {
            is_deleted: { $ne: true }
        }
    });
});

test('MATCH_ACTIVE_ORDERS filter logic excludes soft-deleted records and retains active and legacy records', () => {
    const { MATCH_ACTIVE_ORDERS } = require('../../mongodb/aggregation_queries');
    assert.deepEqual(MATCH_ACTIVE_ORDERS, { $match: { is_deleted: { $ne: true } } });

    const records = [
        { order_id: 'O-1', is_deleted: false, net_sales: 100 }, // Active created order
        { order_id: 'O-2', net_sales: 200 },                     // Historical order without is_deleted flag
        { order_id: 'O-3', is_deleted: true, net_sales: 300 }   // Soft-deleted test order
    ];

    // Filter using the exact logic of MATCH_ACTIVE_ORDERS ($match: { is_deleted: { $ne: true } })
    const activeRecords = records.filter(doc => doc.is_deleted !== true);

    assert.equal(activeRecords.length, 2);
    assert.deepEqual(activeRecords.map(r => r.order_id), ['O-1', 'O-2']);
    assert.ok(!activeRecords.some(r => r.order_id === 'O-3'));
});

