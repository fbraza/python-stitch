# stitch Specification Document

## Project: stitch - Type-Safe RPC for Python Services

### Executive Summary

stitch is a Python library that enables type-safe RPC between Python services, inspired by TypeScript's tRPC. It automatically extracts type information from Python functions and propagates it to clients, providing runtime validation without manual schema definitions.

### Core Design Principles

1. **Zero Code Generation**: Types flow from server to client without build steps
2. **Runtime Type Safety**: Leverage Python's type hints for validation
3. **Model Library Agnostic**: Support Pydantic, msgspec, dataclasses, and attrs
4. **Simple and Pragmatic**: Focus on practical implementation over complex abstractions

## Current Implementation Status

### ✅ Implemented Components

1. **Router System** (`router.py`)
   - Basic router with `query` decorator
   - Stores procedures with type information
   - Extracts schemas using the extractor module

2. **Type Extractor** (`extractor.py`)
   - Extracts function signatures and type hints
   - Generates JSON Schema-like structure for inputs/outputs
   - Handles basic types (int, str, bool, list, dict)
   - Supports model types with $ref notation

3. **Model Detection** (`models.py`)
   - Detects Pydantic models (v1 and v2)
   - Detects msgspec structs
   - Detects dataclasses
   - Detects attrs classes

### ❌ Not Yet Implemented

1. **Client Implementation** - No client to consume the server
2. **Server Adapters** - No FastAPI/Flask integration
3. **Schema Endpoint** - No way to expose schemas to clients
4. **Mutations** - Only queries are supported
5. **Validation** - No runtime validation of inputs/outputs
6. **Complex Types** - No support for Union, Optional, generics

## Implementation Roadmap

## User Stories & Features

### Epic 1: Core Server Implementation
**As a developer, I want to create type-safe RPC endpoints so that my API is self-documenting and type-checked.**

#### Story 1.1: Complete Router Implementation
```python
# Current implementation (router.py)
router = Router()

@router.query()
def get_user(user_id: int) -> User:
    return User(...)

# Need to add:
@router.mutation()
def create_user(data: CreateUserInput) -> User:
    return User(...)
```

**Tasks:**
- [ ] Add `mutation` decorator to Router class
- [ ] Add `get_schema()` method to return all procedures as JSON
- [ ] Add error handling for duplicate procedure names

#### Story 1.2: Framework Integration with Decorator Stacking

```python
# Example usage - User has full control
from stitch import Router
from fastapi import FastAPI

app = FastAPI()
router = Router()

# User controls the path, middleware, and logic
@app.get("/api/users/{user_id}")
@router.query()                      # Just extracts types
async def get_user(user_id: int) -> User:
    return fetch_user(user_id)

@app.post("/api/users") 
@auth_required                       # User's middleware
@router.mutation()                   # Just extracts types
async def create_user(data: CreateUserInput) -> User:
    return save_user(data)

# User manually adds schema endpoint wherever they want
@app.get("/schema")
def get_schema():
    return router.get_schema()
```

**Tasks:**
- [ ] No adapter classes needed - router decorators stack with framework decorators
- [ ] User manually creates endpoints and adds schema endpoint
- [ ] Framework agnostic - works with FastAPI, Flask, Django, etc.

### Epic 2: Client Implementation
**As a developer, I want to consume stitch services with full type safety.**

#### Story 2.1: Basic Python Client with Runtime Validation
```python
# Client usage example
from stitch.client import Client

# Initialize client (fetches schema once)
client = Client("http://localhost:8000")

# Call procedures with runtime type validation
user = client.call("get_user", user_id=123)  # ✅ Valid
print(user["name"])  # Returns dict from JSON response

# Runtime validation examples:
user = client.call("get_user", user_id="abc")  # ❌ TypeError: user_id must be integer
user = client.call("get_user")  # ❌ TypeError: Missing required argument: user_id
```

**Implementation Approach:**
The client uses a simple `call()` method that:
1. Validates input parameters against the server's schema
2. Makes the appropriate HTTP request (GET for queries, POST for mutations)
3. Validates the response against the output schema
4. Returns the validated response data

