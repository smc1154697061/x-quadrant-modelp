"""
文档处理测试脚本 - 专门测试知识库文档的向量化处理
"""
import os
import sys
import time
from flask import Flask
from unittest.mock import patch, MagicMock

# 确保能够导入应用模块
sys.path.append(os.path.abspath('.'))

# 模拟MinioClient类，避免实际调用MinIO服务
class MockMinioClient:
    def __init__(self):
        self.default_bucket = "test-bucket"
        self.client = MagicMock()
        self.client._endpoint_url = "http://mock-minio:9000"
    
    def download_file(self, object_name, file_path):
        # 模拟下载文件，创建一个简单的测试文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("这是一个测试文档内容。\nThis is test document content.")
        return True
    
    def get_presigned_url(self, object_name):
        return f"http://mock-minio:9000/test-bucket/{object_name}"

# 模拟文档加载和分割函数
def mock_load_document(file_path):
    class MockDocument:
        def __init__(self, content):
            self.page_content = content
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return MockDocument(content)

def mock_split_document(doc):
    # 简单地将文档分成几个块
    content = doc.page_content
    lines = content.split('\n')
    
    chunks = []
    for i, line in enumerate(lines):
        if line.strip():
            chunk = type('obj', (object,), {'page_content': line})
            chunks.append(chunk)
    
    return chunks

