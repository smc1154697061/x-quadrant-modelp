from app.dao.mapper import BaseEntity


class OrganizationMember(BaseEntity):
    """组织成员实体类，对应数据库dodo_organization_members表"""
    
    _table_name = 'dodo_organization_members'
    _primary_key = 'id'
    
    ROLE_OWNER = 'owner'
    ROLE_ADMIN = 'admin'
    ROLE_MEMBER = 'member'
    
    def __init__(self, id=None, organization_id=None, user_id=None, role=None, joined_at=None, **kwargs):
        self.id = id
        self.organization_id = organization_id
        self.user_id = user_id
        self.role = role or self.ROLE_MEMBER
        self.joined_at = joined_at
        for key, value in kwargs.items():
            setattr(self, key, value)
