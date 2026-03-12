"""
文档生成实体 - 对应数据库dodo_doc_generations表
"""
from app.dao.mapper import BaseEntity


class DocGeneration(BaseEntity):
    """文档生成结果实体类"""
    
    _table_name = 'dodo_doc_generations'
    _primary_key = 'id'
    
    def __init__(self, id=None, user_id=None, template_id=None, user_input=None,
                 generated_content=None, word_minio_path=None, pdf_minio_path=None,
                 status=None, created_at=None, **kwargs):
        self.id = id
        self.user_id = user_id
        self.template_id = template_id
        self.user_input = user_input
        self.generated_content = generated_content
        self.word_minio_path = word_minio_path
        self.pdf_minio_path = pdf_minio_path
        self.status = status
        self.created_at = created_at
        
        for key, value in kwargs.items():
            setattr(self, key, value)
