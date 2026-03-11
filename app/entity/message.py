"""
消息实体 - 纯POJO
"""
from app.dao.mapper import BaseEntity


class MessageRole:
    """消息角色常量"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


class Message(BaseEntity):
    """消息实体类，对应数据库messages表"""
    
    _table_name = 'dodo_messages'
    _primary_key = 'id'
    
    def __init__(self, id=None, conversation_id=None, role=None, content=None, created_at=None, **kwargs):
        self.id = id
        self.conversation_id = conversation_id
        self.role = role
        self.content = content
        self.created_at = created_at
        for key, value in kwargs.items():
            setattr(self, key, value)