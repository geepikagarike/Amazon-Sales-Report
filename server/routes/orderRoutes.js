/**
 * Order Management & Tracking API Routes
 * Exposes REST endpoints for orders with input validation and lifecycle management.
 */

const express = require('express');
const router = express.Router();

const orderController = require('../controllers/orderController');
const {
    validateListQueryMiddleware,
    validateCreateBodyMiddleware,
    validateUpdateBodyMiddleware,
    validateStatusBodyMiddleware
} = require('../middleware/validateOrder');

// 1. List orders with pagination, search, sorting, and multi-field filters
router.get('/', validateListQueryMiddleware, orderController.listOrders);

// 2. Create a new order transaction
router.post('/', validateCreateBodyMiddleware, orderController.createOrder);

// 3. Get single order details by order_id or order_item_id
router.get('/:orderId', orderController.getOrderById);

// 4. Update mutable fields of an existing order
router.patch('/:orderId', validateUpdateBodyMiddleware, orderController.updateOrder);

// 5. Update order status with state-machine transition validation
router.patch('/:orderId/status', validateStatusBodyMiddleware, orderController.updateOrderStatus);

// 6. Delete order (soft delete by default, ?hard=true for permanent purge)
router.delete('/:orderId', orderController.deleteOrder);

module.exports = router;
