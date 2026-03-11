import os
import tempfile
import json
import uuid
import psycopg2
import psycopg2.extras
import numpy as np
from typing import List, Dict, Any, Optional
from common import log_
from app.models.embeddings.modelfactory import EmbeddingModelFactory
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config.base import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME, PGVECTOR_DIMENSION
import threading
from common.db_utils import get_db_connection

class PVectorStore:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(PVectorStore, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        try:
            # 初始化嵌入模型
            self.embeddings = EmbeddingModelFactory.get_embeddings()
            
            # 固定表名
            self.table_name = "document_chunks"
            
            # 文本分割器
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50,
                separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""]
            )
            
            # 连接数据库
            self.conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            
            # 创建扩展和表（如果不存在）
            self._init_database()

        except Exception as e:
            log_.error(f"初始化PVector客户端失败: {str(e)}")
            raise
        
        self._initialized = True
    
    def _get_connection(self):
        """获取数据库连接"""
        return psycopg2.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME
        )
    
    def _init_database(self):
        """
        初始化数据库：仅确保 pgvector 扩展存在，不再自动创建 document_chunks 表。
        
        说明：
        - 实际向量数据表统一使用脚本中的 dodo_document_chunks；
        - 避免在应用启动时偷偷创建额外的 document_chunks 表。
        """
        try:
            with self.conn.cursor() as cursor:
                # 只负责扩展，表结构由独立 SQL 脚本管理
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                self.conn.commit()
            
        except Exception as e:
            self.conn.rollback()
            log_.error(f"初始化数据库失败: {str(e)}")
            raise
    
    def _ensure_connection(self):
        """确保数据库连接可用"""
        try:
            # 检查连接是否有效
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
            log_.warning(f"数据库连接已断开，重新连接: {str(e)}")
            self.conn = self._get_connection()
        except Exception as e:
            log_.error(f"检查数据库连接失败: {str(e)}")
            raise
    
    def clear_knowledge_base(self, knowledge_base_id):
        """清空指定知识库的所有向量数据
        
        Args:
            knowledge_base_id: 知识库ID
            
        Returns:
            bool: 是否成功
        """
        try:
            self._ensure_connection()
            
            # 删除指定知识库的所有数据
            with self.conn.cursor() as cursor:
                cursor.execute(f"""
                    DELETE FROM {self.table_name}
                    WHERE knowledge_base_id = %s
                """, (knowledge_base_id,))
                
                self.conn.commit()

            return True
        
        except Exception as e:
            self.conn.rollback()
            log_.error(f"清空知识库向量数据失败: {str(e)}")
            return False
    
    def add_texts(self, texts: List[str], metadatas: List[Dict[str, Any]] = None, knowledge_base_id=None):
        """添加文本到向量存储
        
        Args:
            texts: 文本列表
            metadatas: 元数据列表
            knowledge_base_id: 知识库ID（必须提供）
            
        Returns:
            List[str]: 文档ID列表
        """
        try:
            self._ensure_connection()
            
            if not knowledge_base_id:
                raise ValueError("必须提供knowledge_base_id")
            
            # 准备元数据
            if metadatas is None:
                metadatas = [{} for _ in texts]
            
            # 添加文本内容到元数据
            for i, text in enumerate(texts):
                metadatas[i]["text"] = text
            
            # 生成ID
            ids = [str(uuid.uuid4()) for _ in range(len(texts))]
            
            # 计算嵌入向量
            vectors = []
            for text in texts:
                vector = self.embeddings.embed_query(text)
                vectors.append(vector)
            
            # 批量插入
            with self.conn.cursor() as cursor:
                psycopg2.extras.execute_values(
                    cursor,
                    f"""
                    INSERT INTO {self.table_name} (id, content, metadata, knowledge_base_id, embedding)
                    VALUES %s
                    """,
                    [(
                        id, 
                        text, 
                        json.dumps(metadata, ensure_ascii=False), 
                        knowledge_base_id,
                        vector
                    ) for id, text, metadata, vector in zip(ids, texts, metadatas, vectors)],
                    template="(%(v1)s, %(v2)s, %(v3)s::jsonb, %(v4)s, %(v5)s::vector)",
                    page_size=100
                )
                
                self.conn.commit()
            
            return ids
        
        except Exception as e:
            self.conn.rollback()
            log_.error(f"添加文本失败: {str(e)}")
            raise
    
    def add_documents_from_texts(self, texts: List[str], source: str = None, 
                               metadata: Dict[str, Any] = None, knowledge_base_id=None):
        """从文本列表添加文档
        
        Args:
            texts: 原始文本列表
            source: 文档来源
            metadata: 共享元数据
            knowledge_base_id: 知识库ID
            
        Returns:
            List[str]: 文档ID列表
        """
        try:
            if not knowledge_base_id:
                raise ValueError("必须提供knowledge_base_id")
            
            # 分割文本
            all_chunks = []
            all_metadatas = []
            
            for i, text in enumerate(texts):
                chunks = self.text_splitter.split_text(text)
                
                # 创建元数据
                doc_metadata = metadata.copy() if metadata else {}
                if source:
                    doc_metadata["source"] = source
                doc_metadata["doc_id"] = i
                
                # 为每个块添加元数据
                doc_metadatas = [doc_metadata.copy() for _ in chunks]
                
                all_chunks.extend(chunks)
                all_metadatas.extend(doc_metadatas)
            
            # 添加到向量存储
            return self.add_texts(all_chunks, all_metadatas, knowledge_base_id)
        
        except Exception as e:
            log_.error(f"从文本添加文档失败: {str(e)}")
            raise
    
    def similarity_search(self, query, k=3, table_name=None):
        """
        使用向量相似度搜索最相关的文档
        
        Args:
            query: 查询文本
            k: 返回结果数量
            table_name: 可选的表名，默认使用默认向量表
            
        Returns:
            list: 相关文档列表
        """
        # 修改collection_name参数为table_name
        try:
            # 获取查询向量
            query_embedding = self.embeddings.embed_query(query)
            if not query_embedding:
                return []
            
            # 使用表名或默认表
            collection = table_name or "document_chunks"
            
            # 执行向量搜索
            with self.conn.cursor() as cursor:
                cursor.execute(f"""
                    SELECT content, embedding <=> %s::vector AS distance
                    FROM {collection}
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """, (query_embedding, query_embedding, k))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        "text": row[0],
                        "score": 1.0 - float(row[1])  # 转换距离为相似度分数
                    })
            
            return results
        except Exception as e:
            log_.error(f"向量搜索失败: {str(e)}")
            return []
    
    def delete_by_metadata(self, metadata_field: str, metadata_value: Any, knowledge_base_id=None):
        """按元数据删除向量
        
        Args:
            metadata_field: 元数据字段
            metadata_value: 元数据值
            knowledge_base_id: 知识库ID，如果提供则只删除该知识库中的匹配项
            
        Returns:
            int: 删除的文档数量
        """
        try:
            self._ensure_connection()
            
            # 删除匹配的文档
            with self.conn.cursor() as cursor:
                if knowledge_base_id:
                    cursor.execute(f"""
                        DELETE FROM {self.table_name}
                        WHERE metadata->>%s = %s AND knowledge_base_id = %s
                        RETURNING id;
                    """, (metadata_field, str(metadata_value), knowledge_base_id))
                else:
                    cursor.execute(f"""
                        DELETE FROM {self.table_name}
                        WHERE metadata->>%s = %s
                        RETURNING id;
                    """, (metadata_field, str(metadata_value)))
                
                deleted_ids = cursor.fetchall()
                self.conn.commit()
            
            kb_info = f"知识库 {knowledge_base_id}" if knowledge_base_id else "所有知识库"
            return len(deleted_ids)
        
        except Exception as e:
            self.conn.rollback()
            log_.error(f"按元数据删除向量失败: {str(e)}")
            return 0
    
    def save_to_disk(self, directory_path: str, collection_name=None):
        """将向量存储备份到本地磁盘
        
        Args:
            directory_path: 保存目录
            collection_name: 集合名称，不指定则使用实例默认集合
            
        Returns:
            bool: 是否成功
        """
        try:
            self._ensure_connection()
            collection_name = collection_name or self.table_name
            
            # 将集合名称中的连字符替换为下划线
            sanitized_collection_name = collection_name.replace("-", "_")
            
            # 创建目录
            os.makedirs(directory_path, exist_ok=True)
            
            # 获取所有数据
            with self.conn.cursor() as cursor:
                cursor.execute(f"""
                    SELECT id, content, metadata, embedding
                    FROM {sanitized_collection_name};
                """)
                
                all_docs = []
                for id, content, metadata_json, embedding in cursor.fetchall():
                    try:
                        metadata = json.loads(metadata_json)
                    except:
                        metadata = {}
                    
                    all_docs.append({
                        "id": id,
                        "content": content,
                        "metadata": metadata,
                        "vector": list(map(float, embedding))
                    })
            
            # 保存数据
            backup_file = os.path.join(directory_path, f"{collection_name}_backup.json")
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(all_docs, f, ensure_ascii=False, indent=2)
            
            return True
        
        except Exception as e:
            log_.error(f"保存向量存储到磁盘失败: {str(e)}")
            return False
    
    def load_from_disk(self, directory_path: str, collection_name=None, new_collection_name=None):
        """从本地磁盘加载向量存储
        
        Args:
            directory_path: 加载目录
            collection_name: 原始集合名称
            new_collection_name: 新集合名称，默认使用原始集合名称
            
        Returns:
            bool: 是否成功
        """
        try:
            self._ensure_connection()
            collection_name = collection_name or self.table_name
            new_collection_name = new_collection_name or collection_name
            
            # 将新集合名称中的连字符替换为下划线
            sanitized_new_collection_name = new_collection_name.replace("-", "_")
            
            # 检查备份文件
            backup_file = os.path.join(directory_path, f"{collection_name}_backup.json")
            if not os.path.exists(backup_file):
                log_.error(f"备份文件不存在: {backup_file}")
                return False
            
            # 加载数据
            with open(backup_file, 'r', encoding='utf-8') as f:
                all_docs = json.load(f)
            
            # 创建新集合
            if not all_docs:
                log_.warning(f"备份文件为空: {backup_file}")
                return False
            
            # 获取向量维度
            vector_dimension = len(all_docs[0]["vector"])
            
            # 确保表存在
            self.create_collection(new_collection_name, dimension=vector_dimension)
            
            # 添加数据
            with self.conn.cursor() as cursor:
                # 批量插入，每次100条
                batch_size = 100
                for i in range(0, len(all_docs), batch_size):
                    batch = all_docs[i:i+batch_size]
                    
                    # 构建插入数据
                    values = []
                    for doc in batch:
                        values.append((
                            doc["id"],
                            doc.get("content", ""),
                            json.dumps(doc["metadata"], ensure_ascii=False),
                            doc["vector"]
                        ))
                    
                    # 批量插入
                    psycopg2.extras.execute_values(
                        cursor,
                        f"""
                        INSERT INTO {sanitized_new_collection_name} (id, content, metadata, embedding)
                        VALUES %s
                        """,
                        values,
                        template="(%(v1)s, %(v2)s, %(v3)s::jsonb, %(v4)s::vector)",
                        page_size=100
                    )
                
                self.conn.commit()
            
            return True
        
        except Exception as e:
            self.conn.rollback()
            log_.error(f"从磁盘加载向量存储失败: {str(e)}")
            return False 
    
    def similarity_search_by_kb_id(self, query, kb_id, k=3):
        """
        使用向量相似度在指定知识库中搜索最相关的文档
        
        Args:
            query: 查询文本
            kb_id: 知识库ID
            k: 返回结果数量
            
        Returns:
            list: 相关文档列表
        """
        try:
            # 获取查询向量
            query_embedding = self.embeddings.embed_query(query)
            if not query_embedding:
                return []
            
            # 检查向量维度
            query_dim = len(query_embedding)
            
            # 导入连接函数
            from common.db_utils import get_db_connection
            
            # 使用上下文管理器
            with get_db_connection() as conn:
                # 直接使用默认维度，跳过检查维度步骤
                # 执行向量搜索
                results = []
                with conn.cursor() as cursor:
                    # 使用pgvector的向量相似度运算符 <=>
                    cursor.execute("""
                        SELECT dc.content, 1 - (dc.embedding <=> %s::vector) AS similarity
                        FROM dodo_document_chunks dc
                        JOIN dodo_documents d ON dc.document_id = d.id
                        JOIN dodo_kb_documents kd ON d.id = kd.document_id
                        WHERE kd.kb_id = %s
                        ORDER BY dc.embedding <=> %s::vector
                        LIMIT %s
                    """, (query_embedding, kb_id, query_embedding, k))
                    
                    for row in cursor.fetchall():
                        results.append({
                            "text": row[0],
                            "score": float(row[1])
                        })
                
                return results
        except Exception as e:
            log_.error(f"向量搜索失败: {str(e)}")
            return []
    
    def create_collection(self, collection_name, dimension=None):
        """创建集合表
        
        Args:
            collection_name: 集合名称
            dimension: 向量维度，默认使用配置中的维度
            
        Returns:
            bool: 是否成功
        """
        try:
            self._ensure_connection()
            sanitized_collection_name = collection_name.replace("-", "_")
            dimension = dimension or PGVECTOR_DIMENSION
            
            with self.conn.cursor() as cursor:
                # 检查表是否存在
                cursor.execute(f"""
                    SELECT to_regclass('{sanitized_collection_name}');
                """)
                table_exists = cursor.fetchone()[0] is not None
                
                if not table_exists:
                    # 创建表
                    cursor.execute(f"""
                        CREATE TABLE {sanitized_collection_name} (
                            id UUID PRIMARY KEY,
                            content TEXT,
                            metadata JSONB,
                            embedding vector({dimension})
                        );
                    """)
                    
                    # 创建向量索引
                    cursor.execute(f"""
                        CREATE INDEX ON {sanitized_collection_name} USING ivfflat (embedding vector_ip_ops) WITH (lists = 100);
                    """)
                    
                    self.conn.commit()
                    return True
                else:
                    return True
            
        except Exception as e:
            self.conn.rollback()
            log_.error(f"创建集合失败: {str(e)}")
            return False 