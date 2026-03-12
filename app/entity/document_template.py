"""
文档模板相关实体模型
"""
from datetime import datetime
from app.dao.mapper import BaseEntity


class DocumentTemplate(BaseEntity):
    """文档模板实体类，对应数据库 dodo_document_templates 表"""
    
    _table_name = 'dodo_document_templates'
    _primary_key = 'id'
    
    def __init__(self, id=None, name=None, tags=None, file_type=None,
                 file_size=None, minio_path=None, created_by=None, created_at=None, **kwargs):
        self.id = id
        self.name = name
        self.tags = tags
        self.file_type = file_type
        self.file_size = file_size
        self.minio_path = minio_path
        self.created_by = created_by
        self.created_at = created_at
        # 处理额外的字段
        for key, value in kwargs.items():
            setattr(self, key, value)


class TemplateGeneration(BaseEntity):
    """模板文档生成记录实体类，对应数据库 dodo_template_generations 表"""
    
    _table_name = 'dodo_template_generations'
    _primary_key = 'id'
    
    def __init__(self, id=None, template_id=None, user_id=None, user_input=None,
                 generated_content=None, output_file_path=None, output_file_type=None,
                 status=None, created_at=None, **kwargs):
        self.id = id
        self.template_id = template_id
        self.user_id = user_id
        self.user_input = user_input
        self.generated_content = generated_content
        self.output_file_path = output_file_path
        self.output_file_type = output_file_type
        self.status = status if status is not None else 'pending'
        self.created_at = created_at
        # 处理额外的字段
        for key, value in kwargs.items():
            setattr(self, key, value)
