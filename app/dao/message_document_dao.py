"""
消息-文档关联DAO - 处理对话中的文件上传
"""
from typing import List, Optional
from app.dao.mapper import BaseMapper, select
from app.entity.message_document import MessageDocument
from app.entity.knowledge_base import Document
from common import log_
from common.db_utils import get_db_connection


class MessageDocumentDAO(BaseMapper):
    """消息-文档关联DAO，继承BaseMapper获得通用CRUD"""
    
    entity_class = MessageDocument
    table_name = 'dodo_message_documents'
    primary_key = 'id'
    
    def create_message_document(self, message_id: int, document_id: int):
        """创建消息-文档关联
        
        参数:
            message_id: 消息ID
            document_id: 文档ID
        
        返回:
            关联记录ID
        """
        message_doc = MessageDocument(
            message_id=message_id,
            document_id=document_id
        )
        return self.insert(message_doc)
    
    def get_message_documents(self, message_id: int) -> List[dict]:
        """获取消息关联的文档列表
        
        参数:
            message_id: 消息ID
        
        返回:
            文档信息列表（包含文件名、minio_path等）
        """
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        d.id,
                        d.name,
                        d.file_type,
                        d.file_size,
                        d.minio_path,
                        md.created_at
                    FROM dodo_message_documents md
                    JOIN dodo_documents d ON md.document_id = d.id
                    WHERE md.message_id = %s
                    ORDER BY md.created_at ASC
                """, (message_id,))
                
                results = cursor.fetchall()
                documents = []
                for row in results:
                    documents.append({
                        'id': row[0],
                        'filename': row[1],
                        'file_type': row[2],
                        'file_size': row[3],
                        'minio_path': row[4],
                        'created_at': row[5].isoformat() if row[5] else None
                    })
                
                return documents
    
    def get_document_ids_by_message(self, message_id: int) -> List[int]:
        """获取消息关联的文档ID列表
        
        参数:
            message_id: 消息ID
        
        返回:
            文档ID列表
        """
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT document_id FROM dodo_message_documents WHERE message_id = %s",
                    (message_id,)
                )
                return [row[0] for row in cursor.fetchall()]
    
    def delete_by_message_id(self, message_id: int) -> int:
        """删除消息的所有文档关联
        
        参数:
            message_id: 消息ID
        
        返回:
            删除的记录数
        """
        return self.delete({'message_id': message_id})
