from typing import Any

import requests

from stitch.constants import TYPE_MAPPING
from stitch.fetchers import HTTPSchemaFetcher, SchemaFetcher


class Client:
    def __init__(self, base_url: str, fetcher: SchemaFetcher | None = None):
        self.base_url = base_url.rstrip("/")
        self.fetcher = fetcher or HTTPSchemaFetcher()
        self.schema = self.fetch_schema()

    def call(self, procedure: str, timeout: int = 30, **kwargs: Any):
        schema: dict[str, Any] = self.schema[procedure]["schema"]
        self.__validate_input(schema["input"], params=kwargs)

        response: requests.Response | None = None
        type: str = self.schema[procedure]["type"]

        if type == "query":
            response = requests.get(
                f"{self.base_url}/{procedure}", timeout=timeout, params=kwargs
            )

        if type == "mutation":
            response = requests.post(
                f"{self.base_url}/{procedure}", timeout=timeout, json=kwargs
            )

        if response is None:
            raise ValueError("Invalid procedure type")

        return response.json()

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
