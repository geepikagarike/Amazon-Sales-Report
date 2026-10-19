const path = require('path');
const { createRequire } = require('module');

const requireServerDependency = createRequire(path.join(__dirname, '../server/package.json'));

module.exports = {
    MongoClient: requireServerDependency('mongodb').MongoClient,
    csvParser: requireServerDependency('csv-parser'),
    dotenv: requireServerDependency('dotenv')
};
