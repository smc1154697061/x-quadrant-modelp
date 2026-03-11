"""
用户Mapper - MyBatis Plus风格
"""
from typing import Optional
from app.dao.mapper import BaseMapper, select_one
from app.entity.user import User


class UserDAO(BaseMapper):
    """用户Mapper，继承BaseMapper获得通用CRUD"""
    
    entity_class = User
    table_name = 'dodo_users'
    primary_key = 'id'
    
    @select_one("SELECT * FROM dodo_users WHERE email = %s", User)
    def find_by_email(self, email: str) -> Optional[User]:
        """通过邮箱查找用户"""
        pass
    
    @select_one("SELECT * FROM dodo_users WHERE phone = %s", User)
    def find_by_phone(self, phone: str) -> Optional[User]:
        """通过手机号查找用户"""
        pass
    
    def find_by_id(self, user_id):
        """通过ID查找用户，返回字典"""
        user = self.select_by_id(user_id)
        return user.to_dict() if user else None
    
    def create(self, user: User):
        """创建新用户（面向对象风格）
        
        参数:
            user: User实体对象
        
        返回:
            创建后的User字典（包含id）
        """
        user_id = self.insert(user)
        user.id = user_id
        return user.to_dict()
    
    def update(self, user: User):
        """更新用户信息（面向对象风格）
        
        参数:
            user: User实体对象（必须包含id）
        
        返回:
            是否更新成功
        """
        if not user.id:
            raise ValueError("User实体必须包含id字段")
        
        update_data = user.to_dict()
        update_data.pop('id', None)  # 移除主键
        update_data.pop('created_at', None)  # 移除创建时间
        update_data.pop('name', None)  # 移除name（动态计算字段，不需要更新）
        
        # 只保留非None的字段（避免把未传入的字段更新为NULL）
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        if not update_data:
            return True  # 没有需要更新的字段
        
        return super().update(update_data, {'id': user.id}) > 0
    
    def delete(self, user_id):
        """删除用户"""
        return self.delete_by_id(user_id) > 0
    
    def find_all(self, limit=100, offset=0):
        """获取所有用户（分页），返回字典列表"""
        users = self.select_all(order_by='id DESC', limit=limit, offset=offset)
        return [user.to_dict() for user in users]
    
    def count(self):
        """获取用户总数"""
        return super().count()