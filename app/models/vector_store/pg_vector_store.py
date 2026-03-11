"""
PostgreSQL向量存储实现
"""
from typing import Dict, List, Any, Optional
import uuid

from app.models.vector_store.base import BaseVectorStore
from app.models.embeddings.base import get_embeddings_model
from app.entity.knowledge_base import DocumentChunk
from common.db_utils import get_db_connection
from common import log_

class PGVectorStore(BaseVectorStore):
    """PostgreSQL向量存储实现，使用数组类型代替pgvector"""
    
    def __init__(self):
        """初始化PostgreSQL向量存储"""
        self.embeddings_model = get_embeddings_model()
    
    def add_texts(self, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """
        向向量存储添加文本
        
        Args:
            texts: 文本列表
            metadatas: 元数据列表
            
        Returns:
            List[str]: 文档ID列表
        """
        if not texts:
            return []
        
        # 确保元数据列表与文本列表长度相同
        if metadatas is None:
            metadatas = [{} for _ in texts]
        elif len(metadatas) != len(texts):
            raise ValueError("元数据列表长度必须与文本列表长度相同")
        
        # 获取文本嵌入
        embeddings = self.embeddings_model.embed_documents(texts)
        
        # 准备数据库对象
        chunks = []
        ids = []
        
        for i, (text, embedding, metadata) in enumerate(zip(texts, embeddings, metadatas)):
            # 确保embedding是Python列表
            if not isinstance(embedding, list):
                embedding = embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
                
            # 从元数据中获取文档ID
            document_id = metadata.get("document_id")
            if not document_id:
                # 如果没有提供文档ID，则跳过
                log_.warning(f"跳过没有document_id的文本: {text[:50]}...")
                continue
            
            # 创建文档块对象
            chunk = DocumentChunk(
                document_id=document_id,
                content=text,
                embedding=embedding,
                chunk_index=metadata.get("chunk_index", i)
            )
            chunks.append(chunk)
            ids.append(str(uuid.uuid4()))
        
        # 批量保存到数据库
        try:
            with get_db_session() as session:
                session.bulk_save_objects(chunks)
                return ids
        except Exception as e:
            log_.error(f"向PostgreSQL添加文本失败: {str(e)}")
            return []
    
    def search(self, query: str, k: int = 4) -> List[Dict[str, Any]]:
        """
        搜索与查询最相似的文档
        
        Args:
            query: 查询字符串
            k: 返回结果数量
            
        Returns:
            List[Dict[str, Any]]: 搜索结果列表
        """
        try:
            # 获取查询的嵌入向量
            query_embedding = self.embeddings_model.embed_query(query)
            
            # 确保查询向量是列表
            if not isinstance(query_embedding, list):
                query_embedding = query_embedding.tolist() if hasattr(query_embedding, 'tolist') else list(query_embedding)
            
            # 连接数据库
            session = SessionLocal()
            
            try:
                # 使用原生SQL构建查询
                query_sql = text("""
                    SELECT 
                        dc.id, 
                        dc.document_id, 
                        dc.content, 
                        dc.chunk_index,
                        dc.created_at,
                        SQRT(SUM(POWER(CAST(e.val AS FLOAT) - CAST(:embedding[e.idx] AS FLOAT), 2))) AS distance
                    FROM 
                        document_chunks dc,
                        LATERAL unnest(dc.embedding) WITH ORDINALITY AS e(val, idx)
                    WHERE
                        dc.embedding IS NOT NULL
                    GROUP BY 
                        dc.id, dc.document_id, dc.content, dc.chunk_index, dc.created_at
                    ORDER BY 
                        distance ASC
                    LIMIT :limit
                """)
                
                # 执行查询
                result = session.execute(query_sql, {'embedding': query_embedding, 'limit': k})
                
                # 格式化结果
                formatted_results = []
                for row in result:
                    formatted_results.append({
                        "id": row.id,
                        "document_id": row.document_id,
                        "content": row.content,
                        "chunk_index": row.chunk_index,
                        "distance": float(row.distance),
                        "score": 1.0 / (1.0 + float(row.distance))  # 转换距离为分数
                    })
                
                return formatted_results
            finally:
                session.close()
        except Exception as e:
            log_.error(f"PostgreSQL向量搜索失败: {str(e)}")
            return []
    
    def delete(self, document_ids: List[str]) -> None:
        """
        删除文档的所有块
        
        Args:
            document_ids: 文档ID列表
        """
        try:
            with get_db_session() as session:
                for doc_id in document_ids:
                    session.query(DocumentChunk).filter(
                        DocumentChunk.document_id == doc_id
                    ).delete()
        except Exception as e:
            log_.error(f"从PostgreSQL删除文档失败: {str(e)}") 