**Tasks:**
- [ ] Create `client.py` module with `call()` method
- [ ] Fetch schema from server on initialization
- [ ] Implement input validation against schema
- [ ] Implement output validation against schema
- [ ] Add proper error messages for validation failures
- [ ] Support both query (GET) and mutation (POST) procedures

#### Story 2.2: Type Stub Generation
```python
# Generate .pyi files for IDE support
from stitch.client import Client
from stitch.stubs import generate_stubs

client = Client("http://localhost:8000")
generate_stubs(client, "./types/api.pyi")

# Now IDE has full type hints for all procedures
```

**Tasks:**
- [ ] Create stub generator module
- [ ] Parse schema to generate type hints
- [ ] Write .pyi files with proper imports
- [ ] Support for model type references

### Epic 3: Enhanced Type Support
**As a developer, I want to use complex Python types in my RPC procedures.**

#### Story 3.1: Optional and Union Types
```python
@router.query()
def search_users(
    name: Optional[str] = None,
    age: Optional[int] = None,
    status: Union[str, int] = "active"
) -> List[User]:
    return search_db(name, age, status)
```

**Tasks:**
- [ ] Update extractor to handle Optional types
- [ ] Support Union types in schema generation
- [ ] Add proper validation for union types

#### Story 3.2: Generic Types
```python
from typing import Generic, TypeVar

T = TypeVar('T')

class PagedResponse(Generic[T]):
    items: List[T]
    total: int
    page: int

@router.query()
def list_users(page: int = 1) -> PagedResponse[User]:
    return PagedResponse(items=[...], total=100, page=page)
```

**Tasks:**
- [ ] Handle TypeVar and Generic in extractor
- [ ] Generate proper schemas for generic types
- [ ] Support nested generics

## Technical Implementation Details

### Current Code Structure

```
src/stitch/
├── router.py      # Router with query decorator
├── extractor.py   # Type extraction and schema generation
└── models.py      # Model type detection
```

### Key Functions to Enhance

#### 1. Router.mutation() Implementation
```python
# In router.py, add:
def mutation(self, name: str | None = None):
    def decorator(func: Callable) -> Callable:
        proc_name = name or func.__name__

        type_hints = get_type_hints(func)
        sig = inspect.signature(func)

        self.proc[proc_name] = {
            "type": "mutation",
            "handler": func,
            "signature": sig,
            "type_hints": type_hints,
            "schema": extractor.schemas(sig=sig, hints=type_hints),
        }

        return func

    return decorator
```

#### 2. Router.get_schema() Implementation
```python
# In router.py, add:
def get_schema(self) -> dict:
    """Return all procedures as JSON-serializable schema."""
    schema = {
        "procedures": {},
        "models": {}
    }

    for name, proc in self.proc.items():
        schema["procedures"][name] = {
            "type": proc["type"],
            "schema": proc["schema"]
        }

    # TODO: Collect all referenced models
    return schema
```

#### 3. Framework Integration (No Adapter Needed)

The router works by stacking decorators - no complex adapter classes:

```python
# User has full control over their endpoints
from stitch import Router
from fastapi import FastAPI

app = FastAPI()
router = Router()

# Stack decorators - router just extracts types
@app.get("/api/users/{user_id}")
@router.query()
async def get_user(user_id: int) -> User:
    return fetch_user(user_id)

# Works with any middleware or decorators
@app.post("/api/users")
@auth_middleware
@validate_json
@router.mutation()
async def create_user(data: CreateUserInput) -> User:
    return save_user(data)

# User manually adds schema endpoint
@app.get("/schema")
def schema():
    return router.get_schema()
```

