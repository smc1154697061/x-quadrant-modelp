"""
机器人实体 - 纯POJO
"""
from app.dao.mapper import BaseEntity


class Bot(BaseEntity):
    """机器人实体类，对应数据库bots表"""
    
    _table_name = 'dodo_bots'
    _primary_key = 'id'
    
    def __init__(self, id=None, name=None, description=None, system_prompt=None,
                 model_name=None, created_by=None, is_public=None, created_at=None, **kwargs):
        self.id = id
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.model_name = model_name
        self.created_by = created_by
        self.is_public = is_public
        self.created_at = created_at
        for key, value in kwargs.items():
            setattr(self, key, value)