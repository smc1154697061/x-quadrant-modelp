from datetime import datetime
from typing import Dict, Any


class BaseEntity:
    _table_name = None
    _primary_key = 'id'
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        result = {}
        for key, value in self.__dict__.items():
            if key.startswith('_'):
                continue
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        if data is None:
            return None
        return cls(**data)
    
    @classmethod
    def from_dict_list(cls, data_list):
        if not data_list:
            return []
        return [cls.from_dict(data) for data in data_list]
    
    def __repr__(self):
        attrs = ', '.join(f'{k}={v!r}' for k, v in self.__dict__.items() if not k.startswith('_'))
        return f'{self.__class__.__name__}({attrs})'
