/**
 * E-Commerce Order Management & Tracking API Server
 * Built with Node.js, Express.js, and MongoDB.
 */

const express = require('express');
const cors = require('cors');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '.env') });

const { connectDatabase, closeDatabase, getDb, DB_NAME } = require('./config/database');
const orderRoutes = require('./routes/orderRoutes');
const analyticsRoutes = require('./routes/analytics');
const errorHandler = require('./middleware/errorHandler');

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(express.json({ limit: '1mb' }));

// Health Check Endpoints
function healthHandler(req, res) {
    const isOnline = Boolean(req.app.locals.db || getDb());
    res.json({
        status: isOnline ? 'online' : 'database_unavailable',
        service: 'E-Commerce Order Management & Tracking API',
        database: DB_NAME,
        timestamp: new Date().toISOString()
    });
}

app.get('/health', healthHandler);
app.get('/api/health', healthHandler);

// API Routes
app.use('/api/orders', orderRoutes);
app.use('/api/analytics', analyticsRoutes);

// 404 Route Handler for undefined endpoints
app.use((req, res, next) => {
    res.status(404).json({
        success: false,
        error: `Endpoint '${req.method} ${req.originalUrl}' not found.`
    });
});

// Centralized Error Handling Middleware
app.use(errorHandler);

// MongoDB Connection & Server Initialization
async function startServer() {
    try {
        const db = await connectDatabase();
        app.locals.db = db;

        const server = app.listen(PORT, () => {
            console.log(`====================================================`);
            console.log(`ORDER MANAGEMENT & TRACKING API RUNNING ON PORT ${PORT}`);
            console.log(`Health Check:   http://localhost:${PORT}/health`);
            console.log(`Order Tracker:  http://localhost:${PORT}/api/orders`);
            console.log(`Analytics KPIs: http://localhost:${PORT}/api/analytics/kpis`);
            console.log(`====================================================`);
        });

        // Graceful shutdown
        const shutdown = async (signal) => {
            console.log(`\nReceived ${signal}. Gracefully shutting down server...`);
            server.close(async () => {
                await closeDatabase();
                console.log('HTTP server closed.');
                process.exit(0);
            });
        };

        process.on('SIGINT', () => shutdown('SIGINT'));
        process.on('SIGTERM', () => shutdown('SIGTERM'));
    } catch (err) {
        console.error('Failed to start server. Verify MongoDB availability and environment configuration.');
        process.exitCode = 1;
    }
}

if (require.main === module) {
    startServer();
}

module.exports = app;
