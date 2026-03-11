"""
消息业务对象 - Service层使用的业务逻辑对象
"""
from typing import Optional
from datetime import datetime


class MessageBO:
    """消息业务对象"""
    
    def __init__(self, id: Optional[int] = None, conversation_id: int = None,
                 role: str = None, content: str = None, created_at: datetime = None):
        self.id = id
        self.conversation_id = conversation_id
        self.role = role
        self.content = content
        self.created_at = created_at
    
    def is_user_message(self) -> bool:
        """判断是否为用户消息"""
        return self.role == 'user'
    
    def is_assistant_message(self) -> bool:
        """判断是否为助手消息"""
        return self.role == 'assistant'
    
    def get_preview(self, max_length: int = 50) -> str:
        """获取消息预览（截断）"""
        if not self.content:
            return ""
        if len(self.content) <= max_length:
            return self.content
        return self.content[:max_length] + "..."
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'role': self.role,
            'content': self.content,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """从字典转换"""
        if not data:
            return None
        return cls(
            id=data.get('id'),
            conversation_id=data.get('conversation_id'),
            role=data.get('role'),
            content=data.get('content'),
            created_at=data.get('created_at')
        )
