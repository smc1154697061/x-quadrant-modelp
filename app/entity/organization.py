from app.dao.mapper import BaseEntity


class Organization(BaseEntity):
    """组织实体类，对应数据库dodo_organizations表"""
    
    _table_name = 'dodo_organizations'
    _primary_key = 'id'
    
    def __init__(self, id=None, name=None, description=None, created_by=None, created_at=None, **kwargs):
        self.id = id
        self.name = name
        self.description = description
        self.created_by = created_by
        self.created_at = created_at
        for key, value in kwargs.items():
            setattr(self, key, value)
