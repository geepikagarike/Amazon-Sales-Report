/**
 * Order CSV Importer Script
 * Safely validates, normalizes, and upserts order records from CSV into MongoDB.
 * 
 * Features:
 * - Validates schema and column headers before importing.
 * - Non-destructive: uses stable key 'order_item_id' for idempotent upserts.
 * - Bounded batch processing (bulkWrite in batches of 1,000).
 * - Comprehensive reporting of inserted, updated, and rejected records.
 * - Supports dry-run mode (--dry-run).
 */

const fs = require('fs');
const path = require('path');
const readline = require('readline');
const { MongoClient } = require('mongodb');
require('dotenv').config({ path: path.join(__dirname, '../.env') });

function getMongoUri(options = {}) {
    return options.mongoUri || process.env.MONGODB_URI || process.env.MONGO_URI;
}

function getDbName(options = {}) {
    return options.dbName || process.env.MONGODB_DB_NAME || process.env.DB_NAME || 'ecommerce_analytics_db';
}

function maskUri(uri) {
    if (!uri) return '';
    try {
        return uri.replace(/\/\/(.*?)@/, '//***:***@');
    } catch {
        return 'mongodb://[credentials-masked]';
    }
}

const DEFAULT_CSV_PATH = path.join(__dirname, '../../data/cleaned/fact_orders.csv');

const REQUIRED_HEADERS = ['Order_Item_ID', 'Order_ID', 'Customer_ID', 'Product_ID'];

/**
 * Parses CSV line accounting for quoted commas.
 * @param {string} line 
 * @returns {string[]}
 */
function parseCsvLine(line) {
    const result = [];
    let current = '';
    let inQuotes = false;
    for (let i = 0; i < line.length; i++) {
        const char = line[i];
        if (char === '"') {
            inQuotes = !inQuotes;
        } else if (char === ',' && !inQuotes) {
            result.push(current.trim());
            current = '';
        } else {
            current += char;
        }
    }
    result.push(current.trim());
    return result;
}

/**
 * Normalizes a CSV row into an order document.
 * @param {object} row 
 * @returns {{ valid: boolean, document?: object, error?: string }}
 */
function normalizeCsvRow(row) {
    const orderItemId = (row.Order_Item_ID || row.order_item_id || '').trim();
    const orderId = (row.Order_ID || row.order_id || '').trim();
    const customerId = (row.Customer_ID || row.customer_id || '').trim();
    const productId = (row.Product_ID || row.product_id || '').trim();

    if (!orderItemId || !orderId || !customerId || !productId) {
        return {
            valid: false,
            error: 'Missing required identifier (Order_Item_ID, Order_ID, Customer_ID, or Product_ID)'
        };
    }

    const rawQty = row.Quantity || row.quantity;
    const quantity = parseInt(rawQty, 10);
    if (!Number.isInteger(quantity) || quantity < 0) {
        return { valid: false, error: `Invalid quantity '${rawQty}'` };
    }

    const parseNum = (val) => {
        if (val === undefined || val === null || val === '') return 0.0;
        const num = parseFloat(val);
        return Number.isFinite(num) ? num : 0.0;
    };

    const statusGroup = (row.Order_Status_Group || row.order_status_group || 'Pending').trim();
    const isB2B = ['true', '1'].includes(String(row.Is_B2B || row.is_b2b).toLowerCase());

    const document = {
        order_item_id: orderItemId,
        order_id: orderId,
        customer_id: customerId,
        product_id: productId,
        order_date: (row.Order_Date || row.order_date || new Date().toISOString().slice(0, 10)).trim(),
        order_status: (row.Order_Status || row.order_status || statusGroup).trim(),
        order_status_group: statusGroup,
        courier_status: (row.Courier_Status || row.courier_status || 'Pending').trim(),
        fulfilment_method: (row.Fulfilment_Method || row.fulfilment_method || 'Amazon').trim(),
        fulfilled_by: (row.Fulfilled_By || row.fulfilled_by || '').trim() || undefined,
        sales_channel: (row.Sales_Channel || row.sales_channel || 'Amazon.in').trim(),
        ship_service_level: (row.Ship_Service_Level || row.ship_service_level || 'Standard').trim(),
        quantity,
        unit_price: parseNum(row.Unit_Price || row.unit_price),
        gross_amount: parseNum(row.Gross_Amount || row.gross_amount),
        net_sales: parseNum(row.Net_Sales || row.net_sales),
        cogs: parseNum(row.COGS || row.cogs),
        gross_profit: parseNum(row.Gross_Profit || row.gross_profit),
        profit_margin_pct: parseNum(row.Profit_Margin_Pct || row.profit_margin_pct),
        is_b2b: isB2B,
        ship_city: (row.Ship_City || row.ship_city || '').trim() || undefined,
        ship_state: (row.Ship_State || row.ship_state || '').trim() || undefined,
        region: (row.Region || row.region || '').trim() || undefined,
        ship_postal_code: parseInt(row.Ship_Postal_Code || row.ship_postal_code, 10) || undefined,
        is_deleted: false,
        updated_at: new Date()
    };

    return { valid: true, document };
}

