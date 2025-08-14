import inspect
from collections.abc import Callable
from functools import wraps
from typing import Any, get_type_hints

from fastapi import FastAPI, Request
from pydantic import ValidationError
from starlette.responses import JSONResponse

from stitch import extractor


class BaseRouterError(Exception):
    """Base error class for Router errors"""


class DuplicateProcedureError(BaseRouterError):
    def __init__(self, proc: dict[str, Any], proc_name: str, type: str):
        msg: str = f"""
        message : Duplicate procedure name\n
        procedure: '{proc_name}' already exists\n
        type: procedure of type '{type}'\n
        expected: not in '{proc.keys()}'
        """
        super(BaseRouterError, self).__init__(msg)


class Router:
    def __init__(self):
        self.proc: dict[str, Any] = {}

    def get_schema(self) -> dict[str, Any]:
        if self.proc:
            return {
                name: {"type": proc["type"], "schema": proc["schema"]}
                for name, proc in self.proc.items()
            }

        return self.proc

    def mount(self, app: FastAPI, prefix: str = "") -> None:
        """
        Auto-mount all registered procedures as FastAPI endpoints.

        Args:
            app: FastAPI application instance
            prefix: URL prefix for all endpoints (default: "")
        """
        for proc_name, proc_data in self.proc.items():
            endpoint_path = f"{prefix}/{proc_name}".replace("//", "/")

            if proc_data["type"] == "query":
                # Create GET endpoint
                self._create_query_endpoint(app, endpoint_path, proc_data)
            elif proc_data["type"] == "mutation":
                # Create POST endpoint
                self._create_mutation_endpoint(app, endpoint_path, proc_data)

    def _create_query_endpoint(
        self, app: FastAPI, path: str, proc_data: dict[str, Any]
    ) -> None:
        """Create a GET endpoint for a query procedure."""
        handler = proc_data["handler"]
        signature = proc_data["signature"]

        async def endpoint_wrapper(request: Request):
            # Extract query parameters
            params = dict(request.query_params)

            # Convert parameters to correct types based on signature
            converted_params = self._convert_params(params, signature)

            # Call the handler
            return handler(**converted_params)

        app.get(path)(endpoint_wrapper)

    def _create_mutation_endpoint(
        self, app: FastAPI, path: str, proc_data: dict[str, Any]
    ) -> None:
        """Create a POST endpoint for a mutation procedure."""
        handler = proc_data["handler"]
        signature = proc_data["signature"]

        async def endpoint_wrapper(request: Request):
            # Extract JSON body
            body = await request.json()

            # Convert parameters to correct types based on signature
            converted_params = self._convert_params(body, signature)

            # Call the handler
            return handler(**converted_params)

        app.post(path)(endpoint_wrapper)

    def _convert_params(
        self, params: dict[str, Any], signature: inspect.Signature
    ) -> dict[str, Any]:
        """Convert string parameters to the correct types based on function signature."""
        converted: dict[str, Any] = {}

        for param_name, param in signature.parameters.items():
            if param_name in params:
                value = params[param_name]

                # Get the parameter type annotation
                param_type = param.annotation

                # Convert based on type
                if param_type is int:
                    converted[param_name] = int(value)
                elif param_type is float:
                    converted[param_name] = float(value)
                elif param_type is bool:
                    converted[param_name] = str(value).lower() in (
                        "true",
                        "1",
                        "yes",
                        "on",
                    )
                elif param_type is str:
                    converted[param_name] = str(value)
                else:
                    # For complex types, keep as-is
                    converted[param_name] = value
            elif param.default is not inspect.Parameter.empty:
                # Use default value if parameter not provided
                converted[param_name] = param.default

        return converted

    def query(self, name: str | None = None) -> Callable[[Callable], Callable]:
        """
        Decorator that registers a function as a query handler.
        """
        return self.__make_decorator(type="query", name=name)

    def mutation(self, name: str | None = None) -> Callable[[Callable], Callable]:
        """
        Decorator that registers a function as a mutation handler.
        """
        return self.__make_decorator(type="mutation", name=name)

    def __make_decorator(
        self, type: str, name: str | None = None
    ) -> Callable[[Callable], Callable]:
        """
        Minimal query decorator that:
        1. Registers the function
        2. Extracts type information
        3. Stores schema for client consumption
        """

        def __decorator(func: Callable) -> Callable:
            proc_name = name or func.__name__
            if proc_name in self.proc.keys():
                raise DuplicateProcedureError(
                    proc=self.proc, proc_name=proc_name, type=type
                )

            # Extract type information
            type_hints = get_type_hints(func)
            sig = inspect.signature(func)
            self.proc[proc_name] = {
                "type": type,
                "signature": sig,
                "type_hints": type_hints,
                "schema": extractor.schemas(sig=sig, hints=type_hints),
            }

            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    result = func(*args, **kwargs)
                    if self.proc[proc_name]["schema"]["output"]["type"] == "pydantic":
                        for model in self.proc[proc_name]["schema"]["$defs"]:
                            expected = sorted(
                                self.proc[proc_name]["schema"]["$defs"][model][
                                    "properties"
                                ].keys()
                            )
                            current = sorted(result.model_dump().keys())
                            if expected != current:
                                return JSONResponse(
                                    status_code=422,
                                    content={
                                        "message": "Schema of your pydantic object is incorrect",
                                        # "expected_fields": expected,
                                        # "actual_fields": current
                                    },
                                )
                    return result
                except ValidationError as err:
                    return JSONResponse(
                        status_code=422,
                        content={
                            "message": "Pydantic validation error",
                            "errors": str(err),
                        },
                    )

            self.proc[proc_name]["handler"] = wrapper
            return wrapper

        return __decorator