#### 4. Basic Client Implementation with Runtime Validation
```python
# New file: client.py
import requests
import jsonschema
from typing import Any, Dict

class Client:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.schema = self._fetch_schema()

    def _fetch_schema(self) -> dict:
        """Fetch schema from server."""
        response = requests.get(f"{self.base_url}/schema")
        return response.json()

    def call(self, method: str, **kwargs) -> dict:
        """Call a remote procedure with runtime type validation."""
        if method not in self.schema["procedures"]:
            raise ValueError(f"Unknown procedure: {method}")

        proc_info = self.schema["procedures"][method]
        proc_schema = proc_info["schema"]

        # 1. Validate input against schema
        self._validate_input(method, kwargs, proc_schema["input"])

        # 2. Make HTTP request based on procedure type
        if proc_info["type"] == "query":
            response = requests.get(
                f"{self.base_url}/{method}",
                params=kwargs
            )
        else:  # mutation
            response = requests.post(
                f"{self.base_url}/{method}",
                json=kwargs
            )

        data = response.json()

        # 3. Validate output against schema
        self._validate_output(method, data, proc_schema)

        return data["result"] if "result" in data else data

    def _validate_input(self, method: str, kwargs: dict, input_schema: dict):
        """Validate input parameters against schema."""
        # Check required fields
        for required_field in input_schema.get("required", []):
            if required_field not in kwargs:
                raise TypeError(f"{method}: Missing required argument: {required_field}")

        # Check types
        for field, value in kwargs.items():
            if field in input_schema["properties"]:
                expected_type = input_schema["properties"][field]["type"]
                if not self._check_type(value, expected_type):
                    raise TypeError(f"{method}: {field} must be {expected_type}")

    def _validate_output(self, method: str, data: dict, proc_schema: dict):
        """Validate response data against output schema."""
        output_schema = proc_schema.get("output", {})

        if "$ref" in output_schema:
            # Validate against model definition
            model_name = output_schema["$ref"].split("/")[-1]
            if "$defs" in proc_schema and model_name in proc_schema["$defs"]:
                model_schema = proc_schema["$defs"][model_name]
                try:
                    jsonschema.validate(data.get("result", data), {
                        "type": "object",
                        "properties": model_schema["properties"],
                        "required": model_schema.get("required", [])
                    })
                except jsonschema.ValidationError as e:
                    raise ValueError(f"{method}: Invalid response - {e.message}")

    def _check_type(self, value: Any, expected: str) -> bool:
        """Check if value matches expected type."""
        type_map = {
            "integer": int,
            "string": str,
            "boolean": bool,
            "number": (int, float),
            "array": list,
            "object": dict
        }
        expected_type = type_map.get(expected, object)
        return isinstance(value, expected_type)
```

## Example Usage - Complete Working Example

### Server Code

```python
# server.py
from stitch import Router
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

# Define models
class User(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool = True

class CreateUserInput(BaseModel):
    name: str
    email: str

# Create router and app
router = Router()
app = FastAPI()

# Define endpoints with decorator stacking
@app.get("/api/users/{user_id}")
@router.query()
async def get_user(user_id: int) -> User:
    # Fetch from database
    return User(
        id=user_id,
        name="John Doe",
        email="john@example.com"
    )

@app.get("/api/users")
@router.query()
async def list_users(limit: int = 10, offset: int = 0) -> List[User]:
    # Query database
    return [
        User(id=1, name="John", email="john@example.com"),
        User(id=2, name="Jane", email="jane@example.com")
    ]

@app.post("/api/users")
@router.mutation()
async def create_user(data: CreateUserInput) -> User:
    # Save to database
    return User(
        id=3,
        name=data.name,
        email=data.email
    )

# User manually adds schema endpoint wherever they want
@app.get("/schema")
def get_schema():
    return router.get_schema()

# Run with: uvicorn server:app
```

### Client Code
```python
# client.py
from stitch.client import Client

# Connect to server (fetches schema once)
client = Client("http://localhost:8000")

# Call procedures with runtime validation
try:
    # Valid calls - pass validation
    user = client.call("get_user", user_id=1)
    print(f"User: {user['name']} ({user['email']})")

    users = client.call("list_users", limit=5, offset=0)
    for u in users:
        print(f"- {u['name']}")

    new_user = client.call("create_user", data={
        "name": "Alice",
        "email": "alice@example.com"
    })
    print(f"Created user: {new_user['id']}")

    # Invalid calls - caught by runtime validation
    user = client.call("get_user", user_id="invalid")  # TypeError: user_id must be integer

except TypeError as e:
    print(f"Validation error: {e}")
except ValueError as e:
    print(f"Response validation error: {e}")
```

## Implementation Priority

### Phase 1: MVP (Week 1-2)
**Goal: Working end-to-end prototype**

