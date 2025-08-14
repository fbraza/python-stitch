import inspect
from collections.abc import Callable
from functools import wraps
from typing import Any, get_type_hints

from pydantic import create_model

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
                "handler": func,
                "signature": sig,
                "type_hints": type_hints,
                "schema": extractor.schemas(sig=sig, hints=type_hints),
            }

            @wraps(func)
            def wrapper(*args, **kwargs):
                result = func(*args, **kwargs)

                if self.proc[proc_name]["output"]["type"] == "pydantic":
                    for model in self.proc[proc_name]["output"]["$defs"]:
                        if sorted(result.keys()) != sorted(
                            self.proc[proc_name]["output"]["$defs"][model].keys()
                        ):
                            raise ValueError

                        create_model(model, **result)

                return result

            return func

        return __decorator
