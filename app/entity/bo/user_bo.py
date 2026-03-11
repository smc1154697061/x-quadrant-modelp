"""
用户业务对象 - Service层使用的业务逻辑对象
"""
from typing import Optional
from datetime import datetime


class UserBO:
    """用户业务对象 - 包含业务逻辑处理"""
    
    def __init__(self, id: Optional[int] = None, email: str = None, 
                 phone: Optional[str] = None, created_at: datetime = None):
        self.id = id
        self.email = email
        self.phone = phone
        self.created_at = created_at
    
    @property
    def name(self):
        """从邮箱中提取用户名"""
        return self.email.split('@')[0] if self.email else "用户"
    
    def is_valid_email(self) -> bool:
        """校验邮箱格式"""
        return '@' in self.email if self.email else False
    
    def is_valid_phone(self) -> bool:
        """校验手机号格式"""
        if not self.phone:
            return True  # 手机号可选
        return len(self.phone) == 11 and self.phone.isdigit()
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'email': self.email,
            'phone': self.phone,
            'name': self.name,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_po(cls, user_po):
        """从PO对象转换"""
        if not user_po:
            return None
        return cls(
            id=user_po.id,
            email=user_po.email,
            phone=user_po.phone,
            created_at=user_po.created_at
        )
    
    @classmethod
    def from_dict(cls, user_dict):
        """从字典转换"""
        if not user_dict:
            return None
        return cls(
            id=user_dict.get('id'),
            email=user_dict.get('email'),
            phone=user_dict.get('phone'),
            created_at=user_dict.get('created_at')
        )
