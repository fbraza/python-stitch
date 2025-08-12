from typing import Any

import requests

from stitch.constants import TYPE_MAPPING
from stitch.fetchers import HTTPSchemaFetcher, SchemaFetcher


class Client:
    def __init__(self, base_url: str, fetcher: SchemaFetcher | None = None):
        self.base_url = base_url.rstrip("/")
        self.fetcher = fetcher or HTTPSchemaFetcher()
        self.schema = self.fetch_schema()

    def get(self, endpoint: str, timeout: int = 30, **kwargs: Any):
        schema = self.schema[endpoint]["schema"]
        __input = schema["input"]
        self.__validate_input(__input, params=kwargs)

        # Make the requests
        response = requests.get(
            f"{self.base_url}/{endpoint}", timeout=timeout, params=kwargs
        )
        data = response.json()

        return data

    def fetch_schema(self) -> dict:
        return self.fetcher.fetch(self.base_url)

    def __validate_input(
        self, schema_for_input: dict[str, Any], params: dict[str, Any]
    ):
        """
        Check required fields and fields types against schema
        """
        # Check required fields
        for required_field in schema_for_input["required"]:
            if required_field not in params:
                missing_field_msg: str = f"""
                message   : Missing required field:\n
                missing   : {required_field}\n
                expected  : {", ".join(schema_for_input["required"])}
                """
                raise ValueError(missing_field_msg)

        # Check required field types
        to_validate = {
            param: value
            for param, value in params.items()
            if param in schema_for_input["required"]
        }
        for param, value in to_validate.items():
            if (
                TYPE_MAPPING[type(value)]
                != schema_for_input["properties"][param]["type"]
            ):
                invalid_type_msg: str = f"""
                message   : Invalid type for field:\n
                field     : {param}\n
                expected  : {schema_for_input["properties"][param]["type"]}\n
                received  : {TYPE_MAPPING[type(value)]}
                """
                raise ValueError(invalid_type_msg)
