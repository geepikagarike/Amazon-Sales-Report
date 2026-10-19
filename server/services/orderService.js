/**
 * Order Service Layer
 * Encapsulates core database interactions, query building, business calculations,
 * and order lifecycle state transitions.
 */

const { randomUUID } = require('crypto');
const { validateStatusTransition } = require('../models/Order');

function notFoundError(message = 'Order not found.') {
    const error = new Error(message);
    error.statusCode = 404;
    return error;
}

function clientError(message) {
    const error = new Error(message);
    error.statusCode = 400;
    return error;
}

/**
 * Builds MongoDB query filter from validated search options.
 * @param {object} options 
 * @returns {object}
 */
function buildOrderFilter(options = {}) {
    const filter = { is_deleted: { $ne: true } };

    if (options.status) {
        filter.order_status_group = options.status;
    }
    if (options.region) {
        filter.region = options.region;
    }
    if (options.customerId) {
        filter.customer_id = options.customerId;
    }
    if (options.productId) {
        filter.product_id = options.productId;
    }
    if (options.city) {
        filter.ship_city = new RegExp(`^${escapeRegex(options.city)}$`, 'i');
    }
    if (options.courier) {
        filter.courier_status = options.courier;
    }

    if (options.search) {
        const term = escapeRegex(options.search);
        filter.$or = [
            { order_id: { $regex: term, $options: 'i' } },
            { product_id: { $regex: term, $options: 'i' } },
            { customer_id: { $regex: term, $options: 'i' } }
        ];
    }

    if (options.startDate || options.endDate) {
        filter.order_date = {};
        if (options.startDate) {
            filter.order_date.$gte = options.startDate instanceof Date ? options.startDate.toISOString().slice(0, 10) : options.startDate;
        }
        if (options.endDate) {
            filter.order_date.$lte = options.endDate instanceof Date ? options.endDate.toISOString().slice(0, 10) : options.endDate;
        }
    }

    return filter;
}

