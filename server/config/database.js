/**
 * Database Configuration & Connection Module
 * Connects to MongoDB Atlas or local MongoDB using the native MongoDB driver.
 * Validates configuration, handles connection errors gracefully, and supports clean shutdown.
 */

const { MongoClient } = require('mongodb');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '../.env') });

const MONGO_URI = process.env.MONGO_URI || 'mongodb://localhost:27017';
const DB_NAME = process.env.DB_NAME || 'ecommerce_analytics_db';

let client = null;
let database = null;

/**
 * Validates MongoDB connection URI format without exposing credentials.
 * @param {string} uri 
 * @returns {boolean}
 */
function validateMongoUri(uri) {
    if (!uri || typeof uri !== 'string') return false;
    return uri.startsWith('mongodb://') || uri.startsWith('mongodb+srv://');
}

/**
 * Mask credentials in URI for safe logging.
 * @param {string} uri 
 * @returns {string}
 */
function maskMongoUri(uri) {
    if (!uri) return '';
    try {
        return uri.replace(/\/\/(.*?)@/, '//***:***@');
    } catch {
        return 'mongodb://[credentials-masked]';
    }
}

/**
 * Connects to MongoDB and returns database handle.
 * @param {object} options
 * @returns {Promise<Db>}
 */
async function connectDatabase(options = {}) {
    if (database) return database;

    if (!validateMongoUri(MONGO_URI)) {
        throw new Error('Invalid MONGO_URI configuration. Must start with mongodb:// or mongodb+srv://');
    }

    const connectTimeoutMS = options.serverSelectionTimeoutMS || 5000;
    client = new MongoClient(MONGO_URI, {
        serverSelectionTimeoutMS: connectTimeoutMS,
        ...options
    });

    try {
        console.log(`Connecting to MongoDB at ${maskMongoUri(MONGO_URI)}...`);
        await client.connect();
        database = client.db(DB_NAME);
        console.log(`Successfully connected to database: ${DB_NAME}`);
        return database;
    } catch (err) {
        console.error(`MongoDB connection failed (${err.name || 'Error'}).`);
        if (client) {
            await client.close().catch(() => {});
            client = null;
        }
        database = null;
        throw err;
    }
}

/**
 * Returns current database instance if connected.
 * @returns {Db|null}
 */
function getDb() {
    return database;
}

/**
 * Injects a database instance (useful for testing and dependency injection).
 * @param {Db|null} db 
 */
function setDb(db) {
    database = db;
}

/**
 * Gracefully close the MongoDB client connection.
 */
async function closeDatabase() {
    if (client) {
        await client.close().catch(() => {});
        client = null;
        database = null;
        console.log('MongoDB connection closed.');
    }
}

module.exports = {
    connectDatabase,
    closeDatabase,
    getDb,
    setDb,
    validateMongoUri,
    maskMongoUri,
    MONGO_URI,
    DB_NAME
};
