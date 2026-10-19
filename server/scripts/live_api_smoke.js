const http = require('node:http');
const app = require('../server');
const { MongoClient } = require('../../mongodb/runtime_dependencies');

async function main() {
    const client = new MongoClient(
        process.env.MONGO_URI || 'mongodb://localhost:27017',
        { serverSelectionTimeoutMS: 5000 }
    );
    let server;
    try {
        await client.connect();
        app.locals.db = client.db(process.env.DB_NAME || 'ecommerce_analytics_db');
        server = http.createServer(app);
        await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));

        const url = `http://127.0.0.1:${server.address().port}/api/analytics/kpis`;
        const response = await fetch(url);
        const payload = await response.json();
        if (!response.ok || !payload.success) {
            throw new Error(`Live KPI endpoint returned HTTP ${response.status}.`);
        }
        const data = payload.data;
        console.log(JSON.stringify({
            http_status: response.status,
            total_sales: data.net_realized_revenue,
            distinct_orders: data.total_orders_count,
            units_sold: data.total_items_sold,
            average_order_value: data.average_order_value
        }, null, 2));
    } finally {
        if (server) {
            await new Promise((resolve, reject) => {
                server.close((error) => error ? reject(error) : resolve());
            });
        }
        await client.close();
    }
}

if (require.main === module) {
    main().catch((error) => {
        console.error(`Live API smoke check failed (${error.name || 'Error'}).`);
        process.exitCode = 1;
    });
}

module.exports = { main };
