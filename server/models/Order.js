/**
 * Order Model & Schema Definition
 * Defines the e-commerce order structure, permitted fields, types,
 * index definitions, and the state-machine rules for order status transitions.
 */

const VALID_STATUS_GROUPS = ['Pending', 'Shipped', 'Delivered', 'Cancelled', 'Returned', 'Other'];

/**
 * Valid order status transition state machine.
 * Defines permitted lifecycle progression.
 */
const STATUS_TRANSITIONS = {
    Pending: ['Shipped', 'Cancelled'],
    Shipped: ['Delivered', 'Returned', 'Cancelled'],
    Delivered: ['Returned'],
    Cancelled: [],  // Terminal state
    Returned: [],   // Terminal state
    Other: ['Pending', 'Shipped', 'Cancelled']
};

/**
 * Validates whether transitioning from currentStatus to newStatus is permitted.
 * @param {string} currentStatus 
 * @param {string} newStatus 
 * @returns {{ valid: boolean, error?: string }}
 */
function validateStatusTransition(currentStatus, newStatus) {
    if (!VALID_STATUS_GROUPS.includes(newStatus)) {
        return {
            valid: false,
            error: `Invalid status '${newStatus}'. Allowed statuses: ${VALID_STATUS_GROUPS.join(', ')}.`
        };
    }

    if (currentStatus === newStatus) {
        return { valid: true };
    }

    const allowed = STATUS_TRANSITIONS[currentStatus] || [];
    if (!allowed.includes(newStatus)) {
        return {
            valid: false,
            error: `Cannot transition order status from '${currentStatus}' to '${newStatus}'. Allowed transitions: ${allowed.length ? allowed.join(', ') : 'none (terminal state)'}.`
        };
    }

    return { valid: true };
}

/**
 * Permitted sort fields for order listing queries.
 */
const ALLOWED_SORT_FIELDS = new Set([
    'order_date',
    'gross_amount',
    'net_sales',
    'quantity',
    'order_id',
    'created_at',
    'updated_at'
]);

/**
 * Immutable fields that must never be updated via PATCH /api/orders/:orderId.
 */
const IMMUTABLE_FIELDS = new Set([
    '_id',
    'order_item_id',
    'created_at',
    'is_deleted'
]);

/**
 * Indexes required for high-performance order management queries.
 */
const ORDER_INDEXES = [
    { key: { order_item_id: 1 }, options: { unique: true, name: 'idx_order_item_id_pk' } },
    { key: { order_id: 1 }, options: { name: 'idx_order_id' } },
    { key: { customer_id: 1 }, options: { name: 'idx_customer_id' } },
    { key: { product_id: 1 }, options: { name: 'idx_product_id' } },
    { key: { order_date: -1 }, options: { name: 'idx_order_date_desc' } },
    { key: { order_status_group: 1 }, options: { name: 'idx_status_group' } },
    { key: { ship_city: 1 }, options: { name: 'idx_ship_city' } },
    { key: { courier_status: 1 }, options: { name: 'idx_courier_status' } },
    { key: { is_deleted: 1, order_date: -1 }, options: { name: 'idx_active_orders_date' } },
    { key: { customer_id: 1, order_date: -1 }, options: { name: 'idx_cust_order_history' } }
];

module.exports = {
    VALID_STATUS_GROUPS,
    STATUS_TRANSITIONS,
    validateStatusTransition,
    ALLOWED_SORT_FIELDS,
    IMMUTABLE_FIELDS,
    ORDER_INDEXES
};
