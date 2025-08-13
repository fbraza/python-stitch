"""Shared constants for the stitch package.

This module contains constants that are used across multiple modules in the stitch package.
All constants follow the UPPER_CASE naming convention as per Python standards.
"""

from typing import Any

# Type mapping for JSON Schema generation
# Maps Python types to their corresponding JSON Schema type strings
TYPE_MAPPING = {
    int: "integer",
    float: "number",
    str: "string",
    bool: "boolean",
    list: "array",
    dict: "object",
    None.__class__: "null",
    Any: "any",
}
