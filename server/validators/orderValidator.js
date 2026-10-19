/**
 * Order Request Validators
 * Implements strict input boundary checking, type validation,
 * and sanitization for order creation, updates, and search queries.
 */

const { ALLOWED_SORT_FIELDS, VALID_STATUS_GROUPS, IMMUTABLE_FIELDS } = require('../models/Order');

function clientError(message) {
    const error = new Error(message);
    error.statusCode = 400;
    return error;
}

function parseBoundedInteger(value, name, defaultValue, maximum) {
    if (value === undefined || value === null || value === '') return defaultValue;
    if (typeof value !== 'string' || !/^[1-9]\d*$/.test(value)) {
        throw clientError(`${name} must be a positive integer.`);
    }
    const parsed = Number(value);
    if (!Number.isSafeInteger(parsed) || parsed > maximum) {
        throw clientError(`${name} must not exceed ${maximum}.`);
    }
    return parsed;
}

function parseOptionalString(value, name, maxLength = 100) {
    if (value === undefined || value === null) return undefined;
    if (typeof value !== 'string' || !value.trim() || value.trim().length > maxLength) {
        throw clientError(`${name} must be a non-empty string of at most ${maxLength} characters.`);
    }
    return value.trim();
}

function parseOptionalDate(value, name) {
    if (value === undefined || value === null || value === '') return undefined;
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) {
        throw clientError(`${name} must be a valid ISO date format (YYYY-MM-DD).`);
    }
    return parsed;
}

/**
 * Validates and normalizes query parameters for listing orders.
 * @param {object} query 
 * @returns {object}
 */
function validateListOrdersQuery(query = {}) {
    const page = parseBoundedInteger(query.page, 'page', 1, 1000000);
    const limit = parseBoundedInteger(query.limit, 'limit', 20, 500);

    const sortByParam = query.sortBy || query.sort_by;
    let sortBy = 'order_date';
    if (sortByParam !== undefined) {
        if (!ALLOWED_SORT_FIELDS.has(sortByParam)) {
            throw clientError(`Invalid sortBy field '${sortByParam}'. Allowed fields: ${Array.from(ALLOWED_SORT_FIELDS).join(', ')}.`);
        }
        sortBy = sortByParam;
    }

    const orderParam = query.order || query.direction;
    let sortOrder = -1; // default descending
    if (orderParam !== undefined) {
        const normalized = String(orderParam).toLowerCase();
        if (normalized === 'asc' || normalized === '1') sortOrder = 1;
        else if (normalized === 'desc' || normalized === '-1') sortOrder = -1;
        else throw clientError("order must be either 'asc' or 'desc'.");
    }

    return {
        page,
        limit,
        sortBy,
        sortOrder,
        status: parseOptionalString(query.status || query.order_status_group, 'status', 50),
        region: parseOptionalString(query.region, 'region', 50),
        customerId: parseOptionalString(query.customer_id || query.customerId, 'customer_id', 50),
        productId: parseOptionalString(query.product_id || query.productId, 'product_id', 50),
        city: parseOptionalString(query.city || query.ship_city, 'city', 100),
        courier: parseOptionalString(query.courier || query.courier_status, 'courier', 50),
        search: parseOptionalString(query.search || query.q, 'search', 100),
        startDate: parseOptionalDate(query.startDate || query.from || query.start_date, 'startDate'),
        endDate: parseOptionalDate(query.endDate || query.to || query.end_date, 'endDate')
    };
}

/**
 * Validates body payload for creating a new order.
 * @param {object} body 
 * @returns {object}
 */
function validateCreateOrderBody(body) {
    if (!body || typeof body !== 'object' || Array.isArray(body)) {
        throw clientError('Request body must be a JSON object.');
    }

    for (const field of ['order_id', 'customer_id', 'product_id']) {
        if (typeof body[field] !== 'string' || !body[field].trim()) {
            throw clientError(`${field} is required and must be a non-empty string.`);
        }
    }

    if (!Number.isInteger(body.quantity) || body.quantity <= 0) {
        throw clientError('quantity is required and must be a positive integer.');
    }

    const orderStatusGroup = body.order_status_group || body.order_status || 'Pending';
    if (!VALID_STATUS_GROUPS.includes(orderStatusGroup)) {
        throw clientError(`Invalid order_status_group '${orderStatusGroup}'. Allowed: ${VALID_STATUS_GROUPS.join(', ')}.`);
    }

    const numericFields = ['unit_price', 'gross_amount', 'net_sales', 'cogs', 'gross_profit', 'profit_margin_pct'];
    const stringFields = [
        'order_id', 'customer_id', 'product_id', 'order_status',
        'order_status_group', 'courier_status', 'fulfilment_method', 'fulfilled_by',
        'sales_channel', 'ship_service_level', 'ship_city', 'ship_state', 'region'
    ];

    const clean = {
        order_id: body.order_id.trim(),
        customer_id: body.customer_id.trim(),
        product_id: body.product_id.trim(),
        quantity: body.quantity,
        order_status: body.order_status ? String(body.order_status).trim() : orderStatusGroup,
        order_status_group: orderStatusGroup,
        courier_status: body.courier_status ? String(body.courier_status).trim() : (orderStatusGroup === 'Shipped' ? 'Shipped' : 'Pending'),
        fulfilment_method: body.fulfilment_method ? String(body.fulfilment_method).trim() : 'Amazon',
        fulfilled_by: body.fulfilled_by ? String(body.fulfilled_by).trim() : undefined,
        sales_channel: body.sales_channel ? String(body.sales_channel).trim() : 'Amazon.in',
        ship_service_level: body.ship_service_level ? String(body.ship_service_level).trim() : 'Standard',
        ship_city: body.ship_city ? String(body.ship_city).trim() : undefined,
        ship_state: body.ship_state ? String(body.ship_state).trim() : undefined,
        region: body.region ? String(body.region).trim() : undefined
    };

    for (const field of numericFields) {
        if (body[field] !== undefined) {
            const val = body[field];
            if (typeof val !== 'number' || !Number.isFinite(val) || val < 0) {
                throw clientError(`${field} must be a finite non-negative number.`);
            }
            clean[field] = val;
        }
    }

    if (clean.unit_price !== undefined && clean.gross_amount === undefined) {
        clean.gross_amount = clean.unit_price * clean.quantity;
    }
    if (clean.gross_amount !== undefined && clean.net_sales === undefined) {
        clean.net_sales = ['Delivered', 'Shipped'].includes(clean.order_status_group) ? clean.gross_amount : 0.0;
    }

    if (body.is_b2b !== undefined) {
        if (typeof body.is_b2b !== 'boolean') throw clientError('is_b2b must be a boolean.');
        clean.is_b2b = body.is_b2b;
    } else {
        clean.is_b2b = false;
    }

    if (body.ship_postal_code !== undefined) {
        if (!Number.isInteger(body.ship_postal_code)) throw clientError('ship_postal_code must be an integer.');
        clean.ship_postal_code = body.ship_postal_code;
    }

    return clean;
}

