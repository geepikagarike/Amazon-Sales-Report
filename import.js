require('dotenv').config();

const { MongoClient } = require('mongodb');
const csv = require('csvtojson');
const path = require('path');

const uri = process.env.MONGO_URI?.trim();
const client = new MongoClient(uri);

const csvFilePath = path.join(__dirname, 'Amazon Sale Report.csv');

async function run() {
  try {
    await client.connect();
    console.log("Connected to MongoDB");

    const db = client.db("amazonSalesDB");
    const collection = db.collection("orders");

    const jsonArray = await csv().fromFile(csvFilePath);
    const result = await collection.insertMany(jsonArray);

    console.log(`Inserted ${result.insertedCount} records.`);
  } catch (err) {
    console.error("Error:", err);
  } finally {
    await client.close();
  }
}

run();

