"""
对话业务对象 - Service层使用的业务逻辑对象
"""
from typing import Optional
from datetime import datetime


class ConversationBO:
    """对话业务对象"""
    
    def __init__(self, id: Optional[int] = None, user_id: int = None,
                 bot_id: int = None, created_at: datetime = None):
        self.id = id
        self.user_id = user_id
        self.bot_id = bot_id
        self.created_at = created_at
    
    def belongs_to_user(self, user_id: int) -> bool:
        """判断对话是否属于指定用户"""
        return self.user_id == user_id
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'bot_id': self.bot_id,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """从字典转换"""
        if not data:
            return None
        return cls(
            id=data.get('id'),
            user_id=data.get('user_id'),
            bot_id=data.get('bot_id'),
            created_at=data.get('created_at')
        )
