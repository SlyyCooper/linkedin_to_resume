from typing import Any, Optional, List, Dict, Union
from dataclasses import dataclass

class ZodType:
    def __init__(self, type_name: str):
        self.type_name = type_name

class z:
    @staticmethod
    def string():
        return ZodType("string")
    
    @staticmethod
    def array(item_type):
        return ZodType(f"array<{item_type.type_name}>")
    
    @staticmethod
    def object(schema: Dict):
        return ZodType("object")
    
    @staticmethod
    def optional(field_type):
        return ZodType(f"optional<{field_type.type_name}>")

def zodResponseFormat(schema, name: str):
    return {"type": "json_object", "schema": schema} 