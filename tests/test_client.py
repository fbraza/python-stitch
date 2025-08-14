from unittest.mock import patch

import pytest

from stitch.client import Client, FieldTypeError, RequiredFieldMissing
from stitch.fetchers import HTTPSchemaFetcher, SchemaFetcher


class MockSchemaFetcher(SchemaFetcher):
    def __init__(self, schema):
        self.schema = schema

    def fetch(self, base_url: str) -> dict:
        return self.schema


def test_client_initialization(mock_schema):
    client = Client("http://localhost:8000", MockSchemaFetcher(mock_schema))

    assert client.schema == mock_schema


def test_fetch_schema(mock_schema):
    client = Client("http://localhost:8000", MockSchemaFetcher(mock_schema))

    assert client.fetch_schema() == mock_schema


@patch("requests.get")
def test_valid_request(mock_get, mock_schema):
    client = Client("http://localhost:8000", MockSchemaFetcher(mock_schema))
    mock_get.return_value.json.return_value = {"id": 1, "name": "John", "age": 30}
    result = client.call("get_user", user_id=1)

    assert result.json()["name"] == "John"
    assert result.json()["age"] == 30
    assert result.json()["id"] == 1


@patch("requests.get")
def test_missing_required_field(mock_get, mock_schema):
    client = Client("http://localhost:8000", MockSchemaFetcher(mock_schema))
    mock_get.return_value.json.return_value = mock_schema

    with pytest.raises(RequiredFieldMissing, match="Missing required field"):
        client.call("get_user")  # Missing user_id


@patch("requests.get")
def test_wrong_type_field(mock_get, mock_schema):
    client = Client("http://localhost:8000", MockSchemaFetcher(mock_schema))
    mock_get.return_value.json.return_value = mock_schema

    with pytest.raises(FieldTypeError, match="Invalid type for field:"):
        client.call("get_user", user_id="1")  # Wrong user_id type


def test_http_schema_fetcher(live_server):
    client = Client(live_server, HTTPSchemaFetcher())
    schema = client.fetch_schema()

    assert "get_user" in schema
    assert schema == {
        "get_user": {
            "type": "query",
            "schema": {
                "input": {
                    "properties": {"user_id": {"type": "integer"}},
                    "required": ["user_id"],
                },
                "output": {"$ref": "#/defs/User", "type": "pydantic"},
                "$defs": {
                    "User": {
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"},
                            "age": {"type": "integer"},
                        },
                        "required": ["id", "name", "age"],
                    }
                },
            },
        }
    }


def test_working_http_query(live_server):
    client = Client(live_server, HTTPSchemaFetcher())
    response = client.call(procedure="get_user", user_id=1)

    assert response.json() == {"id": 1, "name": "John Doe", "age": 30}


def test_should_return_422_for_incorrect_pydantic_model(
    live_server_with_unsyced_return,
):
    client = Client(live_server_with_unsyced_return, HTTPSchemaFetcher())
    response = client.call(procedure="get_car", matriculation="0000")

    assert response.status_code == 422


def test_should_return_422_for_unsynced_model(live_server_with_unsyced_schema):
    client = Client(live_server_with_unsyced_schema, HTTPSchemaFetcher())
    response = client.call(procedure="get_car", matriculation="0000")

    assert response.status_code == 422
