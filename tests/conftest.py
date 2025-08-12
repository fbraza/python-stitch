import pytest
from pydantic import BaseModel
from stitch.client import Client, SchemaFetcher


class User(BaseModel):
    id: int
    name: str
    age: int


@pytest.fixture
def sample_user():
    return User(id=1, name="John", age=30)


@pytest.fixture
def base_url():
    return "http://localhost:8000"


@pytest.fixture
def mock_schema():
    return {
        "get_user": {
            "type": "query",
            "schema": {
                "input": {
                    "properties": {"user_id": {"type": "integer"}},
                    "required": ["user_id"]
                },
                "output": {"$ref": "#/defs/User"},
                "$defs": {
                    "User": {
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"},
                            "age": {"type": "integer"}
                        },
                        "required": ["id", "name", "age"]
                    }
                }
            }
        }
    }
