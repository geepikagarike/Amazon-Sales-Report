/**
 * Order Controller
 * Bridges HTTP transport layer to Order service business logic.
 */

const orderService = require('../services/orderService');

function getDatabase(req) {
    const db = req.app.locals.db || require('../config/database').getDb();
    if (!db) {
        const error = new Error('Database is not connected.');
        error.statusCode = 503;
        throw error;
    }
    return db;
}

async function listOrders(req, res, next) {
    try {
        const db = getDatabase(req);
        const result = await orderService.listOrders(db, req.validatedQuery || req.query);
        res.status(200).json({
            success: true,
            pagination: result.pagination,
            data: result.data
        });
    } catch (err) {
        next(err);
    }
}

async function getOrderById(req, res, next) {
    try {
        const db = getDatabase(req);
        const orderId = req.params.orderId || req.params.id;
        const order = await orderService.getOrderById(db, orderId);
        res.status(200).json({
            success: true,
            data: order
        });
    } catch (err) {
        next(err);
    }
}

async function createOrder(req, res, next) {
    try {
        const db = getDatabase(req);
        const orderData = req.validatedBody || req.body;
        const newOrder = await orderService.createOrder(db, orderData);
        res.status(201).json({
            success: true,
            message: 'Order created successfully.',
            data: newOrder
        });
    } catch (err) {
        next(err);
    }
}

async function updateOrder(req, res, next) {
    try {
        const db = getDatabase(req);
        const orderId = req.params.orderId || req.params.id;
        const updates = req.validatedUpdates || req.body;
        const updated = await orderService.updateOrder(db, orderId, updates);
        res.status(200).json({
            success: true,
            message: 'Order updated successfully.',
            data: updated
        });
    } catch (err) {
        next(err);
    }
}

async function updateOrderStatus(req, res, next) {
    try {
        const db = getDatabase(req);
        const orderId = req.params.orderId || req.params.id;
        const status = req.validatedStatus || req.body.status;
        const updated = await orderService.updateOrderStatus(db, orderId, status);
        res.status(200).json({
            success: true,
            message: 'Order status updated successfully.',
            data: updated
        });
    } catch (err) {
        next(err);
    }
}

async function deleteOrder(req, res, next) {
    try {
        const db = getDatabase(req);
        const orderId = req.params.orderId || req.params.id;
        const hard = req.query.hard === 'true';
        const result = await orderService.deleteOrder(db, orderId, hard);
        res.status(200).json({
            success: true,
            message: hard ? 'Order permanently deleted.' : 'Order deleted successfully (soft-deleted).',
            data: result
        });
    } catch (err) {
        next(err);
    }
}

module.exports = {
    getDatabase,
    listOrders,
    getOrderById,
    createOrder,
    updateOrder,
    updateOrderStatus,
    deleteOrder
};
