"""
模板实体 - 对应数据库dodo_templates表
"""
from app.dao.mapper import BaseEntity


class Template(BaseEntity):
    """模板实体类"""
    
    _table_name = 'dodo_templates'
    _primary_key = 'id'
    
    def __init__(self, id=None, name=None, tag=None, file_type=None, 
                 minio_path=None, file_size=None, created_by=None, 
                 created_at=None, **kwargs):
        self.id = id
        self.name = name
        self.tag = tag
        self.file_type = file_type
        self.minio_path = minio_path
        self.file_size = file_size
        self.created_by = created_by
        self.created_at = created_at
        
        for key, value in kwargs.items():
            setattr(self, key, value)
