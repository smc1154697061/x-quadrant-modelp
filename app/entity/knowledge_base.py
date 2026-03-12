"""
知识库相关实体模型 - 使用原生 SQL
"""
from datetime import datetime
from app.dao.mapper import BaseEntity


class KnowledgeBase(BaseEntity):
    """知识库实体类，对应数据库 dodo_knowledge_bases 表"""
    
    _table_name = 'dodo_knowledge_bases'
    _primary_key = 'id'
    
    def __init__(self, id=None, name=None, description=None, created_by=None,
                 is_public=None, created_at=None, 
                 chunking_strategy=None, chunk_size=None, chunk_overlap=None, **kwargs):
        self.id = id
        self.name = name
        self.description = description
        self.created_by = created_by
        self.is_public = is_public if is_public is not None else False
        self.created_at = created_at
        self.chunking_strategy = chunking_strategy or 'fixed'
        self.chunk_size = chunk_size if chunk_size is not None else 1000
        self.chunk_overlap = chunk_overlap if chunk_overlap is not None else 200
        for key, value in kwargs.items():
            setattr(self, key, value)


class Document(BaseEntity):
    """文档实体类，对应数据库 dodo_documents 表"""
    
    _table_name = 'dodo_documents'
    _primary_key = 'id'
    
    def __init__(self, id=None, name=None, minio_path=None, file_type=None,
                 file_size=None, status=None, created_at=None, **kwargs):
        self.id = id
        self.name = name
        self.minio_path = minio_path
        self.file_type = file_type
        self.file_size = file_size
        self.status = status if status is not None else 'uploaded'
        self.created_at = created_at
        # 处理额外的字段
        for key, value in kwargs.items():
            setattr(self, key, value)


class DocumentChunk(BaseEntity):
    """文档分块实体类，对应数据库 dodo_document_chunks 表"""
    
    _table_name = 'dodo_document_chunks'
    _primary_key = 'id'
    
    def __init__(self, id=None, document_id=None, content=None, embedding=None,
                 chunk_index=None, created_at=None, **kwargs):
        self.id = id
        self.document_id = document_id
        self.content = content
        self.embedding = embedding  # 向量数据（列表格式）
        self.chunk_index = chunk_index
        self.created_at = created_at
        # 处理额外的字段
        for key, value in kwargs.items():
            setattr(self, key, value)