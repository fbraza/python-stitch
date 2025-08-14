![Stitch](./assets/stitch-logo.png)

A type-safe RPC framework for Python that automatically generates JSON schemas from function signatures.

Stitch lets you define API procedures with Python type hints and automatically generates schemas for client validation and introspection. The client validates inputs against these schemas before making requests, providing type safety and clear error messages. Right now it is working as a MVP with only Pydantic models. (will add `dataclasses` and  `msgspec.Struct`)

## Features

- **Automatic schema generation**
- **Auto-mounting endpoints** - No manual FastAPI route wiring required
- **Pydantic model support**
- **Input validation**
- **Type-safe client**
- **Simple decorator-based API**

## Current State (MVP)

This is a working MVP that provides:
- Router with decorators for defining procedures
- **Auto-mounting of endpoints** - Zero FastAPI boilerplate
- Schema extraction from function signatures
- Type-safe HTTP client with validation
- Support for complex return types and nested pydantic models (list[Model] only)

## Usage

### Implement your server

```python
from pydantic import BaseModel
from fastapi import FastAPI
from stitch.router import Router

router = Router()
app = FastAPI()

class User(BaseModel):
    id: int
    name: str
    email: str

# Define procedures with router decorators only
@router.query()
def get_user(user_id: int) -> User:
    # Your implementation here
    return User(id=user_id, name="Alice", email="alice@example.com")

@router.mutation()
def create_user(name: str, email: str) -> User:
    # Your implementation here
    return User(id=123, name=name, email=email)

# Expose schema endpoint
@app.get("/schema")
def get_schema():
    return router.get_schema()

# 🚀 Auto-mount all procedures as endpoints!
router.mount(app)
# This automatically creates:
# GET /get_user?user_id=42
# POST /create_user (JSON body: {"name": "...", "email": "..."})
```

### 2. Use the type-safe client

```python
from stitch.client import Client

# Create client with base URL
client = Client("http://localhost:8000")

user_01 = client.call("get_user", user_id=42) # :white_check_mark: this works
user_02 = client.call("get_user", user_id=42, age=25) # :x: will raise an error
user_02 = client.call("get_user", user_id="42") # :x: will raise an error
```

## Schema Example

The router automatically generates JSON schemas like this:

```json
{
  "get_user": {
    "schema": {
      "input": {
        "properties": {
          "user_id": {"type": "integer"}
        },
        "required": ["user_id"]
      },
      "output": {
        "$ref": "#/defs/User",
        "type": "dataclass"
      },
      "$defs": {
        "User": {
          "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string"},
            "email": {"type": "string"}
          },
          "required": ["id", "name", "email"]
        }
      }
    }
  }
}
```

## Supported Model Types

Stitch automatically detects and works with:

- **Pydantic** - v1 and v2 models with `model_fields` or `__fields__`

## Installation

```bash
pip install -e .  # Development installation
```

## Roadmap

Future enhancements planned:
- FastAPI integration with automatic endpoint mounting
- Async client support
- WebSocket procedures
- Auto-generated typed stubs
- Advanced schema validation features
- Add support for `msgspec`, `dataclass`
