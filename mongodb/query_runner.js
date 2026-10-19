/**
 * MongoDB Aggregation Query Runner
 * Executes all analytical aggregation pipelines and displays formatted results.
 */

const { MongoClient, dotenv } = require('./runtime_dependencies');
const path = require('path');
const pipelines = require('./aggregation_queries');
dotenv.config({ path: path.join(__dirname, '../server/.env') });

const MONGO_URI = process.env.MONGO_URI || 'mongodb://localhost:27017';
const DB_NAME = process.env.DB_NAME || 'ecommerce_analytics_db';

async function runAllQueries() {
    console.log('======================================================================');
    console.log('EXECUTING MONGODB ANALYTICS AGGREGATION PIPELINES');
    console.log('======================================================================\n');

    const client = new MongoClient(MONGO_URI);

    try {
        await client.connect();
        const db = client.db(DB_NAME);

        // 1. Executive KPIs
        console.log('1. [BUSINESS KPI] Executive Performance Summary:');
        const kpis = await db.collection('orders').aggregate(pipelines.pipelineExecutiveKPIs).toArray();
        console.table(kpis);

        // 2. Monthly Trend
        console.log('\n2. [TREND] Monthly Sales & Revenue Performance:');
        const monthly = await db.collection('orders').aggregate(pipelines.pipelineMonthlySalesTrend).toArray();
        console.table(monthly);

        // 3. Category Breakdown
        console.log('\n3. [CATEGORY] Product Category Revenue & Unit Breakdown:');
        const categories = await db.collection('orders').aggregate(pipelines.pipelineCategoryPerformance).toArray();
        console.table(categories);

        // 4. Top Products
        console.log('\n4. [PRODUCTS] Top 10 Revenue-Generating Product SKUs:');
        const topProducts = await db.collection('orders').aggregate(pipelines.pipelineTopProducts).toArray();
        console.table(topProducts);

        // 5. Top Customers
        console.log('\n5. [CUSTOMERS] Top 10 High-Spending Customer Accounts:');
        const topCust = await db.collection('orders').aggregate(pipelines.pipelineTopCustomers).toArray();
        console.table(topCust);

        // 6. Customer Segments
        console.log('\n6. [SEGMENTATION] Customer Spending Tiers Distribution:');
        const segments = await db.collection('customers').aggregate(pipelines.pipelineCustomerSegmentation).toArray();
        console.table(segments);

        // 7. Order Status Funnel
        console.log('\n7. [OPERATIONS] Order Fulfillment & Status Breakdown:');
        const funnel = await db.collection('orders').aggregate(pipelines.pipelineOrderStatusFunnel).toArray();
        console.table(funnel);

        // 8. Fulfilment Channels
        console.log('\n8. [LOGISTICS] Fulfilment Channel Performance (Amazon FBA vs Merchant):');
        const channels = await db.collection('orders').aggregate(pipelines.pipelineFulfilmentChannel).toArray();
        console.table(channels);

        // 9. Low Performing Products
        console.log('\n9. [INVENTORY] Low-Performing / Tail SKUs (Requiring Marketing Action):');
        const lowProds = await db.collection('orders').aggregate(pipelines.pipelineUnderperformingProducts).toArray();
        console.table(lowProds);

        console.log('\n======================================================================');
        console.log('ALL MONGODB AGGREGATION QUERIES EXECUTED SUCCESSFULLY!');
        console.log('======================================================================');
    } catch (err) {
        console.error(`MongoDB analytics queries failed (${err.name || 'Error'}).`);
        process.exitCode = 1;
    } finally {
        await client.close();
    }
}

if (require.main === module) {
    runAllQueries();
}

module.exports = { runAllQueries };
