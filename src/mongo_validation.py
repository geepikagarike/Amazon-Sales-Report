from __future__ import annotations

import argparse
from typing import Any

import pandas as pd
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from src.analytics_validation import _python_metrics
from src.mongo_integration import get_db_name, get_mongo_uri, load_cleaned_tables

REQUIRED_FIELDS = {
    "orders": {
        "order_item_id": "string",
        "order_id": "string",
        "customer_id": "string",
        "product_id": "string",
        "order_status_group": "string",
        "order_date": "string",
        "quantity": ("int", "long"),
        "gross_amount": ("int", "long", "double", "decimal"),
        "net_sales": ("int", "long", "double", "decimal"),
        "is_b2b": "bool",
    },
    "products": {
        "product_id": "string",
        "category": "string",
        "net_revenue": ("int", "long", "double", "decimal"),
    },
    "customers": {
        "customer_id": "string",
        "total_orders": ("int", "long"),
        "total_spend": ("int", "long", "double", "decimal"),
    },
    "dates": {
        "date_key": ("int", "long"),
        "date_iso": "string",
        "year_month": "string",
    },
}

REQUIRED_INDEX_NAMES = {
    "orders": {"idx_order_item_id", "idx_order_id", "idx_product_id", "idx_order_date"},
    "products": {"idx_prod_id_pk"},
    "customers": {"idx_cust_id_pk"},
    "dates": {"idx_date_key_pk"},
}


def _field_type_query(field: str, expected_types: str | tuple[str, ...]) -> dict[str, Any]:
    allowed = (expected_types,) if isinstance(expected_types, str) else expected_types
    return {"$nor": [{field: {"$type": bson_type}} for bson_type in allowed]}


def validate_mongodb(
    client: Any | None = None,
    tables: dict[str, pd.DataFrame] | None = None,
) -> dict[str, Any]:
    """Run read-only MongoDB checks and return SKIPPED when no server is reachable."""
    source_tables = tables if tables is not None else load_cleaned_tables()
    own_client = client is None
    mongo_client = client
    if own_client:
        mongo_client = MongoClient(get_mongo_uri(), serverSelectionTimeoutMS=5000)

    try:
        mongo_client.admin.command("ping")
    except PyMongoError:
        if own_client:
            mongo_client.close()
        return {
            "status": "SKIPPED",
            "reason": "MongoDB server could not be reached; no live database claims were validated.",
            "collections": {},
            "kpi_comparison": [],
        }

    try:
        database = mongo_client[get_db_name()]
        collection_results: dict[str, Any] = {}
        for collection_name, field_types in REQUIRED_FIELDS.items():
            collection = database[collection_name]
            expected_count = len(source_tables.get(collection_name, pd.DataFrame()))
            actual_count = collection.count_documents({})
            fields = {}
            for field_name, expected_types in field_types.items():
                missing_count = collection.count_documents(
                    {"$or": [{field_name: {"$exists": False}}, {field_name: None}]}
                )
                wrong_type_count = collection.count_documents(
                    _field_type_query(field_name, expected_types)
                )
                fields[field_name] = {
                    "missing_or_null": missing_count,
                    "wrong_type": wrong_type_count,
                    "valid": missing_count == 0 and wrong_type_count == 0,
                }

            index_names = set(collection.index_information())
            expected_indexes = REQUIRED_INDEX_NAMES[collection_name]
            collection_results[collection_name] = {
                "expected_document_count": expected_count,
                "actual_document_count": actual_count,
                "document_count_match": expected_count == actual_count,
                "required_fields": fields,
                "missing_indexes": sorted(expected_indexes - index_names),
            }

        expected_fact = source_tables.get("orders", pd.DataFrame())
        expected_products = source_tables.get("products", pd.DataFrame())
        expected = _python_metrics(expected_fact, expected_products) if not expected_fact.empty else {
            "total_sales": 0.0,
            "distinct_orders": 0,
            "units_sold": 0.0,
        }
        orders = database["orders"]
        aggregation = list(
            orders.aggregate(
                [
                    {"$match": {"is_deleted": {"$ne": True}}},
                    {
                        "$group": {
                            "_id": None,
                            "total_sales": {"$sum": "$net_sales"},
                            "units_sold": {
                                "$sum": {
                                    "$cond": [
                                        {"$in": ["$order_status_group", ["Delivered", "Shipped"]]},
                                        {"$ifNull": ["$quantity", 0]},
                                        0,
                                    ]
                                }
                            },
                        }
                    }
                ]
            )
        )
        aggregate_values = aggregation[0] if aggregation else {"total_sales": 0.0, "units_sold": 0.0}
        actual_orders = int(
            orders.count_documents({"order_id": {"$type": "string"}, "is_deleted": {"$ne": True}})
        ) if expected["distinct_orders"] == 0 else len(
            orders.distinct("order_id", {"order_id": {"$type": "string"}, "is_deleted": {"$ne": True}})
        )
        kpi_comparison = []
        for metric, expected_value in (
            ("total_sales", expected["total_sales"]),
            ("distinct_orders", expected["distinct_orders"]),
            ("units_sold", expected["units_sold"]),
        ):
            actual_value = actual_orders if metric == "distinct_orders" else float(aggregate_values.get(metric, 0.0))
            tolerance = 0.01 if metric != "distinct_orders" else 0.0
            difference = float(expected_value) - float(actual_value)
            kpi_comparison.append(
                {
                    "metric_name": metric,
                    "python_value": expected_value,
                    "mongodb_value": actual_value,
                    "difference": difference,
                    "tolerance": tolerance,
                    "status": "PASS" if abs(difference) <= tolerance else "FAIL",
                }
            )

        monthly_python = _python_metrics(
            expected_fact, expected_products
        )["monthly_sales"] if not expected_fact.empty else {}
        monthly_mongodb = list(
            orders.aggregate(
                [
                    {
                        "$set": {
                            "_normalized_order_date": {
                                "$convert": {
                                    "input": "$order_date",
                                    "to": "date",
                                    "onError": None,
                                    "onNull": None,
                                }
                            }
                        }
                    },
                    {"$match": {"_normalized_order_date": {"$ne": None}}},
                    {
                        "$group": {
                            "_id": {
                                "$dateToString": {
                                    "format": "%Y-%m",
                                    "date": "$_normalized_order_date",
                                }
                            },
                            "total_sales": {"$sum": "$net_sales"},
                        }
                    },
                ]
            )
        )
        monthly_mongodb_values = {row["_id"]: float(row["total_sales"]) for row in monthly_mongodb}
        for month in sorted(set(monthly_python) | set(monthly_mongodb_values)):
            python_value = float(monthly_python.get(month, 0.0))
            mongo_value = monthly_mongodb_values.get(month, 0.0)
            difference = python_value - mongo_value
            kpi_comparison.append(
                {
                    "metric_name": f"monthly_sales:{month}",
                    "python_value": python_value,
                    "mongodb_value": mongo_value,
                    "difference": difference,
                    "tolerance": 0.01,
                    "status": "PASS" if abs(difference) <= 0.01 else "FAIL",
                }
            )

        passed = all(
            result["document_count_match"]
            and not result["missing_indexes"]
            and all(field["valid"] for field in result["required_fields"].values())
            for result in collection_results.values()
        ) and all(row["status"] == "PASS" for row in kpi_comparison)
        return {
            "status": "PASS" if passed else "FAIL",
            "collections": collection_results,
            "kpi_comparison": kpi_comparison,
        }
    finally:
        if own_client:
            mongo_client.close()


def main() -> int:
    result = validate_mongodb()
    print(result)
    if result["status"] == "SKIPPED":
        return 2
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
