"""
用户实体 - 纯POJO
"""
from app.dao.mapper import BaseEntity


class User(BaseEntity):
    """用户实体类，对应数据库users表"""
    
    _table_name = 'dodo_users'
    _primary_key = 'id'
    
    def __init__(self, id=None, email=None, phone=None, created_at=None, **kwargs):
        self.id = id
        self.email = email
        self.phone = phone
        self.created_at = created_at
        # 过滤掉name字段（name是动态计算属性，不应该被赋值）
        for key, value in kwargs.items():
            if key != 'name':  # 跳过name字段
                setattr(self, key, value)
    
    @property
    def name(self):
        """从邮箱中提取用户名"""
        return self.email.split('@')[0] if self.email else "用户"
    
    def to_dict(self):
        """将对象转换为字典"""
        data = super().to_dict()
        data['name'] = self.name
        return data