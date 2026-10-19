/**
 * Express Analytics Routes
 * Exposes REST API endpoints powered by MongoDB Aggregation Pipelines
 */

const express = require('express');
const router = express.Router();
const pipelines = require('../../mongodb/aggregation_queries');
const { getDatabase, sendApiError } = require('../api_validation');

// 1. Executive KPIs
router.get('/kpis', async (req, res) => {
    try {
        const db = getDatabase(req);
        const result = await db.collection('orders').aggregate(pipelines.pipelineExecutiveKPIs).toArray();
        res.json({ success: true, data: result[0] || {} });
    } catch (err) {
        sendApiError(err, res);
    }
});

// 2. Monthly Sales Trend
router.get('/monthly-sales', async (req, res) => {
    try {
        const db = getDatabase(req);
        const result = await db.collection('orders').aggregate(pipelines.pipelineMonthlySalesTrend).toArray();
        res.json({ success: true, data: result });
    } catch (err) {
        sendApiError(err, res);
    }
});

// 3. Category Performance
router.get('/category-performance', async (req, res) => {
    try {
        const db = getDatabase(req);
        const result = await db.collection('orders').aggregate(pipelines.pipelineCategoryPerformance).toArray();
        res.json({ success: true, data: result });
    } catch (err) {
        sendApiError(err, res);
    }
});

// 4. Top 10 Products
router.get('/top-products', async (req, res) => {
    try {
        const db = getDatabase(req);
        const result = await db.collection('orders').aggregate(pipelines.pipelineTopProducts).toArray();
        res.json({ success: true, data: result });
    } catch (err) {
        sendApiError(err, res);
    }
});

// 5. Top 10 Customers
router.get('/top-customers', async (req, res) => {
    try {
        const db = getDatabase(req);
        const result = await db.collection('orders').aggregate(pipelines.pipelineTopCustomers).toArray();
        res.json({ success: true, data: result });
    } catch (err) {
        sendApiError(err, res);
    }
});

// 6. Customer Segments
router.get('/customer-segments', async (req, res) => {
    try {
        const db = getDatabase(req);
        const result = await db.collection('customers').aggregate(pipelines.pipelineCustomerSegmentation).toArray();
        res.json({ success: true, data: result });
    } catch (err) {
        sendApiError(err, res);
    }
});

// 7. Order Status Distribution
router.get('/order-status', async (req, res) => {
    try {
        const db = getDatabase(req);
        const result = await db.collection('orders').aggregate(pipelines.pipelineOrderStatusFunnel).toArray();
        res.json({ success: true, data: result });
    } catch (err) {
        sendApiError(err, res);
    }
});

// 8. Regional Sales
router.get('/regional-sales', async (req, res) => {
    try {
        const db = getDatabase(req);
        const result = await db.collection('orders').aggregate(pipelines.pipelineRegionalSales).toArray();
        res.json({ success: true, data: result });
    } catch (err) {
        sendApiError(err, res);
    }
});

// 9. Fulfilment Channels
router.get('/fulfilment-analysis', async (req, res) => {
    try {
        const db = getDatabase(req);
        const result = await db.collection('orders').aggregate(pipelines.pipelineFulfilmentChannel).toArray();
        res.json({ success: true, data: result });
    } catch (err) {
        sendApiError(err, res);
    }
});

// 10. Low Performing Products
router.get('/underperforming-products', async (req, res) => {
    try {
        const db = getDatabase(req);
        const result = await db.collection('orders').aggregate(pipelines.pipelineUnderperformingProducts).toArray();
        res.json({ success: true, data: result });
    } catch (err) {
        sendApiError(err, res);
    }
});

module.exports = router;