function escapeRegex(text) {
    return text.replace(/[-[\]{}()*+?.,\\^$|#\s]/g, '\\$&');
}

/**
 * Lists orders with pagination, sorting, and multi-criteria filtering.
 * @param {Db} db 
 * @param {object} options 
 * @returns {Promise<{ pagination: object, data: Array }>}
 */
async function listOrders(db, options = {}) {
    const { page = 1, limit = 20, sortBy = 'order_date', sortOrder = -1 } = options;
    const skip = (page - 1) * limit;
    const filter = buildOrderFilter(options);

    const sortObj = { [sortBy]: sortOrder };
    if (sortBy !== '_id') sortObj._id = sortOrder; // Deterministic tie-breaker

    const total = await db.collection('orders').countDocuments(filter);
    const orders = await db.collection('orders')
        .find(filter)
        .sort(sortObj)
        .skip(skip)
        .limit(limit)
        .toArray();

    return {
        pagination: {
            page,
            limit,
            total,
            total_pages: Math.ceil(total / limit) || 1,
            count: orders.length
        },
        data: orders
    };
}

/**
 * Retrieves a single order by order_id or order_item_id.
 * @param {Db} db 
 * @param {string} orderId 
 * @returns {Promise<object>}
 */
async function getOrderById(db, orderId) {
    if (!orderId || typeof orderId !== 'string') {
        throw notFoundError();
    }

    const order = await db.collection('orders').findOne({
        $or: [
            { order_id: orderId },
            { order_item_id: orderId }
        ],
        is_deleted: { $ne: true }
    });

    if (!order) {
        throw notFoundError(`Order '${orderId}' was not found.`);
    }

    return order;
}

/**
 * Creates a new order record.
 * @param {Db} db 
 * @param {object} orderData 
 * @returns {Promise<object>}
 */
async function createOrder(db, orderData) {
    const now = new Date();
    const orderItemId = `ITEM-${randomUUID()}`;

    // Ensure unique item ID
    const existing = await db.collection('orders').findOne({ order_item_id: orderItemId });
    if (existing) {
        const error = new Error(`Order item with ID '${orderItemId}' already exists.`);
        error.statusCode = 409;
        throw error;
    }

    let orderDate = now;
    if (orderData.order_date instanceof Date && !Number.isNaN(orderData.order_date.getTime())) {
        orderDate = orderData.order_date;
    } else if (orderData.order_date && !Number.isNaN(new Date(orderData.order_date).getTime())) {
        orderDate = new Date(orderData.order_date);
    }

    const orderRecord = {
        ...orderData,
        order_item_id: orderItemId,
        order_date: orderDate,
        created_at: now,
        updated_at: now,
        is_deleted: false,
        is_new_record: true
    };

    const result = await db.collection('orders').insertOne(orderRecord);
    return {
        _id: result.insertedId,
        ...orderRecord
    };
}

/**
 * Updates permitted mutable fields of an existing order.
 * @param {Db} db 
 * @param {string} orderId 
 * @param {object} updates 
 * @returns {Promise<object>}
 */
async function updateOrder(db, orderId, updates) {
    const currentOrder = await getOrderById(db, orderId);

    // If status group is being updated, enforce transition rules
    if (updates.order_status_group && updates.order_status_group !== currentOrder.order_status_group) {
        const transition = validateStatusTransition(currentOrder.order_status_group, updates.order_status_group);
        if (!transition.valid) {
            throw clientError(transition.error);
        }
        if (['Cancelled', 'Returned'].includes(updates.order_status_group)) {
            updates.net_sales = 0.0;
        }
    }

    // Recalculate financial fields if quantity or unit_price was modified
    const newQty = updates.quantity !== undefined ? updates.quantity : currentOrder.quantity;
    const newPrice = updates.unit_price !== undefined ? updates.unit_price : currentOrder.unit_price;
    if (updates.gross_amount === undefined && (updates.quantity !== undefined || updates.unit_price !== undefined)) {
        if (newPrice !== undefined && newQty !== undefined) {
            updates.gross_amount = newPrice * newQty;
            const status = updates.order_status_group || currentOrder.order_status_group;
            if (updates.net_sales === undefined) {
                updates.net_sales = ['Delivered', 'Shipped'].includes(status) ? updates.gross_amount : 0.0;
            }
        }
    }

    updates.updated_at = new Date();

    const result = await db.collection('orders').findOneAndUpdate(
        { _id: currentOrder._id },
        { $set: updates },
        { returnDocument: 'after' }
    );

    return result.value || { ...currentOrder, ...updates };
}

/**
 * Updates order status according to the valid state machine.
 * @param {Db} db 
 * @param {string} orderId 
 * @param {string} newStatus 
 * @returns {Promise<object>}
 */
async function updateOrderStatus(db, orderId, newStatus) {
    const currentOrder = await getOrderById(db, orderId);

    const transition = validateStatusTransition(currentOrder.order_status_group, newStatus);
    if (!transition.valid) {
        throw clientError(transition.error);
    }

    const updates = {
        order_status: newStatus,
        order_status_group: newStatus,
        updated_at: new Date()
    };

    if (newStatus === 'Shipped') {
        updates.courier_status = 'Shipped';
    } else if (newStatus === 'Delivered') {
        updates.courier_status = 'Delivered to Buyer';
    } else if (newStatus === 'Cancelled') {
        updates.courier_status = 'Cancelled';
        updates.net_sales = 0.0;
    } else if (newStatus === 'Returned') {
        updates.courier_status = 'Returned to Seller';
        updates.net_sales = 0.0;
    }

    const result = await db.collection('orders').findOneAndUpdate(
        { _id: currentOrder._id },
        { $set: updates },
        { returnDocument: 'after' }
    );

    return result.value || { ...currentOrder, ...updates };
}

/**
 * Safe order deletion implementing soft-delete by default.
 * @param {Db} db 
 * @param {string} orderId 
 * @param {boolean} hardDelete 
 * @returns {Promise<{ deleted: boolean, order_id: string, hard: boolean }>}
 */
async function deleteOrder(db, orderId, hardDelete = false) {
    const currentOrder = await getOrderById(db, orderId);

    if (hardDelete) {
        await db.collection('orders').deleteOne({ _id: currentOrder._id });
        return {
            deleted: true,
            order_id: currentOrder.order_id,
            order_item_id: currentOrder.order_item_id,
            hard: true
        };
    }

    // Soft delete policy: preserves audit trail
    await db.collection('orders').updateOne(
        { _id: currentOrder._id },
        {
            $set: {
                is_deleted: true,
                deleted_at: new Date(),
                updated_at: new Date()
            }
        }
    );

    return {
        deleted: true,
        order_id: currentOrder.order_id,
        order_item_id: currentOrder.order_item_id,
        hard: false
    };
}

module.exports = {
    listOrders,
    getOrderById,
    createOrder,
    updateOrder,
    updateOrderStatus,
    deleteOrder,
    buildOrderFilter
};
