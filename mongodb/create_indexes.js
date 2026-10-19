/**
 * MongoDB Index Creation Script (Node.js)
 * Creates strategic single-field and compound indexes on MongoDB collections
 * for optimized analytical query performance, filtering, and joins.
 */

const { MongoClient, dotenv } = require('./runtime_dependencies');
const path = require('path');
dotenv.config({ path: path.join(__dirname, '../server/.env') });

const MONGO_URI = process.env.MONGO_URI || 'mongodb://localhost:27017';
const DB_NAME = process.env.DB_NAME || 'ecommerce_analytics_db';

async function createIndexes() {
    const client = new MongoClient(MONGO_URI);

    try {
        await client.connect();
        const db = client.db(DB_NAME);
        console.log(`Creating indexes on database: ${DB_NAME}...`);

        // 1. Orders Collection Indexes
        console.log('\n1. Creating indexes on "orders" collection:');
        
        // Single-field indexes
        await db.collection('orders').createIndex({ order_item_id: 1 }, { unique: true, name: 'idx_order_item_id' });
        console.log(' - Created unique index: idx_order_item_id');

        await db.collection('orders').createIndex({ order_id: 1 }, { name: 'idx_order_id' });
        console.log(' - Created index: idx_order_id');

        await db.collection('orders').createIndex({ customer_id: 1 }, { name: 'idx_customer_id' });
        console.log(' - Created index: idx_customer_id');

        await db.collection('orders').createIndex({ product_id: 1 }, { name: 'idx_product_id' });
        console.log(' - Created index: idx_product_id');

        await db.collection('orders').createIndex({ order_date: 1 }, { name: 'idx_order_date' });
        console.log(' - Created index: idx_order_date');

        await db.collection('orders').createIndex({ order_status_group: 1 }, { name: 'idx_status_group' });
        console.log(' - Created index: idx_status_group');

        await db.collection('orders').createIndex({ fulfilment_method: 1 }, { name: 'idx_fulfilment' });
        console.log(' - Created index: idx_fulfilment');

        // Compound indexes for high-speed analytical aggregations
        await db.collection('orders').createIndex(
            { order_status_group: 1, net_sales: -1 },
            { name: 'idx_status_revenue' }
        );
        console.log(' - Created compound index: idx_status_revenue');

        await db.collection('orders').createIndex(
            { customer_id: 1, order_date: -1 },
            { name: 'idx_customer_date' }
        );
        console.log(' - Created compound index: idx_customer_date');

        await db.collection('orders').createIndex(
            { region: 1, ship_state: 1, net_sales: -1 },
            { name: 'idx_region_state_sales' }
        );
        console.log(' - Created compound index: idx_region_state_sales');

        // 2. Customers Collection Indexes
        console.log('\n2. Creating indexes on "customers" collection:');
        await db.collection('customers').createIndex({ customer_id: 1 }, { unique: true, name: 'idx_cust_id_pk' });
        console.log(' - Created unique index: idx_cust_id_pk');

        await db.collection('customers').createIndex({ customer_segment: 1, total_spend: -1 }, { name: 'idx_cust_segment_spend' });
        console.log(' - Created compound index: idx_cust_segment_spend');

        await db.collection('customers').createIndex({ state: 1, region: 1 }, { name: 'idx_cust_geo' });
        console.log(' - Created compound index: idx_cust_geo');

        // 3. Products Collection Indexes
        console.log('\n3. Creating indexes on "products" collection:');
        await db.collection('products').createIndex({ product_id: 1 }, { unique: true, name: 'idx_prod_id_pk' });
        console.log(' - Created unique index: idx_prod_id_pk');

        await db.collection('products').createIndex({ category: 1, net_revenue: -1 }, { name: 'idx_prod_cat_rev' });
        console.log(' - Created compound index: idx_prod_cat_rev');

        // 4. Date dimension primary key
        console.log('\n4. Creating indexes on "dates" collection:');
        await db.collection('dates').createIndex({ date_key: 1 }, { unique: true, name: 'idx_date_key_pk' });
        console.log(' - Created unique index: idx_date_key_pk');

        console.log('\nAll indexes created successfully!');
    } catch (err) {
        console.error(`Index creation failed (${err.name || 'Error'}).`);
        process.exitCode = 1;
    } finally {
        await client.close();
    }
}

if (require.main === module) {
    createIndexes();
}

module.exports = { createIndexes };
