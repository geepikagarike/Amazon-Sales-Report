function clientError(message) {
    const error = new Error(message);
    error.statusCode = 400;
    return error;
}

function parseBoundedInteger(value, name, defaultValue, maximum) {
    if (value === undefined) return defaultValue;
    if (typeof value !== 'string' || !/^[1-9]\d*$/.test(value)) {
        throw clientError(`${name} must be a positive integer.`);
    }
    const parsed = Number(value);
    if (!Number.isSafeInteger(parsed) || parsed > maximum) {
        throw clientError(`${name} must not exceed ${maximum}.`);
    }
    return parsed;
}

function parseOptionalFilter(value, name) {
    if (value === undefined) return undefined;
    if (typeof value !== 'string' || !value.trim() || value.trim().length > 100) {
        throw clientError(`${name} must be a non-empty string of at most 100 characters.`);
    }
    return value.trim();
}

function parseOrdersQuery(query) {
    return {
        page: parseBoundedInteger(query.page, 'page', 1, 1000000),
        limit: parseBoundedInteger(query.limit, 'limit', 20, 500),
        status: parseOptionalFilter(query.status, 'status'),
        region: parseOptionalFilter(query.region, 'region'),
        customerId: parseOptionalFilter(query.customer_id, 'customer_id')
    };
}

function validateNewOrder(body) {
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

    const allowedFields = [
        'order_id', 'customer_id', 'product_id', 'quantity', 'order_status',
        'order_status_group', 'courier_status', 'fulfilment_method', 'fulfilled_by',
        'sales_channel', 'ship_service_level', 'unit_price', 'gross_amount',
        'net_sales', 'cogs', 'gross_profit', 'profit_margin_pct', 'is_b2b',
        'ship_city', 'ship_state', 'region', 'ship_postal_code'
    ];
    const stringFields = new Set([
        'order_id', 'customer_id', 'product_id', 'order_status',
        'order_status_group', 'courier_status', 'fulfilment_method', 'fulfilled_by',
        'sales_channel', 'ship_service_level', 'ship_city', 'ship_state', 'region'
    ]);
    const newOrder = {};
    for (const field of allowedFields) {
        if (body[field] === undefined) continue;
        const value = body[field];
        if (['unit_price', 'gross_amount', 'net_sales', 'cogs', 'gross_profit', 'profit_margin_pct'].includes(field)) {
            if (typeof value !== 'number' || !Number.isFinite(value) || value < 0) {
                throw clientError(`${field} must be a finite non-negative number.`);
            }
        }
        if (stringFields.has(field) && typeof value !== 'string') {
            throw clientError(`${field} must be a string.`);
        }
        if (field === 'is_b2b' && typeof value !== 'boolean') {
            throw clientError('is_b2b must be a boolean.');
        }
        if (field === 'ship_postal_code' && !Number.isInteger(value)) {
            throw clientError('ship_postal_code must be an integer.');
        }
        if (typeof value === 'string' && value.length > 200) {
            throw clientError(`${field} must not exceed 200 characters.`);
        }
        newOrder[field] = typeof value === 'string' ? value.trim() : value;
    }
    return newOrder;
}

function getDatabase(req) {
    const db = req.app.locals.db;
    if (!db) {
        const error = new Error('Database is not connected.');
        error.statusCode = 503;
        throw error;
    }
    return db;
}

function sendApiError(error, res) {
    const statusCode = Number.isInteger(error.statusCode) ? error.statusCode : 500;
    if (statusCode >= 500) {
        console.error(`API request failed (${error.name || 'Error'}).`);
    }
    const message = statusCode === 400 || statusCode === 503
        ? error.message
        : 'Internal server error.';
    return res.status(statusCode).json({ success: false, error: message });
}

module.exports = {
    getDatabase,
    parseOrdersQuery,
    sendApiError,
    validateNewOrder
};
