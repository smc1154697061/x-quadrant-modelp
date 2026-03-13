"""
组织管理相关实体模型
"""
from datetime import datetime
from app.dao.mapper import BaseEntity


class Organization(BaseEntity):
    """组织实体类，对应数据库 dodo_organizations 表"""

    _table_name = 'dodo_organizations'
    _primary_key = 'id'

    def __init__(self, id=None, name=None, description=None, created_by=None,
                 created_at=None, updated_at=None, **kwargs):
        self.id = id
        self.name = name
        self.description = description
        self.created_by = created_by
        self.created_at = created_at
        self.updated_at = updated_at
        # 处理额外的字段
        for key, value in kwargs.items():
            setattr(self, key, value)


class OrganizationMember(BaseEntity):
    """组织成员实体类，对应数据库 dodo_organization_members 表"""

    _table_name = 'dodo_organization_members'
    _primary_key = 'id'

    # 角色常量
    ROLE_OWNER = 'owner'
    ROLE_ADMIN = 'admin'
    ROLE_MEMBER = 'member'

    def __init__(self, id=None, organization_id=None, user_id=None, role=None,
                 created_at=None, **kwargs):
        self.id = id
        self.organization_id = organization_id
        self.user_id = user_id
        self.role = role if role is not None else self.ROLE_MEMBER
        self.created_at = created_at
        # 处理额外的字段
        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def role_display(self):
        """获取角色的显示名称"""
        role_map = {
            self.ROLE_OWNER: '创建者',
            self.ROLE_ADMIN: '管理员',
            self.ROLE_MEMBER: '成员'
        }
        return role_map.get(self.role, self.role)

    def is_owner(self):
        """是否是创建者"""
        return self.role == self.ROLE_OWNER

    def is_admin(self):
        """是否是管理员（包括创建者）"""
        return self.role in [self.ROLE_OWNER, self.ROLE_ADMIN]