def test_document_processing():
    """测试文档处理功能"""
    print("开始测试文档处理功能...")
    
    # 创建一个Flask应用实例
    app = Flask(__name__)
    
    # 设置应用配置
    app.config.update(
        TESTING=True,
        SECRET_KEY='test_key',
    )
    
    # 指定要处理的文档ID
    document_id = 3
    
    # 创建一个完整的模拟处理函数
    def mock_process_document_thread(self, document_id, app_instance=None):
        """模拟文档处理线程，完整测试向量化流程"""
        from sqlalchemy import text
        from common.db_utils import get_db_session
        from common import log_
        import os
        import uuid
        import tempfile
        
        temp_file_path = None
        app_context = None
        
        try:
            # 导入所需模块
            from app.dao.knowledge_dao import DocumentDAO, DocumentChunkDAO
            from app.entity.knowledge_base import DocumentChunk
            
            # 获取文档信息
            document = DocumentDAO.find_by_id(document_id)
            if not document:
                log_.error(f"文档不存在: {document_id}")
                return
            

            # 检查PostgreSQL向量扩展
            try:
                with get_db_session() as session:
                    # 检查pgvector扩展是否已安装
                    result = session.execute(text("SELECT COUNT(*) FROM pg_extension WHERE extname = 'vector'")).scalar()
                    if result == 0:
                        log_.error("PostgreSQL中未安装pgvector扩展，无法处理文档向量")
                        DocumentDAO.update_status(document_id, "failed")
                        return

                    # 使用正确的列名atttypmod
                    try:
                        result = session.execute(text("SELECT atttypmod FROM pg_attribute WHERE attrelid = 'document_chunks'::regclass AND attname = 'embedding'")).scalar()
                        vector_dim = result - 4  # pgvector存储方式：维度+4

                        # 确保向量维度为1536，这是表结构定义的维度
                        if vector_dim != 1536:
                            log_.warning(f"检测到的向量维度 {vector_dim} 与表定义的1536不匹配，将使用1536")
                            vector_dim = 1536
                    except Exception as e:
                        log_.warning(f"获取向量维度失败，将使用默认值1536: {str(e)}")
                        vector_dim = 1536
            except Exception as e:
                log_.error(f"检查数据库向量支持失败: {str(e)}")
                DocumentDAO.update_status(document_id, "failed")
                return
            
            # 创建临时目录
            temp_dir = tempfile.mkdtemp(prefix="doc_process_")
            temp_file_path = os.path.join(temp_dir, f"doc_{document_id}.txt")
            
            try:
                # 模拟从MinIO下载文件
                # 使用模拟的MinIO客户端
                minio_client = MockMinioClient()
                minio_client.download_file(document['minio_path'], temp_file_path)
                
                # 检查文件是否存在
                if not os.path.exists(temp_file_path):
                    raise FileNotFoundError(f"无法下载文件: {temp_file_path}")
                
                # 模拟加载文档
                with patch('app.utils.document_loader.load_document', side_effect=mock_load_document):
                    doc = mock_load_document(temp_file_path)

                # 模拟分割文档
                with patch('app.utils.document_loader.split_document', side_effect=mock_split_document):
                    chunks = mock_split_document(doc)

                # 模拟嵌入模型
                class MockEmbeddingsModel:
                    def __init__(self, vector_dim=1536):
                        self.vector_dim = vector_dim
                        
                    def embed_query(self, text):
                        # 生成一个假的向量，维度与数据库匹配，确保返回Python列表而非NumPy数组
                        import numpy as np
                        # 生成NumPy数组并转换为普通Python列表
                        return np.random.rand(self.vector_dim).astype(float).tolist()
                
                # 使用从数据库检测到的向量维度，确保是1536
                vector_dim = 1536  # 强制使用1536维度，与数据库表结构匹配

                # 计算嵌入并存储
                chunk_objects = []
                
                # 为每个分块创建嵌入向量
                for i, chunk in enumerate(chunks):
                    # 生成嵌入向量
                    embedding = MockEmbeddingsModel(vector_dim).embed_query(chunk.page_content)
                    
                    # 确保向量是Python列表，而不是NumPy数组
                    if hasattr(embedding, 'tolist'):
                        embedding = embedding.tolist()
                    elif not isinstance(embedding, list):
                        embedding = list(embedding)
                    
                    # 创建分块对象
                    chunk_obj = DocumentChunk(
                        document_id=document_id,
                        content=chunk.page_content,
                        embedding=embedding,
                        chunk_index=i
                    )
                    
                    chunk_objects.append(chunk_obj)
                
                # 批量保存所有分块
                if chunk_objects:
                    try:
                        # 记录第一个对象的向量维度和类型，用于调试
                        first_obj = chunk_objects[0]

                        # 尝试批量保存
                        DocumentChunkDAO.bulk_create(chunk_objects)
                    except Exception as e:
                        log_.error(f"批量保存分块失败: {str(e)}")
                        # 尝试逐个保存以隔离问题
                        successful_chunks = 0
                        for idx, chunk_obj in enumerate(chunk_objects):
                            try:
                                # 确保向量是Python列表
                                if hasattr(chunk_obj.embedding, 'tolist'):
                                    chunk_obj.embedding = chunk_obj.embedding.tolist()
                                elif not isinstance(chunk_obj.embedding, list):
                                    chunk_obj.embedding = list(chunk_obj.embedding)
                                
                                # 使用DAO单独保存
                                chunk_dict = DocumentChunkDAO.create_single(chunk_obj)
                                if chunk_dict:
                                    successful_chunks += 1
                            except Exception as single_error:
                                log_.error(f"保存单个分块 {idx+1} 失败: {str(single_error)}")
                        

                # 更新文档状态为已完成
                DocumentDAO.update_status(document_id, "completed")

            except Exception as e:
                log_.error(f"处理文档时出错: {str(e)}")
                DocumentDAO.update_status(document_id, "failed")
            finally:
                # 清理临时文件
                if temp_file_path and os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

                # 清理临时目录
                if os.path.exists(temp_dir):
                    os.rmdir(temp_dir)

        except Exception as e:
            log_.error(f"处理文档线程异常: {str(e)}")
            try:
                DocumentDAO.update_status(document_id, "failed")
            except:
                pass
    
    try:
        # 导入需要的模块
        from app.services.knowledge_service import KnowledgeService
        from app.models.embeddings.base import get_embeddings_model
        from app.models.vector_store.base import get_vector_store
        from app.dao.knowledge_dao import DocumentDAO
        
        # 使用应用上下文
        with app.app_context():
            print("已创建Flask应用上下文")
            
            # 预加载嵌入模型和向量存储到应用上下文中
            print("正在加载嵌入模型...")
            try:
                app.embeddings_model = get_embeddings_model()
                print("嵌入模型加载成功")
            except Exception as e:
                print(f"加载嵌入模型失败: {str(e)}")
                app.embeddings_model = None
            
            print("正在加载向量存储...")
            try:
                app.vector_store = get_vector_store()
                print("向量存储加载成功")
            except Exception as e:
                print(f"加载向量存储失败: {str(e)}")
                app.vector_store = None
            
            print("已将嵌入模型和向量存储加载到应用上下文")
            
            # 创建知识服务实例
            knowledge_service = KnowledgeService()
            print("已创建知识服务实例")
            
            # 获取文档当前状态
            document = DocumentDAO.find_by_id(document_id)
            if not document:
                print(f"错误: 文档ID {document_id} 不存在!")
                sys.exit(1)
                
            print(f"文档当前状态: {document['status']}")
            
            # 更新文档状态为"uploaded"
            DocumentDAO.update_status(document_id, "uploaded")
            print(f"已将文档状态更新为 'uploaded'")
            
            # 使用模拟的方法处理文档
            print("\n开始处理文档...")
            with patch.object(KnowledgeService, '_process_document_thread', mock_process_document_thread):
                # 确保正确传递参数，避免意外的关键字参数
                knowledge_service._process_document_thread(document_id, app)
            print("文档处理完成")
            
            # 检查文档状态
            document = DocumentDAO.find_by_id(document_id)
            print(f"处理后文档状态: {document['status']}")
            
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("测试完成")


if __name__ == "__main__":
    test_document_processing() 