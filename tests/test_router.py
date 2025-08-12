from pydantic import BaseModel

from stitch.router import Router


class User(BaseModel):
    name: str
    age: int


def test_router_query():
    router = Router()

    @router.query()
    def get_user(user_id: int) -> User: ...  # type: ignore

    assert router.proc["get_user"]["type"] == "query"
    assert router.proc["get_user"]["handler"] == get_user
    assert router.proc["get_user"]["schema"] == {
        "input": {
            "properties": {"user_id": {"type": "integer"}},
            "required": ["user_id"],
        },
        "output": {"$ref": "#/defs/User"},
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
