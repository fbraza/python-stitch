import pytest
from pydantic import BaseModel

from stitch.router import DuplicateProcedureError, Router


class User(BaseModel):
    name: str
    age: int


def test_router_query():
    router = Router()

    @router.query()
    def get_user(user_id: int) -> User: ...  # type: ignore

    assert router.proc["get_user"]["handler"] == get_user
    assert router.proc["get_user"]["type"] == "query"
    assert router.proc["get_user"]["schema"] == {
        "input": {
            "properties": {"user_id": {"type": "integer"}},
            "required": ["user_id"],
        },
        "output": {"$ref": "#/defs/User", "type": "pydantic"},
        "$defs": {
            "User": {
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"},
                },
                "required": ["name", "age"],
            }
        },
    }


def test_raise_for_duplciated_procs():
    router = Router()

    @router.query("get_user")
    def get_user(user_id: int) -> User: ...  # type: ignore

    with pytest.raises(DuplicateProcedureError, match="Duplicate procedure name"):

        @router.query("get_user")
        def collect_user(user_id: int) -> User: ...  # type: ignore


def test_empty_router():
    router = Router()

    assert router.get_schema() == {}
