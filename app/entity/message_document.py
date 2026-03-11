"""
消息-文档关联实体 - 对应 dodo_message_documents 表
"""
from app.dao.mapper.base_entity import BaseEntity


class MessageDocument(BaseEntity):
    """消息-文档关联实体（用于对话中上传的文件）"""
    
    _table_name = 'dodo_message_documents'
    _primary_key = 'id'
    
    def __init__(self, id=None, message_id=None, document_id=None, created_at=None):
        self.id = id
        self.message_id = message_id
        self.document_id = document_id
        self.created_at = created_at
