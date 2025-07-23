""""
------------------------------------------------------------
 Author : Rayyan Mirza
 Base class for all data models with common functionality
------------------------------------------------------------
"""

from dataclasses import dataclass, field, fields
from typing import Any, Dict, List, Optional
from datetime import datetime
import json

@dataclass
class BaseModel:
    """Base class for all data models with common functionality"""
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        result = {}
        for field_obj in fields(self):
            value = getattr(self, field_obj.name)
            if isinstance(value, datetime):
                result[field_obj.name] = value.isoformat()
            elif isinstance(value, BaseModel):
                result[field_obj.name] = value.to_dict()
            elif isinstance(value, list):
                result[field_obj.name] = [
                    item.to_dict() if isinstance(item, BaseModel) else item
                    for item in value
                ]
            else:
                result[field_obj.name] = value
        return result
    
    def to_json(self) -> str:
        """Serialize to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create instance from dictionary"""
        # This is a basic implementation - you may need to customize per model
        return cls(**data)
    
    def validate(self) -> bool:
        """Override in subclasses for custom validation"""
        return True
