# pyTRPC Specification Document

## Project: pyTRPC - Type-Safe RPC for Python Services

### Executive Summary

pyTRPC is a Python library that enables type-safe RPC between Python services, inspired by TypeScript's tRPC. It automatically extracts type information from Python functions and propagates it to clients, providing runtime validation without manual schema definitions.

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

#### Story 1.2: Server Adapter - FastAPI Integration
```python
# Example usage
from pytrpc import Router
from pytrpc.adapters import FastAPIAdapter
from fastapi import FastAPI

router = Router()

@router.query()
def get_user(user_id: int) -> User:
    return fetch_user(user_id)

app = FastAPI()
adapter = FastAPIAdapter(router)
adapter.attach(app, path="/trpc")

# This should create:
# GET /trpc/schema - Returns procedure schemas
# GET /trpc/get_user?user_id=123 - Query endpoint
```

**Tasks:**
- [ ] Create `adapters/fastapi.py` module
- [ ] Implement schema endpoint
- [ ] Map queries to GET endpoints
- [ ] Map mutations to POST endpoints
- [ ] Handle parameter extraction and validation

### Epic 2: Client Implementation
**As a developer, I want to consume pyTRPC services with full type safety and IDE support.**

#### Story 2.1: Basic Python Client
```python
# Client usage example
from pytrpc.client import Client

# Initialize client
client = Client("http://localhost:8000/trpc")

# Call procedures with type safety
user = client.get_user(user_id=123)  # Returns User object
print(user.name)  # IDE knows about User fields
```

**Tasks:**
- [ ] Create `client.py` module
- [ ] Fetch schema from server on initialization
- [ ] Create dynamic methods for each procedure
- [ ] Implement request/response handling
- [ ] Add error handling and retries

#### Story 2.2: Type Stub Generation
```python
# Generate .pyi files for IDE support
from pytrpc.client import Client
from pytrpc.stubs import generate_stubs

client = Client("http://localhost:8000/trpc")
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

#### 3. FastAPI Adapter Implementation
```python
# New file: adapters/fastapi.py
from fastapi import FastAPI, Query, Body
from typing import Any, Dict
import json

class FastAPIAdapter:
    def __init__(self, router):
        self.router = router
    
    def attach(self, app: FastAPI, path: str = "/trpc"):
        """Attach router to FastAPI app."""
        
        @app.get(f"{path}/schema")
        async def get_schema():
            return self.router.get_schema()
        
        # Register each procedure
        for name, proc in self.router.proc.items():
            if proc["type"] == "query":
                self._register_query(app, path, name, proc)
            elif proc["type"] == "mutation":
                self._register_mutation(app, path, name, proc)
    
    def _register_query(self, app, path, name, proc):
        handler = proc["handler"]
        
        @app.get(f"{path}/{name}")
        async def query_endpoint(**kwargs):
            # Call the original handler with query params
            result = handler(**kwargs)
            return {"result": result}
        
        return query_endpoint
```

#### 4. Basic Client Implementation
```python
# New file: client.py
import httpx
from typing import Any, Dict

class Client:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.schema = self._fetch_schema()
        self._build_methods()
    
    def _fetch_schema(self) -> dict:
        """Fetch schema from server."""
        response = httpx.get(f"{self.base_url}/schema")
        return response.json()
    
    def _build_methods(self):
        """Create methods for each procedure."""
        for name, proc in self.schema["procedures"].items():
            if proc["type"] == "query":
                setattr(self, name, self._create_query(name, proc))
            elif proc["type"] == "mutation":
                setattr(self, name, self._create_mutation(name, proc))
    
    def _create_query(self, name: str, proc: dict):
        def query(**kwargs):
            response = httpx.get(
                f"{self.base_url}/{name}",
                params=kwargs
            )
            return response.json()["result"]
        return query
    
    def _create_mutation(self, name: str, proc: dict):
        def mutation(**kwargs):
            response = httpx.post(
                f"{self.base_url}/{name}",
                json=kwargs
            )
            return response.json()["result"]
        return mutation
```

## Example Usage - Complete Working Example

### Server Code

```python
# server.py
from pytrpc import Router
from pytrpc.adapters import FastAPIAdapter
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

# Define models
class User(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool = True

class CreateUserInput(BaseModel):
    name: str
    email: str

# Create router
router = Router()

# Define procedures
@router.query()
def get_user(user_id: int) -> User:
    # Fetch from database
    return User(
        id=user_id,
        name="John Doe",
        email="john@example.com"
    )

@router.query()
def list_users(limit: int = 10, offset: int = 0) -> List[User]:
    # Query database
    return [
        User(id=1, name="John", email="john@example.com"),
        User(id=2, name="Jane", email="jane@example.com")
    ]

@router.mutation()
def create_user(data: CreateUserInput) -> User:
    # Save to database
    return User(
        id=3,
        name=data.name,
        email=data.email
    )

# Create FastAPI app
app = FastAPI()
adapter = FastAPIAdapter(router)
adapter.attach(app, path="/trpc")

# Run with: uvicorn server:app
```

### Client Code
```python
# client.py
from pytrpc.client import Client

# Connect to server
client = Client("http://localhost:8000/trpc")

# Call procedures with type safety
user = client.get_user(user_id=1)
print(f"User: {user['name']} ({user['email']})")

users = client.list_users(limit=5)
for u in users:
    print(f"- {u['name']}")

new_user = client.create_user(data={
    "name": "Alice",
    "email": "alice@example.com"
})
print(f"Created user: {new_user['id']}")
```

## Implementation Priority

### Phase 1: MVP (Week 1-2)
**Goal: Working end-to-end prototype**

1. **Complete Router** ✅ Partially done
   - [x] Query decorator
   - [ ] Mutation decorator
   - [ ] get_schema() method

2. **FastAPI Adapter**
   - [ ] Create adapters/fastapi.py
   - [ ] Schema endpoint
   - [ ] Query/Mutation endpoints
   - [ ] Parameter extraction

3. **Basic Client**
   - [ ] Create client.py
   - [ ] Schema fetching
   - [ ] Dynamic method creation
   - [ ] HTTP requests (GET/POST)

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

1. **Additional Adapters**
   - [ ] Flask adapter
   - [ ] Django adapter
   - [ ] Standalone ASGI/WSGI

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

3. **Create FastAPI adapter** (new file: adapters/fastapi.py)
   - Start with the basic implementation shown above
   - Test with a simple FastAPI app

4. **Create basic client** (new file: client.py)
   - Start with synchronous version using requests/httpx
   - Add async support later

5. **Write tests**
   - Test the complete flow: server → schema → client
### File Structure for New Implementation

```
src/
├── stitch/              # Rename to pytrpc later
│   ├── __init__.py
│   ├── router.py        # ✅ Exists - needs mutation & get_schema
│   ├── extractor.py     # ✅ Exists - works well
│   ├── models.py        # ✅ Exists - works well
│   ├── client.py        # ❌ TODO - Create this
│   └── adapters/        # ❌ TODO - Create this
│       ├── __init__.py
│       └── fastapi.py
└── tests/               # ❌ TODO - Add tests
    ├── test_router.py
    ├── test_extractor.py
    └── test_integration.py
```

## Summary

pyTRPC is a pragmatic implementation of type-safe RPC for Python, focusing on:

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
