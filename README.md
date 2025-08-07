# Stitch

A zero-boilerplate, end-to-end type-safe RPC framework for Python microservices.

Stitch lets you define your service procedures with Python type hints—whether you use `dataclasses`, `attrs`, `msgspec.Struct`, or `pydantic.BaseModel`—and automatically generates a fully-typed client on import. No extra schema files. No manual codegen. IDE autocomplete and static type checks just work, as if you were calling a local function.

## Features

- **Zero-config introspection**  
  Expose a `/~stitch` endpoint that publishes your service’s full API shape in JSON Schema.
- **Multi-model support**  
  First-class adapters for `dataclasses`, `attrs`, `msgspec`, and `pydantic`.
- **Automatic stub generation**  
  Builds PEP 561 stubs on the fly; IDEs (PyCharm, VS Code) and type checkers (Mypy, Pyright) understand your RPC calls.
- **Pluggable transports**  
  HTTP/1.1 JSON by default; extendable to WebSockets, HTTP/2, or Unix sockets.
- **Runtime validation**  
  Uses the fastest available codec for each model type, with optional zero-validation mode for hot paths.
- **OpenAPI & GraphQL integration**  
  Generate the same typed client from any OpenAPI 3 or GraphQL schema.

## Quickstart

### Server (FastAPI example)
```python
from fastapi import FastAPI
from dataclasses import dataclass
from stitch import procedure, mount

app = FastAPI()
rpc = mount(app)  # Adds /rpc/* and /~stitch

@dataclass
class Query:
    id: int

@dataclass
class User:
    id: int
    name: str

@procedure()
def get_user(q: Query) -> User:
    return User(id=q.id, name="Alice")

### Client

```python
from stitch import Client

# Connect and auto-generate stubs
client = await Client.connect("http://localhost:8000")

# IDE knows exact signature and return type
user = await client.get_user(id=42)
print(user.name)
```
