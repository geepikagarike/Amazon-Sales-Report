/**
 * Non-destructive MongoDB CSV import. Existing documents are updated by their
 * source primary key; records absent from the CSV are never deleted.
 */

const fs = require('fs');
const path = require('path');
const { MongoClient, csvParser: csv, dotenv } = require('./runtime_dependencies');
dotenv.config({ path: path.join(__dirname, '../server/.env') });

const MONGO_URI = process.env.MONGO_URI || 'mongodb://localhost:27017';
const DB_NAME = process.env.DB_NAME || 'ecommerce_analytics_db';
const DATA_DIR = path.join(__dirname, '../data/cleaned');
const COLLECTION_KEYS = {
    products: 'product_id',
    customers: 'customer_id',
    dates: 'date_key',
    orders: 'order_item_id'
};

function readCsv(filePath) {
    return new Promise((resolve, reject) => {
        const results = [];
        fs.createReadStream(filePath)
            .pipe(csv())
            .on('data', (data) => results.push(data))
            .on('end', () => resolve(results))
            .on('error', reject);
    });
}

function parseNumber(value, integer = false) {
    if (value === undefined || value === null || value.trim() === '') return null;
    const parsed = Number(value);
    if (!Number.isFinite(parsed) || (integer && !Number.isInteger(parsed))) {
        throw new Error(`Invalid ${integer ? 'integer' : 'number'} value in CSV: ${value}`);
    }
    return parsed;
}

function parseBoolean(value) {
    if (value === undefined || value === null || value.trim() === '') return null;
    if (['true', '1'].includes(value.trim().toLowerCase())) return true;
    if (['false', '0'].includes(value.trim().toLowerCase())) return false;
    throw new Error(`Invalid boolean value in CSV: ${value}`);
}

function mapCsvRecord(collectionName, row) {
    const mappings = {
        products: {
            Product_ID: ['product_id', 'string'],
            Product_Name: ['product_name', 'string'],
            Category: ['category', 'string'],
            Size: ['size', 'string'],
            Unit_MSRP: ['unit_msrp', 'number'],
            Unit_Cost: ['unit_cost', 'number'],
            Total_Units_Sold: ['total_units_sold', 'integer'],
            Gross_Revenue: ['gross_revenue', 'number'],
            Net_Revenue: ['net_revenue', 'number']
        },
        customers: {
            Customer_ID: ['customer_id', 'string'],
            Customer_Name: ['customer_name', 'string'],
            Customer_Segment: ['customer_segment', 'string'],
            Is_B2B: ['is_b2b', 'boolean'],
            City: ['city', 'string'],
            State: ['state', 'string'],
            Region: ['region', 'string'],
            Postal_Code: ['postal_code', 'integer'],
            Total_Orders: ['total_orders', 'integer'],
            Total_Spend: ['total_spend', 'number'],
            Gross_Spend: ['gross_spend', 'number'],
            First_Order_Date: ['first_order_date', 'date'],
            Last_Order_Date: ['last_order_date', 'date']
        },
        dates: {
            Date_Key: ['date_key', 'integer'],
            Full_Date: ['full_date', 'date'],
            Date_ISO: ['date_iso', 'date'],
            Year: ['year', 'integer'],
            Quarter: ['quarter', 'string'],
            Month_Number: ['month_number', 'integer'],
            Month_Name: ['month_name', 'string'],
            Year_Month: ['year_month', 'string'],
            Day_Of_Month: ['day_of_month', 'integer'],
            Day_Of_Week: ['day_of_week', 'string'],
            Is_Weekend: ['is_weekend', 'boolean']
        },
        orders: {
            Order_Item_ID: ['order_item_id', 'string'],
            Order_ID: ['order_id', 'string'],
            Customer_ID: ['customer_id', 'string'],
            Product_ID: ['product_id', 'string'],
            Order_Date: ['order_date', 'date'],
            Year: ['year', 'integer'],
            Month_Name: ['month_name', 'string'],
            Quarter: ['quarter', 'string'],
            Order_Status: ['order_status', 'string'],
            Order_Status_Group: ['order_status_group', 'string'],
            Courier_Status: ['courier_status', 'string'],
            Fulfilment_Method: ['fulfilment_method', 'string'],
            Fulfilled_By: ['fulfilled_by', 'string'],
            Sales_Channel: ['sales_channel', 'string'],
            Ship_Service_Level: ['ship_service_level', 'string'],
            Quantity: ['quantity', 'integer'],
            Unit_Price: ['unit_price', 'number'],
            Gross_Amount: ['gross_amount', 'number'],
            Net_Sales: ['net_sales', 'number'],
            COGS: ['cogs', 'number'],
            Gross_Profit: ['gross_profit', 'number'],
            Profit_Margin_Pct: ['profit_margin_pct', 'number'],
            Is_B2B: ['is_b2b', 'boolean'],
            Ship_City: ['ship_city', 'string'],
            Ship_State: ['ship_state', 'string'],
            Region: ['region', 'string'],
            Ship_Postal_Code: ['ship_postal_code', 'integer'],
            Is_New_Record: ['is_new_record', 'boolean']
        }
    };
    const mapping = mappings[collectionName];
    if (!mapping) throw new Error(`Unsupported MongoDB collection: ${collectionName}`);
    const document = {};
    for (const [source, [target, kind]] of Object.entries(mapping)) {
        const value = row[source];
        if (kind === 'integer') document[target] = parseNumber(value, true);
        else if (kind === 'number') document[target] = parseNumber(value);
        else if (kind === 'boolean') document[target] = parseBoolean(value);
        else if (kind === 'date') {
            document[target] = value && value.trim() ? value.trim().slice(0, 10) : null;
        } else {
            document[target] = value === undefined || value === '' ? null : value;
        }
    }
    const key = document[COLLECTION_KEYS[collectionName]];
    if (key === null || key === undefined || key === '') {
        throw new Error(`CSV row has no valid key for collection ${collectionName}`);
    }
    return document;
}

