"""
模板文档相关实体模型
"""
from datetime import datetime
from app.dao.mapper import BaseEntity


class DocumentTemplate(BaseEntity):
    """文档模板实体类"""
    
    _table_name = 'dodo_document_templates'
    _primary_key = 'id'
    
    def __init__(self, id=None, name=None, description=None, category=None,
                 minio_path=None, file_type=None, file_size=None, created_by=None,
                 is_public=None, created_at=None, **kwargs):
        self.id = id
        self.name = name
        self.description = description
        self.category = category
        self.minio_path = minio_path
        self.file_type = file_type
        self.file_size = file_size
        self.created_by = created_by
        self.is_public = is_public if is_public is not None else False
        self.created_at = created_at
        for key, value in kwargs.items():
            setattr(self, key, value)


class GeneratedDocument(BaseEntity):
    """生成的文档实体类"""
    
    _table_name = 'dodo_generated_documents'
    _primary_key = 'id'
    
    def __init__(self, id=None, template_id=None, template_name=None, user_input=None,
                 generated_content=None, output_format=None, minio_path=None,
                 created_by=None, created_at=None, **kwargs):
        self.id = id
        self.template_id = template_id
        self.template_name = template_name
        self.user_input = user_input
        self.generated_content = generated_content
        self.output_format = output_format or 'word'
        self.minio_path = minio_path
        self.created_by = created_by
        self.created_at = created_at
        for key, value in kwargs.items():
            setattr(self, key, value)
