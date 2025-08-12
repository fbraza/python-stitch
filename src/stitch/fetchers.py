from abc import ABC, abstractmethod

import requests


class SchemaFetcher(ABC):
    @abstractmethod
    def fetch(self, base_url: str) -> dict:
        pass


class HTTPSchemaFetcher(SchemaFetcher):
    def fetch(self, base_url: str) -> dict:
        response = requests.get(f"{base_url}/schema", timeout=30)
        response.raise_for_status()
        return response.json()
