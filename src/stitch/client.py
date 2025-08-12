import requests

from abc import ABC, abstractmethod
from typing import Any


TYPE_MAPPING = {
    int: "integer",
    float: "number",
    str: "string",
    bool: "boolean",
    list: "array",
    dict: "object",
    Any: "any",
}


class SchemaFetcher(ABC):
    @abstractmethod
    def fetch(self, base_url: str) -> dict:
        pass


class HTTPSchemaFetcher(SchemaFetcher):
    def fetch(self, base_url: str) -> dict:
        response = requests.get(f"{base_url}/schema")
        response.raise_for_status()
        return response.json()


class Client:
    def __init__(self, base_url: str, fetcher: SchemaFetcher | None = None):
        self.base_url = base_url.rstrip("/")
        self.fetcher = fetcher or HTTPSchemaFetcher()
        self.schema = self.fetch_schema()

    def get(self, endpoint: str, **kwargs):
        schema = self.schema[endpoint]["schema"]
        __input = schema["input"]

        # Check required fields
        for required_field in __input["required"]:
            if required_field not in kwargs:
                msg: str = f"""
                message   : Missing required field:\n
                missing   : {required_field}\n
                expected  : {", ".join(__input["required"])}
                """
                raise ValueError(msg)

        # Check required field types
        to_validate = {
            param: value for param, value in kwargs.items() 
            if param in __input["required"]
        }
        for param, value in to_validate.items():
            if TYPE_MAPPING[type(value)] != __input["properties"][param]["type"]:
                msg: str = f"""
                message   : Invalid type for field:\n
                field     : {param}\n
                expected  : {__input["properties"][param]["type"]}\n
                received  : {TYPE_MAPPING[type(value)]}
                """
                raise ValueError(msg)

        # Make the requests
        response = requests.get(f"{self.base_url}/{endpoint}", params=kwargs)
        data = response.json()

        return data

    def fetch_schema(self) -> dict:
        return self.fetcher.fetch(self.base_url)