/**
 * Validates body payload for partially updating an existing order.
 * @param {object} body 
 * @returns {object}
 */
function validateUpdateOrderBody(body) {
    if (!body || typeof body !== 'object' || Array.isArray(body)) {
        throw clientError('Request body must be a JSON object.');
    }

    const keys = Object.keys(body);
    if (keys.length === 0) {
        throw clientError('Request body cannot be empty.');
    }

    for (const immutable of IMMUTABLE_FIELDS) {
        if (body[immutable] !== undefined) {
            throw clientError(`Field '${immutable}' is immutable and cannot be updated.`);
        }
    }

    const updates = {};

    if (body.quantity !== undefined) {
        if (!Number.isInteger(body.quantity) || body.quantity <= 0) {
            throw clientError('quantity must be a positive integer.');
        }
        updates.quantity = body.quantity;
    }

    const numericFields = ['unit_price', 'gross_amount', 'net_sales', 'cogs', 'gross_profit', 'profit_margin_pct'];
    for (const field of numericFields) {
        if (body[field] !== undefined) {
            const val = body[field];
            if (typeof val !== 'number' || !Number.isFinite(val) || val < 0) {
                throw clientError(`${field} must be a finite non-negative number.`);
            }
            updates[field] = val;
        }
    }

    const stringFields = [
        'customer_id', 'product_id', 'order_status', 'order_status_group',
        'courier_status', 'fulfilment_method', 'fulfilled_by', 'sales_channel',
        'ship_service_level', 'ship_city', 'ship_state', 'region'
    ];
    for (const field of stringFields) {
        if (body[field] !== undefined) {
            if (typeof body[field] !== 'string' || !body[field].trim()) {
                throw clientError(`${field} must be a non-empty string.`);
            }
            if (body[field].trim().length > 200) {
                throw clientError(`${field} must not exceed 200 characters.`);
            }
            updates[field] = body[field].trim();
        }
    }

    if (body.order_status_group !== undefined) {
        if (!VALID_STATUS_GROUPS.includes(body.order_status_group)) {
            throw clientError(`Invalid order_status_group '${body.order_status_group}'. Allowed: ${VALID_STATUS_GROUPS.join(', ')}.`);
        }
        updates.order_status_group = body.order_status_group;
    }

    if (body.is_b2b !== undefined) {
        if (typeof body.is_b2b !== 'boolean') throw clientError('is_b2b must be a boolean.');
        updates.is_b2b = body.is_b2b;
    }

    if (body.ship_postal_code !== undefined) {
        if (!Number.isInteger(body.ship_postal_code)) throw clientError('ship_postal_code must be an integer.');
        updates.ship_postal_code = body.ship_postal_code;
    }

    return updates;
}

/**
 * Validates body payload for updating order status.
 * @param {object} body 
 * @returns {string} Target new status
 */
function validateStatusUpdateBody(body) {
    if (!body || typeof body !== 'object' || Array.isArray(body)) {
        throw clientError('Request body must be a JSON object.');
    }
    const status = body.status || body.order_status_group || body.order_status;
    if (typeof status !== 'string' || !status.trim()) {
        throw clientError("Field 'status' is required and must be a non-empty string.");
    }
    const trimmed = status.trim();
    if (!VALID_STATUS_GROUPS.includes(trimmed)) {
        throw clientError(`Invalid status '${trimmed}'. Allowed: ${VALID_STATUS_GROUPS.join(', ')}.`);
    }
    return trimmed;
}

module.exports = {
    clientError,
    validateListOrdersQuery,
    validateCreateOrderBody,
    validateUpdateOrderBody,
    validateStatusUpdateBody
};
