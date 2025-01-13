from typing import Dict, Any, TypeVar, Type, Optional
from datetime import datetime
import json
from ..models.base import BaseDbModel

T = TypeVar('T', bound=BaseDbModel)

def row_to_model(row: Optional[Dict[str, Any]], model_class: Type[T]) -> Optional[T]:
    """Convert database row to model instance"""
    if not row:
        return None
    
    # Convert datetime objects to isoformat strings
    processed_row = {}
    for key, value in row.items():
        if isinstance(value, datetime):
            processed_row[key] = value.isoformat()
        elif isinstance(value, (dict, list)):
            processed_row[key] = json.dumps(value)
        else:
            processed_row[key] = value
            
    return model_class(**processed_row)

def model_to_row(model: BaseDbModel) -> Dict[str, Any]:
    """Convert model instance to database row"""
    row = {}
    model_dict = model.__dict__  # or use dict(model) if __dict__ is not available
    for key, value in model_dict.items():
        if value is None:
            continue
        if isinstance(value, (dict, list)):
            row[key] = json.dumps(value)
        else:
            row[key] = value
    return row
