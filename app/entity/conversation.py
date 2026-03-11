"""
会话实体 - 纯POJO
"""
from app.dao.mapper import BaseEntity


class Conversation(BaseEntity):
    """会话实体类，对应数据库conversations表"""
    
    _table_name = 'dodo_conversations'
    _primary_key = 'id'
    
    def __init__(self, id=None, user_id=None, bot_id=None, created_at=None, **kwargs):
        self.id = id
        self.user_id = user_id
        self.bot_id = bot_id
        self.created_at = created_at
        for key, value in kwargs.items():
            setattr(self, key, value)