1. **Complete Router** ✅ Partially done
   - [x] Query decorator
   - [ ] Mutation decorator
   - [ ] get_schema() method

2. **Framework Integration**
   - [ ] No adapter classes needed - decorators stack naturally
   - [ ] User creates their own endpoints and schema endpoint  
   - [ ] Test decorator stacking with FastAPI/Flask

3. **Basic Client**
   - [ ] Create client.py with `call()` method
   - [ ] Schema fetching on initialization
   - [ ] Input validation against schema
   - [ ] Output validation against schema
   - [ ] HTTP requests (GET for queries, POST for mutations)

4. **Testing**
   - [ ] Unit tests for extractor
   - [ ] Integration test with FastAPI
   - [ ] End-to-end test (server + client)

### Phase 2: Type Safety (Week 3-4)
**Goal: Enhanced type support and validation**

1. **Complex Types**
   - [ ] Optional/Union support
   - [ ] Generic types
   - [ ] Nested models
   - [ ] Lists with type parameters

2. **Validation**
   - [ ] Input validation against schema
   - [ ] Output validation
   - [ ] Better error messages

3. **Type Stubs**
   - [ ] Generate .pyi files
   - [ ] IDE integration

### Phase 3: Production Ready (Week 5-6)
**Goal: Production features**

1. **Framework Examples**
   - [ ] Flask decorator stacking example
   - [ ] Django decorator stacking example
   - [ ] Documentation for different frameworks

2. **Advanced Features**
   - [ ] Middleware support
   - [ ] Authentication helpers
   - [ ] Request context
   - [ ] Batch queries

3. **Performance**
   - [ ] Schema caching
   - [ ] Connection pooling
   - [ ] Async support

## Key Design Decisions

### 1. Schema Format
Use JSON Schema format for maximum compatibility:
```json
{
  "procedures": {
    "get_user": {
      "type": "query",
      "schema": {
        "input": {
          "properties": {
            "user_id": {"type": "integer"}
          },
          "required": ["user_id"]
        },
        "output": {
          "$ref": "#/defs/User"
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
}
```

### 2. Transport Protocol
- **Queries**: GET requests with query parameters
- **Mutations**: POST requests with JSON body
- **Schema**: GET /trpc/schema endpoint
- **Errors**: Standard HTTP status codes + JSON error details

### 3. Model Library Strategy
- Auto-detect which model library is being used
- Support mixing different libraries in one project
- Provide adapters for serialization/deserialization

## Next Steps

### Immediate Actions (Start Here!)

1. **Add mutation decorator to Router** (router.py)
   ```python
   def mutation(self, name: str | None = None):
       # Copy the query decorator logic but with type="mutation"
   ```

2. **Add get_schema method to Router** (router.py)
   ```python
   def get_schema(self) -> dict:
       return {"procedures": self.proc}
   ```

3. **Test framework integration**
   - Test decorator stacking with FastAPI
   - Test decorator stacking with Flask

4. **Create basic client** (new file: client.py)
   - Start with synchronous version using requests/httpx
   - Add async support later

5. **Write tests**
   - Test the complete flow: server → schema → client
### File Structure for New Implementation

```
src/
├── stitch/              
│   ├── __init__.py
│   ├── router.py        # ✅ Exists - needs mutation & get_schema
│   ├── extractor.py     # ✅ Exists - works well
│   ├── models.py        # ✅ Exists - works well
│   └── client.py        # ❌ TODO - Create this
└── tests/               # ❌ TODO - Add tests
    ├── test_router.py
    ├── test_extractor.py
    └── test_integration.py
```

## Summary

stitch is a pragmatic implementation of type-safe RPC for Python, focusing on:

1. **Simple, working code** over complex abstractions
2. **Incremental implementation** - start with MVP, add features as needed
3. **Real-world usage** - FastAPI first, other frameworks later
4. **Developer experience** - Type safety and IDE support

The current codebase has a solid foundation with the type extractor and model detection. The next steps are clear:
1. Complete the Router (add mutation and get_schema)
2. Create the FastAPI adapter
3. Build a basic client
4. Test the complete flow

This approach will deliver a working product quickly that can be enhanced iteratively based on real usage and feedback.
