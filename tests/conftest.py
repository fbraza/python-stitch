import pytest
from fastapi import FastAPI
from pydantic import BaseModel

from stitch.router import Router


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
                    "required": ["user_id"],
                },
                "output": {"$ref": "#/defs/User"},
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


@pytest.fixture
def server():
    from fastapi.testclient import TestClient

    router = Router()
    app = FastAPI()

    @app.get("/get_user")
    @router.query(name="get_user")
    def get_user(user_id: int) -> User:
        return User(id=user_id, name="John", age=30)

    @app.get("/schema")
    def schema() -> dict:
        return router.get_schema()

    client = TestClient(app)
    yield client


@pytest.fixture(scope="function")
def live_server():
    import threading
    import time

    router = Router()
    app = FastAPI()

    @app.get("/get_user")
    @router.query(name="get_user")
    def get_user(user_id: int) -> User:
        return User(id=user_id, name="John Doe", age=30)

    @app.get("/schema")
    def schema() -> dict:
        return router.get_schema()

    import uvicorn

    config = uvicorn.Config(app, host="127.0.0.1", port=8001, log_level="error")
    server = uvicorn.Server(config)

    def run_server():
        server.run()

    thread = threading.Thread(target=run_server)
    thread.daemon = True
    thread.start()
    time.sleep(0.1)  # Give server time to start

    yield "http://localhost:8001"

    # Teardown
    server.should_exit = True
    thread.join(timeout=2)
