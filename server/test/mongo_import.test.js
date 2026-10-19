const assert = require('node:assert/strict');
const test = require('node:test');

const { mapCsvRecord, upsertRecords } = require('../../mongodb/import_data');

test('Mongo CSV mapper preserves null measures and maps actual fact columns', () => {
    const document = mapCsvRecord('orders', {
        Order_Item_ID: 'I-1',
        Order_ID: 'O-1',
        Customer_ID: 'C-1',
        Product_ID: 'P-1',
        Order_Date: '2024-01-03',
        Quantity: '2',
        Net_Sales: '',
        Order_Status_Group: 'Delivered',
        Is_B2B: 'False'
    });
    assert.equal(document.order_item_id, 'I-1');
    assert.equal(document.quantity, 2);
    assert.equal(document.net_sales, null);
    assert.equal(document.is_b2b, false);
    assert.equal(document.order_date, '2024-01-03');
});

test('repeated Node imports use source-keyed upserts and never delete collections', async () => {
    const writes = [];
    const db = {
        collection(name) {
            assert.equal(name, 'orders');
            return {
                async createIndex(field, options) {
                    assert.equal(field, 'order_item_id');
                    assert.equal(options.unique, true);
                },
                async bulkWrite(operations, options) {
                    assert.equal(options.ordered, false);
                    writes.push(...operations);
                }
            };
        }
    };
    const document = { order_item_id: 'I-1', order_id: 'O-1' };
    assert.equal(await upsertRecords(db, 'orders', [document]), 1);
    assert.equal(await upsertRecords(db, 'orders', [document]), 1);
    assert.equal(writes.length, 2);
    assert.ok(writes.every((operation) => operation.updateOne.upsert));
    assert.deepEqual(writes[0].updateOne.filter, { order_item_id: 'I-1' });
});

const { normalizeCsvRow, importOrdersFromCsv } = require('../scripts/importOrders');

test('importOrders normalizeCsvRow correctly maps fact columns and rejects invalid records', () => {
    const validRow = {
        Order_Item_ID: 'ITEM-TEST-1',
        Order_ID: 'ORD-TEST-1',
        Customer_ID: 'CUST-1',
        Product_ID: 'PROD-1',
        Order_Date: '2022-05-01',
        Quantity: '2',
        Unit_Price: '450.50',
        Gross_Amount: '901.00',
        Net_Sales: '901.00',
        Order_Status_Group: 'Shipped',
        Courier_Status: 'Shipped',
        Fulfilment_Method: 'Amazon',
        Ship_City: 'Mumbai',
        Ship_State: 'Maharashtra',
        Region: 'West',
        Is_B2B: 'False'
    };
    const res = normalizeCsvRow(validRow);
    assert.equal(res.valid, true);
    assert.equal(res.document.order_item_id, 'ITEM-TEST-1');
    assert.equal(res.document.quantity, 2);
    assert.equal(res.document.unit_price, 450.50);
    assert.equal(res.document.gross_amount, 901.00);
    assert.equal(res.document.is_b2b, false);
    assert.equal(res.document.is_deleted, false);

    // Missing identifier
    const invalidRow = { ...validRow, Order_ID: '' };
    const invalidRes = normalizeCsvRow(invalidRow);
    assert.equal(invalidRes.valid, false);
    assert.match(invalidRes.error, /Missing required identifier/);

    // Invalid negative quantity
    const negativeQtyRow = { ...validRow, Quantity: '-5' };
    const negativeRes = normalizeCsvRow(negativeQtyRow);
    assert.equal(negativeRes.valid, false);
    assert.match(negativeRes.error, /Invalid quantity/);
});

test('importOrders requires explicit database configuration when not in dry-run mode', async () => {
    const originalUri = process.env.MONGODB_URI;
    const originalMongoUri = process.env.MONGO_URI;
    delete process.env.MONGODB_URI;
    delete process.env.MONGO_URI;

    try {
        await assert.rejects(
            async () => {
                await importOrdersFromCsv(__filename, { dryRun: false });
            },
            {
                message: /Explicit MongoDB configuration required/
            }
        );
    } finally {
        if (originalUri) process.env.MONGODB_URI = originalUri;
        if (originalMongoUri) process.env.MONGO_URI = originalMongoUri;
    }
});