async function upsertRecords(db, collectionName, documents, batchSize = 1000) {
    if (!Number.isInteger(batchSize) || batchSize < 1) {
        throw new RangeError('batchSize must be a positive integer');
    }
    const keyFieldByCollection = {
        orders: 'order_item_id',
        products: 'product_id',
        customers: 'customer_id',
        dates: 'date_key'
    };
    const keyField = keyFieldByCollection[collectionName];
    if (!keyField) throw new Error(`Unsupported MongoDB collection: ${collectionName}`);
    const collection = db.collection(collectionName);
    const indexNames = {
        orders: 'idx_order_item_id',
        products: 'idx_prod_id_pk',
        customers: 'idx_cust_id_pk',
        dates: 'idx_date_key_pk'
    };
    await collection.createIndex(keyField, {
        unique: true,
        name: indexNames[collectionName]
    });
    for (let start = 0; start < documents.length; start += batchSize) {
        const batch = documents.slice(start, start + batchSize);
        const operations = batch.map((document) => {
            if (document[keyField] === null || document[keyField] === undefined) {
                throw new Error(`${collectionName} document is missing ${keyField}`);
            }
            return {
                updateOne: {
                    filter: { [keyField]: document[keyField] },
                    update: { $set: document },
                    upsert: true
                }
            };
        });
        if (operations.length) await collection.bulkWrite(operations, { ordered: false });
    }
    return documents.length;
}

async function importDataset() {
    const client = new MongoClient(MONGO_URI, { serverSelectionTimeoutMS: 5000 });
    try {
        await client.connect();
        const db = client.db(DB_NAME);
        const files = {
            products: 'dim_products.csv',
            customers: 'dim_customers.csv',
            dates: 'dim_dates.csv',
            orders: 'fact_orders.csv'
        };
        const result = {};
        for (const [collectionName, fileName] of Object.entries(files)) {
            const sourcePath = path.join(DATA_DIR, fileName);
            const rows = await readCsv(sourcePath);
            const documents = rows.map((row) => mapCsvRecord(collectionName, row));
            result[collectionName] = await upsertRecords(db, collectionName, documents);
            console.log(`${collectionName}: upserted ${documents.length} source records`);
        }
        console.log('Import complete. Existing documents absent from the CSV files were retained.');
        return result;
    } finally {
        await client.close();
    }
}

if (require.main === module) {
    importDataset().catch((error) => {
        console.error(`MongoDB import failed: ${error.message}`);
        process.exitCode = 1;
    });
}

module.exports = { importDataset, mapCsvRecord, readCsv, upsertRecords };
