"""Non-destructively upsert cleaned star-schema data into MongoDB."""

from __future__ import annotations

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from src.mongo_integration import get_db_name, get_mongo_uri, upsert_mongo_tables


def import_to_mongodb(client: MongoClient | None = None) -> dict[str, int]:
    owns_client = client is None
    mongo_client = client or MongoClient(get_mongo_uri(), serverSelectionTimeoutMS=5000)
    try:
        mongo_client.admin.command("ping")
        database = mongo_client[get_db_name()]
        counts = upsert_mongo_tables(database)
        print(f"Upserted source records by stable keys into database {get_db_name()}: {counts}")
        print("Existing MongoDB documents not present in the CSV inputs were retained.")
        return counts
    except PyMongoError:
        print("MongoDB import failed: unable to connect or write. Check the MongoDB service and environment configuration.")
        raise
    finally:
        if owns_client:
            mongo_client.close()


if __name__ == "__main__":
    import_to_mongodb()
