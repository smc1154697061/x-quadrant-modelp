"""
知识库数据访问对象 (KnowledgeDAO) - 使用原生 SQL + BaseMapper
"""
from typing import List, Optional
import json

from common import log_
from common.error_codes import APIException, ErrorCode
from app.dao.mapper import BaseMapper
from app.entity.knowledge_base import KnowledgeBase, Document, DocumentChunk
from common.db_utils import get_db_connection


class KnowledgeBaseDAO(BaseMapper):
    """知识库Mapper，继承BaseMapper获得通用CRUD"""
    
    entity_class = KnowledgeBase
    table_name = 'dodo_knowledge_bases'
    primary_key = 'id'
    
    @classmethod
    def find_by_id(cls, kb_id):
        """通过ID查找知识库"""
        mapper = cls()
        kb = mapper.select_by_id(kb_id)
        return kb.to_dict() if kb else None
    
    @classmethod
    def find_by_user_id(cls, user_id, include_public=True):
        """查找用户的所有知识库"""
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                if include_public:
                    sql = """
                        SELECT * FROM dodo_knowledge_bases 
                        WHERE created_by = %s OR is_public = true 
                        ORDER BY id DESC
                    """
                    cursor.execute(sql, (user_id,))
                else:
                    sql = """
                        SELECT * FROM dodo_knowledge_bases 
                        WHERE created_by = %s 
                        ORDER BY id DESC
                    """
                    cursor.execute(sql, (user_id,))
                
                columns = [desc[0] for desc in cursor.description]
                results = []
                for row in cursor.fetchall():
                    row_dict = dict(zip(columns, row))
                    kb = KnowledgeBase.from_dict(row_dict)
                    results.append(kb.to_dict())
                return results
    
    @classmethod
    def get_all_knowledge_bases(cls):
        """获取所有知识库"""
        mapper = cls()
        kbs = mapper.select_all(order_by="id DESC")
        return [kb.to_dict() for kb in kbs]
    
    @classmethod
    def create(cls, kb: KnowledgeBase):
        """创建新知识库"""
        try:
            mapper = cls()
            kb_id = mapper.insert(kb)
            kb.id = kb_id
            return kb.to_dict()
        except Exception as e:
            log_.error(f"创建知识库失败: {str(e)}")
            raise APIException(ErrorCode.DATABASE_ERROR, msg="创建知识库失败")
    
    @classmethod
    def update(cls, kb_id, data):
        """更新知识库信息"""
        try:
            mapper = cls()
            kb = mapper.select_by_id(kb_id)
            if not kb:
                return False
            
            # 更新字段
            for key, value in data.items():
                if hasattr(kb, key):
                    setattr(kb, key, value)
            
            result = mapper.update_by_id(kb)
            return result > 0
        except Exception as e:
            log_.error(f"更新知识库失败: {str(e)}")
            raise APIException(ErrorCode.DATABASE_ERROR, msg="更新知识库失败")
    
    @classmethod
    def delete(cls, kb_id):
        """删除知识库"""
        try:
            mapper = cls()
            result = mapper.delete_by_id(kb_id)
            return result > 0
        except Exception as e:
            log_.error(f"删除知识库失败: {str(e)}")
            raise APIException(ErrorCode.DATABASE_ERROR, msg="删除知识库失败")
    
    @classmethod
    def count(cls):
        """获取知识库总数"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM dodo_knowledge_bases")
                    return cursor.fetchone()[0]
        except Exception as e:
            log_.error(f"统计知识库总数失败: {str(e)}")
            raise APIException(ErrorCode.DATABASE_ERROR, msg="统计知识库总数失败")
    
    @classmethod
    def find_public_only(cls):
        """获取所有公共知识库"""
        mapper = cls()
        kbs = mapper.select_by_conditions({"is_public": True}, order_by="id DESC")
        return [kb.to_dict() for kb in kbs]


class DocumentDAO(BaseMapper):
    """文档Mapper，继承BaseMapper获得通用CRUD"""
    
    entity_class = Document
    table_name = 'dodo_documents'
    primary_key = 'id'
    
    @classmethod
    def find_by_id(cls, document_id):
        """通过ID查找文档"""
        mapper = cls()
        doc = mapper.select_by_id(document_id)
        return doc.to_dict() if doc else None
    
    @classmethod
    def find_by_kb_id(cls, kb_id):
        """查找知识库中的所有文档（通过关联表）"""
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT d.id, d.name, d.minio_path, d.file_type, 
                           d.file_size, d.status, d.created_at
                    FROM dodo_documents d
                    INNER JOIN dodo_kb_documents kd ON d.id = kd.document_id
                    WHERE kd.kb_id = %s
                    ORDER BY d.created_at DESC
                """, (kb_id,))
                
                columns = [desc[0] for desc in cursor.description]
                results = []
                for row in cursor.fetchall():
                    row_dict = dict(zip(columns, row))
                    doc = Document.from_dict(row_dict)
                    results.append(doc.to_dict())
                return results
    
    @classmethod
    def create(cls, document: Document):
        """创建新文档"""
        try:
            mapper = cls()
            doc_id = mapper.insert(document)
            document.id = doc_id
            return document.to_dict()
        except Exception as e:
            log_.error(f"创建文档失败: {str(e)}")
            raise APIException(ErrorCode.DATABASE_ERROR, msg="创建文档失败")
    
    @classmethod
    def update_status(cls, document_id, status):
        """更新文档状态"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "UPDATE dodo_documents SET status = %s WHERE id = %s",
                        (status, document_id)
                    )
                    return cursor.rowcount > 0
        except Exception as e:
            log_.error(f"更新文档状态失败: {str(e)}")
            raise APIException(ErrorCode.DATABASE_ERROR, msg="更新文档状态失败")
    
    @classmethod
    def delete(cls, document_id):
        """删除文档"""
        try:
            mapper = cls()
            result = mapper.delete_by_id(document_id)
            return result > 0
        except Exception as e:
            log_.error(f"删除文档失败: {str(e)}")
            raise APIException(ErrorCode.DATABASE_ERROR, msg="删除文档失败")
    
    @classmethod
    def count_by_kb_id(cls, kb_id):
        """统计知识库中的文档数量"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT COUNT(*) FROM dodo_kb_documents WHERE kb_id = %s
                    """, (kb_id,))
                    return cursor.fetchone()[0]
        except Exception as e:
            log_.error(f"统计知识库文档数量失败: {str(e)}")
            return 0


class DocumentChunkDAO(BaseMapper):
    """文档分块Mapper，继承BaseMapper获得通用CRUD"""
    
    entity_class = DocumentChunk
    table_name = 'dodo_document_chunks'
    primary_key = 'id'
    
    @classmethod
    def find_by_document_id(cls, document_id):
        """查找文档的所有分块"""
        mapper = cls()
        chunks = mapper.select_by_conditions({"document_id": document_id})
        return [chunk.to_dict() for chunk in chunks]
    
    @classmethod
    def create(cls, chunk: DocumentChunk):
        """创建文档分块"""
        try:
            # 处理 embedding 向量（转换为 PostgreSQL 数组格式）
            if chunk.embedding and isinstance(chunk.embedding, list):
                chunk.embedding = json.dumps(chunk.embedding)
            
            mapper = cls()
            chunk_id = mapper.insert(chunk)
            chunk.id = chunk_id
            return chunk.to_dict()
        except Exception as e:
            log_.error(f"创建文档分块失败: {str(e)}")
            raise APIException(ErrorCode.DATABASE_ERROR, msg="创建文档分块失败")
    
    @classmethod
    def create_single(cls, chunk_obj: DocumentChunk):
        """创建单个文档块对象"""
        return cls.create(chunk_obj)
    
    @classmethod
    def bulk_create(cls, chunks: List[DocumentChunk]):
        """批量创建文档分块"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    for chunk in chunks:
                        # 处理embedding
                        embedding_str = None
                        if chunk.embedding:
                            if isinstance(chunk.embedding, list):
                                # 转换为PostgreSQL数组格式: '[1,2,3]'
                                embedding_str = str(chunk.embedding)
                            elif isinstance(chunk.embedding, str):
                                embedding_str = chunk.embedding
                        
                        cursor.execute("""
                            INSERT INTO dodo_document_chunks 
                            (document_id, content, embedding, chunk_index, created_at)
                            VALUES (%s, %s, %s::vector, %s, NOW())
                        """, (chunk.document_id, chunk.content, embedding_str, chunk.chunk_index))
            
            return len(chunks)
        except Exception as e:
            log_.error(f"批量创建文档分块失败: {str(e)}")
            raise APIException(ErrorCode.DATABASE_ERROR, msg="批量创建文档分块失败")
    
    @classmethod
    def delete_by_document_id(cls, document_id):
        """删除文档的所有分块"""
        try:
            mapper = cls()
            result = mapper.delete({"document_id": document_id})
            return result
        except Exception as e:
            log_.error(f"删除文档分块失败: {str(e)}")
            raise APIException(ErrorCode.DATABASE_ERROR, msg="删除文档分块失败")
    
    @classmethod
    def search_similar(cls, kb_id: int, query_embedding: list, top_k: int = 5):
        """向量相似度搜索
        
        参数:
            kb_id: 知识库ID
            query_embedding: 查询向量
            top_k: 返回top K个结果
        
        返回:
            相似文档分块列表
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # 将列表转为PostgreSQL数组格式
                    embedding_str = str(query_embedding)
                    
                    # 使用向量相似度搜索
                    cursor.execute("""
                        SELECT dc.id, dc.document_id, dc.content, dc.chunk_index, dc.created_at,
                               d.name as document_name,
                               1 - (dc.embedding <=> %s::vector) as similarity
                        FROM dodo_document_chunks dc
                        INNER JOIN dodo_documents d ON dc.document_id = d.id
                        INNER JOIN dodo_kb_documents kd ON d.id = kd.document_id
                        WHERE kd.kb_id = %s AND dc.embedding IS NOT NULL
                        ORDER BY dc.embedding <=> %s::vector
                        LIMIT %s
                    """, (embedding_str, kb_id, embedding_str, top_k))
                    
                    results = []
                    for row in cursor.fetchall():
                        results.append({
                            'id': row[0],
                            'document_id': row[1],
                            'content': row[2],
                            'chunk_index': row[3],
                            'created_at': row[4].isoformat() if row[4] else None,
                            'document_name': row[5],
                            'similarity': float(row[6]) if row[6] else 0.0
                        })
                    return results
        except Exception as e:
            log_.error(f"向量相似度搜索失败: {str(e)}")
            return []
