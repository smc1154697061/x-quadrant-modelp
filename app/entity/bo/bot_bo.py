"""
机器人业务对象 - Service层使用的业务逻辑对象
"""
from typing import Optional, List
from datetime import datetime


class BotBO:
    """机器人业务对象 - 包含业务逻辑处理"""
    
    def __init__(self, id: Optional[int] = None, name: str = None,
                 description: Optional[str] = None, system_prompt: Optional[str] = None,
                 model_name: Optional[str] = None, created_by: Optional[int] = None,
                 is_public: bool = False, kb_ids: List[int] = None,
                 kb_names: List[str] = None, created_at: datetime = None):
        self.id = id
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.model_name = model_name
        self.created_by = created_by
        self.is_public = is_public
        self.kb_ids = kb_ids or []
        self.kb_names = kb_names or []
        self.created_at = created_at
    
    def can_access_by_user(self, user_id: int) -> bool:
        """判断用户是否有权访问此机器人"""
        return self.is_public or self.created_by == user_id
    
    def can_edit_by_user(self, user_id: int) -> bool:
        """判断用户是否有权编辑此机器人"""
        return self.created_by == user_id
    
    def has_knowledge_base(self) -> bool:
        """判断是否关联了知识库"""
        return len(self.kb_ids) > 0
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'system_prompt': self.system_prompt,
            'model_name': self.model_name,
            'created_by': self.created_by,
            'is_public': self.is_public,
            'kb_ids': self.kb_ids,
            'kb_names': self.kb_names,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_po(cls, bot_po):
        """从PO对象转换"""
        if not bot_po:
            return None
        return cls(
            id=bot_po.id,
            name=bot_po.name,
            description=bot_po.description,
            system_prompt=bot_po.system_prompt,
            model_name=bot_po.model_name,
            created_by=bot_po.created_by,
            is_public=bot_po.is_public,
            created_at=bot_po.created_at
        )
    
    @classmethod
    def from_dict(cls, bot_dict):
        """从字典转换（适配现有DAO返回的dict）"""
        if not bot_dict:
            return None
        return cls(
            id=bot_dict.get('id'),
            name=bot_dict.get('name'),
            description=bot_dict.get('description'),
            system_prompt=bot_dict.get('system_prompt'),
            model_name=bot_dict.get('model_name'),
            created_by=bot_dict.get('created_by'),
            is_public=bot_dict.get('is_public', False),
            kb_ids=bot_dict.get('kb_ids', []),
            kb_names=bot_dict.get('kb_names', []),
            created_at=bot_dict.get('created_at')
        )
