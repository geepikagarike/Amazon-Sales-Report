/**
 * Automated Input Validation & Boundary Tests
 * Tests query parameter parsing, body validation rules, status boundaries,
 * and error middleware responses.
 */

const assert = require('node:assert/strict');
const test = require('node:test');

const {
    validateListOrdersQuery,
    validateCreateOrderBody,
    validateUpdateOrderBody,
    validateStatusUpdateBody
} = require('../validators/orderValidator');
const { validateStatusTransition } = require('../models/Order');

test('validateListOrdersQuery applies safe defaults and accepts valid filters', () => {
    const parsed = validateListOrdersQuery({
        page: '2',
        limit: '50',
        sortBy: 'gross_amount',
        order: 'asc',
        status: 'Delivered',
        region: 'North',
        startDate: '2024-01-01',
        endDate: '2024-01-31'
    });

    assert.equal(parsed.page, 2);
    assert.equal(parsed.limit, 50);
    assert.equal(parsed.sortBy, 'gross_amount');
    assert.equal(parsed.sortOrder, 1);
    assert.equal(parsed.status, 'Delivered');
    assert.equal(parsed.region, 'North');
    assert.ok(parsed.startDate instanceof Date);
    assert.ok(parsed.endDate instanceof Date);
});

test('validateListOrdersQuery rejects invalid page, limit, sort, or date', () => {
    assert.throws(() => validateListOrdersQuery({ page: '0' }), /page must be a positive integer/);
    assert.throws(() => validateListOrdersQuery({ page: 'abc' }), /page must be a positive integer/);
    assert.throws(() => validateListOrdersQuery({ limit: '501' }), /limit must not exceed 500/);
    assert.throws(() => validateListOrdersQuery({ sortBy: 'unknown_column' }), /Invalid sortBy field/);
    assert.throws(() => validateListOrdersQuery({ order: 'sideways' }), /order must be either 'asc' or 'desc'/);
    assert.throws(() => validateListOrdersQuery({ startDate: 'not-a-date' }), /startDate must be a valid ISO date/);
});

test('validateCreateOrderBody validates required identifiers and positive quantity', () => {
    assert.throws(() => validateCreateOrderBody(null), /Request body must be a JSON object/);
    assert.throws(() => validateCreateOrderBody([]), /Request body must be a JSON object/);
    assert.throws(() => validateCreateOrderBody({ customer_id: 'C1', product_id: 'P1', quantity: 1 }), /order_id is required/);
    assert.throws(() => validateCreateOrderBody({ order_id: 'O1', product_id: 'P1', quantity: 1 }), /customer_id is required/);
    assert.throws(() => validateCreateOrderBody({ order_id: 'O1', customer_id: 'C1', quantity: 1 }), /product_id is required/);

    // Invalid quantity
    assert.throws(() => validateCreateOrderBody({ order_id: 'O1', customer_id: 'C1', product_id: 'P1', quantity: 0 }), /quantity is required and must be a positive integer/);
    assert.throws(() => validateCreateOrderBody({ order_id: 'O1', customer_id: 'C1', product_id: 'P1', quantity: -5 }), /quantity is required and must be a positive integer/);
    assert.throws(() => validateCreateOrderBody({ order_id: 'O1', customer_id: 'C1', product_id: 'P1', quantity: 2.5 }), /quantity is required and must be a positive integer/);
});

test('validateCreateOrderBody validates types and auto-computes financial fields', () => {
    const valid = validateCreateOrderBody({
        order_id: 'O-100',
        customer_id: 'C-100',
        product_id: 'P-100',
        quantity: 2,
        unit_price: 50.0,
        order_status_group: 'Delivered',
        is_b2b: true
    });

    assert.equal(valid.gross_amount, 100.0);
    assert.equal(valid.net_sales, 100.0);
    assert.equal(valid.is_b2b, true);
    assert.equal(valid.order_status_group, 'Delivered');

    // Negative unit price
    assert.throws(() => validateCreateOrderBody({
        order_id: 'O-100', customer_id: 'C-100', product_id: 'P-100', quantity: 1, unit_price: -10
    }), /unit_price must be a finite non-negative number/);

    // Invalid boolean
    assert.throws(() => validateCreateOrderBody({
        order_id: 'O-100', customer_id: 'C-100', product_id: 'P-100', quantity: 1, is_b2b: 'yes'
    }), /is_b2b must be a boolean/);
});

test('validateUpdateOrderBody enforces non-empty payload and protects immutable fields', () => {
    assert.throws(() => validateUpdateOrderBody({}), /Request body cannot be empty/);
    assert.throws(() => validateUpdateOrderBody({ order_item_id: 'NEW-ID' }), /Field 'order_item_id' is immutable/);
    assert.throws(() => validateUpdateOrderBody({ _id: 'NEW-ID' }), /Field '_id' is immutable/);
    assert.throws(() => validateUpdateOrderBody({ created_at: new Date() }), /Field 'created_at' is immutable/);
    assert.throws(() => validateUpdateOrderBody({ is_deleted: true }), /Field 'is_deleted' is immutable/);

    const valid = validateUpdateOrderBody({ quantity: 4, region: 'East' });
    assert.equal(valid.quantity, 4);
    assert.equal(valid.region, 'East');
});

test('validateStatusUpdateBody requires valid status value', () => {
    assert.throws(() => validateStatusUpdateBody({}), /Field 'status' is required/);
    assert.throws(() => validateStatusUpdateBody({ status: 'InvalidStatus' }), /Invalid status 'InvalidStatus'/);
    assert.equal(validateStatusUpdateBody({ status: 'Delivered' }), 'Delivered');
    assert.equal(validateStatusUpdateBody({ order_status_group: 'Cancelled' }), 'Cancelled');
});

test('validateStatusTransition enforces lifecycle rules', () => {
    // Valid transitions
    assert.equal(validateStatusTransition('Pending', 'Shipped').valid, true);
    assert.equal(validateStatusTransition('Pending', 'Cancelled').valid, true);
    assert.equal(validateStatusTransition('Shipped', 'Delivered').valid, true);
    assert.equal(validateStatusTransition('Shipped', 'Returned').valid, true);
    assert.equal(validateStatusTransition('Delivered', 'Returned').valid, true);
    assert.equal(validateStatusTransition('Pending', 'Pending').valid, true);

    // Invalid transitions
    assert.equal(validateStatusTransition('Cancelled', 'Shipped').valid, false);
    assert.equal(validateStatusTransition('Returned', 'Delivered').valid, false);
    assert.equal(validateStatusTransition('Delivered', 'Pending').valid, false);
});
