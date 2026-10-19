from pymongo.errors import ServerSelectionTimeoutError

from src.mongo_validation import _field_type_query, validate_mongodb


def test_mongodb_live_validation_skips_unreachable_database_without_credentials():
    class UnavailableClient:
        class Admin:
            def command(self, name):
                assert name == "ping"
                raise ServerSelectionTimeoutError("private connection detail")

        admin = Admin()

    result = validate_mongodb(client=UnavailableClient(), tables={})

    assert result["status"] == "SKIPPED"
    assert "could not be reached" in result["reason"]
    assert "private" not in result["reason"]


def test_required_mongodb_type_query_accepts_any_declared_bson_type():
    query = _field_type_query("quantity", ("int", "long"))

    assert query == {
        "$nor": [
            {"quantity": {"$type": "int"}},
            {"quantity": {"$type": "long"}},
        ]
    }