/**
 * Runs CSV import process.
 * @param {string} filePath 
 * @param {object} options 
 * @returns {Promise<object>} Import summary
 */
async function importOrdersFromCsv(filePath = DEFAULT_CSV_PATH, options = {}) {
    const isDryRun = options.dryRun || process.argv.includes('--dry-run');
    const batchSize = options.batchSize || 1000;

    if (!fs.existsSync(filePath)) {
        throw new Error(`CSV file not found: ${filePath}`);
    }

    console.log(`Starting CSV Order import from: ${filePath}`);
    console.log(`Mode: ${isDryRun ? 'DRY-RUN (Validation only)' : 'LIVE IMPORT'}`);

    const fileStream = fs.createReadStream(filePath);
    const rl = readline.createInterface({
        input: fileStream,
        crlfDelay: Infinity
    });

    let headers = null;
    let totalProcessed = 0;
    let validRecords = 0;
    let rejectedRecords = 0;
    const rejections = [];
    const batch = [];

    let client = null;
    let collection = null;

    if (!isDryRun) {
        const targetUri = getMongoUri(options);
        const targetDbName = getDbName(options);

        if (!targetUri) {
            throw new Error(
                'Explicit MongoDB configuration required for live import. ' +
                'Please set MONGODB_URI (or MONGO_URI) in server/.env or environment variables.'
            );
        }

        if (!targetUri.startsWith('mongodb://') && !targetUri.startsWith('mongodb+srv://')) {
            throw new Error('Invalid connection URI: must start with mongodb:// or mongodb+srv://');
        }

        console.log(`Connecting to database at: ${maskUri(targetUri)} (DB: ${targetDbName})`);
        client = new MongoClient(targetUri, { serverSelectionTimeoutMS: 5000 });
        await client.connect();
        const db = client.db(targetDbName);
        collection = db.collection('orders');

        // Ensure unique index
        await collection.createIndex({ order_item_id: 1 }, { unique: true, name: 'idx_order_item_id' });
    }

    const startTime = Date.now();

    try {
        for await (const line of rl) {
            if (!line.trim()) continue;

            if (!headers) {
                headers = parseCsvLine(line);
                const missing = REQUIRED_HEADERS.filter(h => !headers.includes(h));
                if (missing.length) {
                    throw new Error(`CSV is missing required headers: ${missing.join(', ')}`);
                }
                continue;
            }

            totalProcessed++;
            const values = parseCsvLine(line);
            const row = {};
            headers.forEach((h, idx) => {
                row[h] = values[idx] || '';
            });

            const result = normalizeCsvRow(row);
            if (!result.valid) {
                rejectedRecords++;
                if (rejections.length < 10) {
                    rejections.push({ line: totalProcessed + 1, error: result.error });
                }
                continue;
            }

            validRecords++;
            if (!isDryRun) {
                batch.push({
                    updateOne: {
                        filter: { order_item_id: result.document.order_item_id },
                        update: { $set: result.document, $setOnInsert: { created_at: new Date() } },
                        upsert: true
                    }
                });

                if (batch.length >= batchSize) {
                    await collection.bulkWrite(batch, { ordered: false });
                    batch.length = 0;
                    process.stdout.write(`Processed ${totalProcessed} rows...\r`);
                }
            }
        }

        if (!isDryRun && batch.length > 0) {
            await collection.bulkWrite(batch, { ordered: false });
            batch.length = 0;
        }

        const elapsedSeconds = ((Date.now() - startTime) / 1000).toFixed(2);
        const summary = {
            status: 'COMPLETED',
            dryRun: isDryRun,
            file: filePath,
            totalProcessed,
            validRecords,
            rejectedRecords,
            rejectionSamples: rejections,
            elapsedSeconds: parseFloat(elapsedSeconds)
        };

        console.log('\n========================================');
        console.log('CSV ORDER IMPORT SUMMARY:');
        console.log(` - Total rows evaluated: ${summary.totalProcessed}`);
        console.log(` - Valid & queued:       ${summary.validRecords}`);
        console.log(` - Rejected invalid:     ${summary.rejectedRecords}`);
        console.log(` - Duration:             ${summary.elapsedSeconds}s`);
        console.log('========================================');

        return summary;
    } finally {
        if (client) {
            await client.close();
        }
    }
}

if (require.main === module) {
    const targetFile = process.argv[2] && !process.argv[2].startsWith('--')
        ? process.argv[2]
        : DEFAULT_CSV_PATH;

    importOrdersFromCsv(targetFile)
        .then(() => process.exit(0))
        .catch((err) => {
            console.error(`Import execution error: ${err.message}`);
            process.exit(1);
        });
}

module.exports = {
    parseCsvLine,
    normalizeCsvRow,
    importOrdersFromCsv,
    DEFAULT_CSV_PATH
};
