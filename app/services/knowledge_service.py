"""
知识库服务 - 处理知识库和文档管理
"""
import os
import json
import shutil
import time
import uuid
import tempfile
import hashlib
from werkzeug.utils import secure_filename
from datetime import datetime
from common import log_
from flask import current_app
from app.models.vector_store.povector_store import PVectorStore
from common.minio_client import MinioClient
from common.db_utils import get_db_connection
from app.entity.knowledge_base import KnowledgeBase, Document, DocumentChunk
from app.dao.knowledge_dao import KnowledgeBaseDAO, DocumentDAO, DocumentChunkDAO
from common.error_codes import APIException, ErrorCode
from app.utils.document_loader import load_document, split_document

class KnowledgeService:
    """知识库服务类"""
    
    def __init__(self):
        """初始化知识库服务"""
        # 初始化MinIO客户端
        self.minio_client = MinioClient.get_instance()
        
        # 向量模型和向量存储（优先使用全局预加载的模型，如果没有则延迟加载）
        self._embeddings_model = None
        self._vector_store = None
        
        # 允许上传的文件类型（包含图片类型）
        self.allowed_extensions = {
            'txt', 'pdf', 'doc', 'docx', 'csv', 'xls', 'xlsx', 
            'ppt', 'pptx', 'md', 'html', 'htm',
            'jpg', 'jpeg', 'png', 'bmp', 'tiff', 'tif', 'gif', 'webp'
        }
        
        self._presigned_url_cache = {}  # 添加预签名URL缓存
        self._cache_expiry = {}  # URL过期时间缓存
    
    @property
    def embeddings_model(self):
        """获取嵌入模型（优先使用全局预加载的模型）"""
        if self._embeddings_model is None:
            # 优先从Flask g对象获取
            try:
                from flask import g
                if hasattr(g, 'embedding_model'):
                    self._embeddings_model = g.embedding_model
                    return self._embeddings_model
            except:
                pass
            
            # 其次从应用上下文获取
            try:
                from flask import current_app
                if hasattr(current_app, 'embedding_model'):
                    self._embeddings_model = current_app.embedding_model
                    return self._embeddings_model
            except:
                pass
            
            # 最后尝试从工厂获取单例
            from app.models.embeddings.modelfactory import EmbeddingModelFactory
            self._embeddings_model = EmbeddingModelFactory.get_embeddings()
            
        return self._embeddings_model

    @property
    def vector_store(self):
        """获取向量存储（优先使用全局预加载的存储）"""
        if self._vector_store is None:
            # 优先从Flask应用上下文获取预加载的向量存储
            try:
                from flask import current_app
                if hasattr(current_app, '_get_current_object'):
                    # 确保获取实际的应用实例，而不是代理对象
                    app = current_app._get_current_object()
                    if hasattr(app, 'vector_store'):
                        self._vector_store = app.vector_store
                    else:
                        # 没有预加载存储时，懒加载
                        from app.models.vector_store.base import get_vector_store
                        self._vector_store = get_vector_store()
            except RuntimeError as e:
                # 应用上下文不存在的情况下直接懒加载
                from app.models.vector_store.base import get_vector_store
                self._vector_store = get_vector_store()
            except Exception as e:
                from app.models.vector_store.base import get_vector_store
                self._vector_store = get_vector_store()
        return self._vector_store
    
    def _is_allowed_file(self, filename):
        """检查文件类型是否允许上传（基于原始文件名提取扩展名）"""
        try:
            import os
            ext = os.path.splitext(filename)[1].lower().lstrip('.')
            return ext in self.allowed_extensions
        except Exception:
            return False
    
    def create_knowledge_base(self, dto, user_id):
        """创建知识库（面向对象风格）
        
        参数:
            dto: KnowledgeBaseCreateDTO对象
            user_id: 当前用户ID
        
        返回:
            知识库字典
        """
        try:
            # 创建知识库实体对象
            from app.entity.knowledge_base import KnowledgeBase
            kb = KnowledgeBase(
                name=dto.name,
                description=dto.description,
                created_by=user_id,
                is_public=False
            )
            
            # 调用DAO创建
            kb_dict = KnowledgeBaseDAO().create(kb)
            
            return kb_dict
        except Exception as e:
            log_.error(f"创建知识库失败: {str(e)}")
            raise APIException(ErrorCode.SYSTEM_ERROR, msg=f"创建知识库失败: {str(e)}")
    
    def get_knowledge_bases(self, user_id=None):
        """获取知识库列表"""
        try:
            if user_id:
                # 用户已登录，获取用户自己的知识库和公共知识库
                kb_list = KnowledgeBaseDAO().find_by_user_id(user_id, include_public=True)
            else:
                # 用户未登录，返回公共知识库
                kb_list = KnowledgeBaseDAO().find_public_only()

            # 为每个知识库添加文档信息
            for kb in kb_list:
                kb_id = kb["id"]
                documents = DocumentDAO().find_by_kb_id(kb_id)
                
                # 为每个文档添加预签名URL
                for doc in documents:
                    if doc["minio_path"]:
                        doc["url"] = self.minio_client.get_presigned_url(doc["minio_path"])
                
                kb["documents"] = documents
            
            return kb_list
        except Exception as e:
            log_.error(f"获取知识库列表失败: {str(e)}")
            raise APIException(ErrorCode.SYSTEM_ERROR, msg=f"获取知识库列表失败: {str(e)}")
    
    def get_knowledge_bases_basic(self, user_id=None):
        """获取知识库基本信息列表（不包含文档）"""
        try:
            if user_id:
                kb_list = KnowledgeBaseDAO().find_by_user_id(user_id, include_public=True)
            else:
                kb_list = KnowledgeBaseDAO().find_public_only()
            
            # 不添加文档信息
            return kb_list
        except Exception as e:
            log_.error(f"获取知识库列表失败: {str(e)}")
            raise APIException(ErrorCode.SYSTEM_ERROR, msg=f"获取知识库列表失败: {str(e)}")
    
    def get_knowledge_base(self, kb_id):
        """获取单个知识库详情"""
        try:
            kb = KnowledgeBaseDAO().find_by_id(kb_id)
            if not kb:
                raise FileNotFoundError("知识库不存在")
            
            # 获取知识库中的文档
            documents = DocumentDAO().find_by_kb_id(kb_id)
            
            # 为每个文档添加预签名URL
            for doc in documents:
                if doc["minio_path"]:
                    try:
                        doc["url"] = self.minio_client.get_presigned_url(doc["minio_path"])
                    except Exception as e:
                        log_.error(f"为文档 {doc['id']} 生成预签名URL失败: {str(e)}")
                        # 使用静态URL作为回退
                        doc["url"] = f"{self.minio_client.client._endpoint_url}/{self.minio_client.default_bucket}/{doc['minio_path']}"
            
            kb["documents"] = documents
            return kb
        except FileNotFoundError:
            raise
        except Exception as e:
            log_.error(f"获取知识库详情失败: {str(e)}")
            raise APIException(ErrorCode.SYSTEM_ERROR, msg=f"获取知识库详情失败: {str(e)}")
    
    def get_knowledge_base_details(self, kb_id):
        """获取单个知识库详细信息（包含文档和URL）"""
        try:
            kb = KnowledgeBaseDAO().find_by_id(kb_id)
            if not kb:
                raise FileNotFoundError("知识库不存在")
            
            # 添加文档信息和URL
            documents = DocumentDAO().find_by_kb_id(kb_id)
            for doc in documents:
                if doc["minio_path"]:
                    doc["url"] = self.minio_client.get_presigned_url(doc["minio_path"])
            
            kb["documents"] = documents
            return kb
        except Exception as e:
            log_.error(f"获取知识库详情失败: {str(e)}")
            raise APIException(ErrorCode.SYSTEM_ERROR, msg=f"获取知识库详情失败: {str(e)}")
    
    def delete_knowledge_base(self, kb_id):
        """删除知识库"""
        try:
            # 检查知识库是否被机器人使用
            is_used = self.is_knowledge_base_used_by_bot(kb_id)
            if is_used:
                # 知识库正在被机器人使用，不允许删除
                raise APIException(ErrorCode.VALIDATION_ERROR, msg="该知识库已被机器人使用，无法删除")
            
            # 先获取知识库信息
            kb = KnowledgeBaseDAO().find_by_id(kb_id)
            if not kb:
                raise FileNotFoundError("知识库不存在")
            
            # 获取知识库中的所有文档
            documents = DocumentDAO().find_by_kb_id(kb_id)
            
            # 删除MinIO中的文件
            for doc in documents:
                if doc["minio_path"]:
                    self.minio_client.delete_file(doc["minio_path"])
            
            # 删除知识库（会级联删除文档和文档块）
            KnowledgeBaseDAO().delete(kb_id)
            
            return True
        except FileNotFoundError:
            raise
        except Exception as e:
            log_.error(f"删除知识库失败: {str(e)}")
            raise APIException(ErrorCode.SYSTEM_ERROR, msg=f"删除知识库失败: {str(e)}")
    
    def add_file_to_knowledge_base(self, kb_id, file):
        """向知识库添加文件，但不进行向量化处理"""
        temp_file_path = None
        try:
            # 限制文件大小（例如：最大100MB）
            max_file_size = 100 * 1024 * 1024  # 100MB
            if hasattr(file, 'content_length') and file.content_length > max_file_size:
                log_.error(f"文件过大: {file.content_length} 字节，超过限制: {max_file_size} 字节")
                raise APIException(ErrorCode.VALIDATION_ERROR, msg="文件过大，最大允许100MB")
            
            # 检查是否为有效文件对象
            if not hasattr(file, 'save') or not callable(file.save):
                log_.error("无效的文件对象")
                raise APIException(ErrorCode.VALIDATION_ERROR, msg="无效的文件对象")
                
            # 检查MinIO连接
            try:
                # 检查MinIO客户端是否初始化
                if not self.minio_client:
                    log_.error("MinIO客户端未初始化")
                    raise APIException(ErrorCode.SYSTEM_ERROR, msg="存储服务未正确配置，请联系管理员")
                
                # 检查客户端对象是否存在
                if not self.minio_client.client:
                    log_.error("MinIO客户端对象为空")
                    
                    # 尝试重新初始化MinIO客户端
                    from common.minio_client import MinioClient
                    self.minio_client = MinioClient()
                    
                    # 再次检查客户端是否初始化成功
                    if not self.minio_client or not self.minio_client.client:
                        log_.error("MinIO客户端重新初始化失败")
                        raise APIException(ErrorCode.SYSTEM_ERROR, msg="存储服务无法连接，请稍后再试")
                    
                # 检查默认桶是否存在，使用带重试的方法
                max_retries = 3
                retry_delay = 1  # 初始延迟1秒
                
                for attempt in range(max_retries):
                    try:
                        if not self.minio_client.client.bucket_exists(self.minio_client.default_bucket):
                            log_.warning(f"MinIO默认桶不存在: {self.minio_client.default_bucket}，尝试创建")
                            self.minio_client.client.make_bucket(self.minio_client.default_bucket)
                        else:
                            log_.debug(f"MinIO默认桶存在: {self.minio_client.default_bucket}")
                        
                        # 桶检查成功，跳出循环
                        break
                    except Exception as bucket_error:
                        log_.error(f"检查MinIO桶失败 (尝试 {attempt+1}/{max_retries}): {str(bucket_error)}")
                        
                        if attempt < max_retries - 1:
                            import time
                            time.sleep(retry_delay)
                            retry_delay *= 2  # 指数退避
                        else:
                            log_.error("检查MinIO桶失败，已达到最大重试次数")
                            raise APIException(ErrorCode.SYSTEM_ERROR, msg="存储服务暂时不可用，请稍后再试")
            except APIException:
                # 直接重新抛出APIException
                raise
            except Exception as e:
                log_.error(f"MinIO连接检查失败: {str(e)}", exc_info=True)
                raise APIException(ErrorCode.SYSTEM_ERROR, msg="存储服务连接失败，请稍后再试")
            
            # 检查数据库连接
            try:
                with get_db_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT 1")
                        result = cursor.fetchone()
                        if result[0] != 1:
                            log_.error("数据库连接检查失败: 返回值不是1")
                            raise APIException(ErrorCode.SYSTEM_ERROR, msg="数据库服务不可用")
            except Exception as e:
                log_.error(f"数据库连接检查失败: {str(e)}", exc_info=True)
                raise APIException(ErrorCode.SYSTEM_ERROR, msg=f"数据库服务不可用: {str(e)}")
            
            # 检查知识库是否存在
            kb = KnowledgeBaseDAO().find_by_id(kb_id)
            if not kb:
                log_.error(f"知识库不存在，ID: {kb_id}")
                raise FileNotFoundError("知识库不存在")
            
            # 获取知识库名称，并将其转换为安全的文件夹名
            kb_name = secure_filename(kb['name'])
            
            # 检查文件类型
            if not hasattr(file, 'filename') or not file.filename:
                log_.error("文件名不存在")
                raise APIException(ErrorCode.VALIDATION_ERROR, msg="文件名不能为空")
                
            original_filename = file.filename
            safe_filename = secure_filename(original_filename)

            if not self._is_allowed_file(original_filename):
                log_.error(f"不支持的文件类型: {original_filename}")
                raise APIException(ErrorCode.VALIDATION_ERROR, msg="不支持的文件类型")
            
            # 生成唯一的文件名
            file_ext = os.path.splitext(original_filename)[1]
            unique_filename = f"{uuid.uuid4().hex}{file_ext}"
            
            # 准备临时文件路径
            temp_dir = os.path.abspath("./data/temp")
            os.makedirs(temp_dir, exist_ok=True)
            temp_file_path = os.path.join(temp_dir, unique_filename)
            
            # 保存上传的文件到临时目录
            try:
                file.save(temp_file_path)
            except Exception as e:
                log_.error(f"保存文件到临时目录失败: {str(e)}", exc_info=True)
                raise APIException(ErrorCode.FILE_UPLOAD_ERROR, msg=f"保存文件失败: {str(e)}")
            
            # 检查文件是否成功保存
            if not os.path.exists(temp_file_path):
                log_.error(f"临时文件未成功保存: {temp_file_path}")
                raise IOError("保存临时文件失败")
            
            # 获取文件大小
            try:
                file_size = os.path.getsize(temp_file_path)
                
                # 再次检查文件大小
                if file_size > max_file_size:
                    log_.error(f"文件过大: {file_size} 字节，超过限制: {max_file_size} 字节")
                    os.remove(temp_file_path)
                    raise APIException(ErrorCode.VALIDATION_ERROR, msg="文件过大，最大允许100MB")
                
                # 检查文件大小是否为0
                if file_size == 0:
                    log_.error("文件大小为0")
                    os.remove(temp_file_path)
                    raise APIException(ErrorCode.VALIDATION_ERROR, msg="文件为空")
            except Exception as e:
                if not isinstance(e, APIException):
                    log_.error(f"获取文件大小失败: {str(e)}", exc_info=True)
                    raise APIException(ErrorCode.FILE_UPLOAD_ERROR, msg=f"获取文件大小失败: {str(e)}")
                raise
            
            # 上传到MinIO - 使用知识库名称作为文件夹
            minio_path = f"{kb_name}/{unique_filename}"
            
            try:
                self.minio_client.upload_file(
                    file_path=temp_file_path,
                    object_name=minio_path
                )
                
                # 验证文件是否成功上传
                try:
                    self.minio_client.client.stat_object(self.minio_client.default_bucket, minio_path)
                except Exception as e:
                    log_.error(f"文件上传验证失败: {str(e)}", exc_info=True)
                    raise Exception(f"文件上传到MinIO后无法验证: {str(e)}")
            except Exception as e:
                log_.error(f"上传到MinIO失败: {str(e)}", exc_info=True)
                raise APIException(ErrorCode.FILE_UPLOAD_ERROR, msg=f"上传到MinIO失败: {str(e)}")
            
            # 创建文档记录，状态设为 "uploaded"（已上传但未处理）
            try:
                from app.entity.knowledge_base import Document
                from app.dao.kb_document_dao import KBDocumentDAO
                
                # 创建文档对象（不再包含kb_id）
                doc_entity = Document(
                    name=original_filename,
                    minio_path=minio_path,
                    file_type=file_ext.lstrip('.'),
                    file_size=file_size,
                    status="uploaded"  # 新状态：已上传但未向量化
                )
                document = DocumentDAO().create(doc_entity)
                
                # 创建知识库-文档关联
                kb_doc_dao = KBDocumentDAO()
                if not kb_doc_dao.add_document_to_kb(kb_id, document['id']):
                    log_.error(f"创建文档与知识库关联失败")
                    raise Exception("创建文档与知识库关联失败")
                
                # 验证文档记录是否成功创建
                doc_check = DocumentDAO().find_by_id(document['id'])
                if not doc_check:
                    log_.error(f"文档记录创建后无法验证: {document['id']}")
                    raise Exception("文档记录创建后无法验证")
            except Exception as e:
                log_.error(f"创建文档记录失败: {str(e)}", exc_info=True)
                # 如果数据库操作失败，尝试删除已上传的文件
                try:
                    self.minio_client.delete_file(minio_path)
                except Exception as delete_error:
                    log_.warning(f"删除MinIO中的文件失败: {minio_path}, 错误: {str(delete_error)}")
                
                if isinstance(e, APIException):
                    raise
                else:
                    raise APIException(ErrorCode.DATABASE_ERROR, msg=f"创建文档记录失败: {str(e)}")
            
            # 清理临时文件
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except Exception as e:
                    log_.warning(f"删除临时文件失败: {str(e)}")
            
            # 添加预签名URL
            try:
                document["url"] = self.minio_client.get_presigned_url(minio_path)
            except Exception as e:
                log_.warning(f"生成预签名URL失败: {str(e)}")
                document["url"] = f"{self.minio_client.default_bucket}/{minio_path}"
            
            return document
        except Exception as e:
            log_.error(f"上传文件过程中发生异常: {str(e)}", exc_info=True)
            # 清理临时文件
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except Exception as clean_error:
                    log_.warning(f"删除临时文件失败: {str(clean_error)}")
            
            # 重新抛出异常
            if isinstance(e, (FileNotFoundError, APIException)):
                raise
            
            log_.error(f"添加文件到知识库失败: {str(e)}", exc_info=True)
            raise APIException(ErrorCode.SYSTEM_ERROR, msg=f"添加文件到知识库失败: {str(e)}")
    
    def process_document(self, document_id):
        """处理已上传的文档，进行向量化"""
        try:
            # 获取文档信息
            document = DocumentDAO().find_by_id(document_id)
            if not document:
                raise FileNotFoundError("文档不存在")
            
            # 检查文档状态
            if document["status"] not in ["uploaded", "failed"]:
                if document["status"] == "completed":
                    return {"message": "文档已完成处理", "document_id": document_id}
                elif document["status"] == "processing":
                    return {"message": "文档正在处理中", "document_id": document_id}
                else:
                    return {"message": f"文档状态不允许处理: {document['status']}", "document_id": document_id}
            
            # 更新文档状态为处理中
            DocumentDAO().update_status(document_id, "processing")
            
            # 异步处理文档（在生产环境中应该使用celery或其他异步任务队列）
            import threading
            
            # 获取当前Flask应用实例
            try:
                from flask import current_app
                # 确保获取实际的应用实例，而不是代理对象
                if hasattr(current_app, '_get_current_object'):
                    app_instance = current_app._get_current_object()
                    thread = threading.Thread(target=self._process_document_thread, args=(document_id, app_instance))
                else:
                    log_.warning("无法获取Flask应用实例的_get_current_object方法")
                    thread = threading.Thread(target=self._process_document_thread, args=(document_id, None))
            except Exception as e:
                log_.error(f"获取Flask应用实例失败: {str(e)}")
                thread = threading.Thread(target=self._process_document_thread, args=(document_id, None))
                
            thread.daemon = True
            thread.start()
            
            return {"message": "文档处理请求已发送", "document_id": document_id}
        except FileNotFoundError:
            raise
        except Exception as e:
            log_.error(f"处理文档失败: {str(e)}")
            raise APIException(ErrorCode.SYSTEM_ERROR, msg=f"处理文档失败: {str(e)}")
            
    def _process_document_thread(self, document_id, app_instance=None):
        """在后台线程中处理文档"""
        temp_file_path = None
        app_context = None
        
        try:
            # 首先推送应用上下文，确保在任何操作之前完成
            if app_instance:
                try:
                    # 检查是否已经有活动的应用上下文
                    from flask import has_app_context
                    if not has_app_context():
                        app_context = app_instance.app_context()
                        app_context.push()
                    else:
                        log_.debug("线程中已存在活动的Flask应用上下文，无需创建新上下文")
                except ImportError:
                    # 如果无法导入has_app_context，则尝试直接创建上下文
                    app_context = app_instance.app_context()
                    app_context.push()
                except Exception as e:
                    log_.warning(f"创建Flask应用上下文时出错: {str(e)}，将尝试继续处理")
            else:
                log_.warning("未提供应用实例，将不使用Flask应用上下文")
                
            # 后续所有操作都在应用上下文中执行
            
            # 获取文档信息
            document = DocumentDAO().find_by_id(document_id)
            if not document:
                log_.error(f"文档不存在: {document_id}")
                return
            
            # 检查PostgreSQL向量扩展
            try:
                with get_db_connection() as conn:
                    with conn.cursor() as cursor:
                        # 检查pgvector扩展是否已安装
                        cursor.execute("SELECT COUNT(*) FROM pg_extension WHERE extname = 'vector'")
                        result = cursor.fetchone()[0]
                        if result == 0:
                            log_.error("PostgreSQL中未安装pgvector扩展，无法处理文档向量")
                            DocumentDAO().update_status(document_id, "failed")
                            return

                        # 检查向量列的维度
                        try:
                            cursor.execute("SELECT typmod FROM pg_attribute WHERE attrelid = 'dodo_document_chunks'::regclass AND attname = 'embedding'")
                            result = cursor.fetchone()
                            if result:
                                vector_dim = result[0] - 4  # pgvector存储方式：维度+4

                                # 确保向量维度为1536，这是表结构定义的维度
                                if vector_dim != 1536:
                                    log_.warning(f"检测到的向量维度 {vector_dim} 与表定义的1536不匹配，将使用1536")
                                    vector_dim = 1536
                            else:
                                vector_dim = 1536
                        except Exception as e:
                            log_.warning(f"获取向量维度失败，将使用默认值1536: {str(e)}")
                            vector_dim = 1536
            except Exception as e:
                log_.error(f"检查数据库向量支持失败: {str(e)}", exc_info=True)
                DocumentDAO().update_status(document_id, "failed")
                return
                
            # 检查文件大小，限制大文件处理
            max_process_size = 50 * 1024 * 1024  # 50MB
            if document["file_size"] > max_process_size:
                log_.warning(f"文件过大，可能需要更多资源: {document['file_size']} 字节")
            
            # 下载文件到临时目录
            temp_dir = os.path.abspath("./data/temp")
            os.makedirs(temp_dir, exist_ok=True)
            
            # 生成唯一的临时文件路径
            temp_file_name = f"process_{uuid.uuid4().hex}{os.path.splitext(document['name'])[1]}"
            temp_file_path = os.path.join(temp_dir, temp_file_name)
            
            try:
                self.minio_client.download_file(
                    object_name=document["minio_path"],
                    file_path=temp_file_path
                )
            except Exception as e:
                log_.error(f"从MinIO下载文件失败: {str(e)}", exc_info=True)
                DocumentDAO().update_status(document_id, "failed")
                return
            
            # 加载文档
            try:
                doc = load_document(temp_file_path)
            except Exception as e:
                log_.error(f"加载文档失败: {str(e)}", exc_info=True)
                DocumentDAO().update_status(document_id, "failed")
                return
            
            # 分割文档
            try:
                chunks = split_document(doc)

                # 限制分块数量，防止资源过度占用
                max_chunks = 1000
                if len(chunks) > max_chunks:
                    log_.warning(f"分块数量过多: {len(chunks)}，已限制为 {max_chunks}")
                    chunks = chunks[:max_chunks]
            except Exception as e:
                log_.error(f"分割文档失败: {str(e)}", exc_info=True)
                DocumentDAO().update_status(document_id, "failed")
                return
            
            # 计算嵌入并存储
            chunk_objects = []
            
            # 批处理嵌入，每次处理一部分分块，避免内存占用过高
            batch_size = 50
            for i in range(0, len(chunks), batch_size):
                batch_chunks = chunks[i:i+batch_size]

                batch_objects = []
                for j, chunk in enumerate(batch_chunks):
                    chunk_index = i + j
                    
                    try:
                        # 确保embeddings_model能在上下文外工作
                        if not hasattr(self, '_embeddings_model') or self._embeddings_model is None:
                            # 如果有应用实例，尝试从中获取嵌入模型
                            if app_instance and hasattr(app_instance, 'embeddings_model'):
                                self._embeddings_model = app_instance.embeddings_model
                            else:
                                # 否则创建新的嵌入模型
                                from app.models.embeddings.base import get_embeddings_model
                                self._embeddings_model = get_embeddings_model()

                        # 生成嵌入向量
                        embedding = self.embeddings_model.embed_query(chunk.page_content)

                        # 确保向量是Python列表
                        if not isinstance(embedding, list):
                            embedding = embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)

                        # 确保向量维度为1536
                        if len(embedding) != 1536:
                            log_.warning(f"嵌入向量维度 {len(embedding)} 与数据库表维度可能不匹配")
                            # 不再尝试调整向量维度，直接使用模型生成的向量
                
                        # 创建分块对象
                        chunk_obj = DocumentChunk(
                            document_id=document_id,
                            content=chunk.page_content,
                            embedding=embedding,
                            chunk_index=chunk_index
                        )
                
                        batch_objects.append(chunk_obj)
                    except Exception as e:
                        log_.error(f"处理第 {chunk_index} 个分块失败: {str(e)}", exc_info=True)
                
                # 批量保存当前批次的分块
                if batch_objects:
                    try:
                        # 尝试批量保存
                        DocumentChunkDAO().bulk_create(batch_objects)
                        chunk_objects.extend(batch_objects)
                    except Exception as e:
                        log_.error(f"批量保存分块失败: {str(e)}", exc_info=True)
                        # 尝试逐个保存以隔离问题
                        successful_chunks = []
                        for idx, chunk_obj in enumerate(batch_objects):
                            try:
                                # 不再检查向量维度，直接尝试保存
                                """
                                if len(chunk_obj.embedding) != 1536:
                                    log_.warning(f"分块 {idx} 的向量维度 {len(chunk_obj.embedding)} 与表定义的1536不匹配，跳过")
                                    continue
                                """
                                
                                # 使用DAO单独保存
                                chunk_dict = DocumentChunkDAO().create_single(chunk_obj)
                                if chunk_dict:
                                    successful_chunks.append(chunk_obj)
                            except Exception as single_error:
                                log_.error(f"保存单个分块 {idx} 失败: {str(single_error)}")
                        
                        if successful_chunks:
                            chunk_objects.extend(successful_chunks)
                
            # 更新文档状态
            if chunk_objects:
                # 如果有成功处理的分块，标记为完成
                DocumentDAO().update_status(document_id, "completed")
            else:
                # 如果没有成功处理的分块，标记为失败
                DocumentDAO().update_status(document_id, "failed")
                log_.error("未能生成任何分块，处理失败")
            
            # 清理临时文件
            try:
                if temp_file_path and os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
            except Exception as e:
                log_.warning(f"删除临时文件失败: {str(e)}")
            
            # 释放内存
            chunks = None
            chunk_objects = None
            import gc
            gc.collect()
        except Exception as e:
            log_.error(f"处理文档异常: {str(e)}", exc_info=True)
            try:
                # 更新文档状态为失败
                DocumentDAO().update_status(document_id, "failed")
                
                # 清理临时文件
                if temp_file_path and os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
            except Exception as clean_error:
                log_.warning(f"清理资源失败: {str(clean_error)}")
            
            # 释放内存
            import gc
            gc.collect()
        finally:
            # 如果创建了应用上下文，在处理结束后弹出
            if app_context:
                try:
                    app_context.pop()
                except Exception as ctx_error:
                    log_.warning(f"释放应用上下文失败: {str(ctx_error)}")
                    
            # 确保临时文件被清理
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except Exception as e:
                    log_.warning(f"清理临时文件失败: {str(e)}")
    
    def delete_document(self, document_id):
        """删除文档"""
        try:
            # 获取文档信息
            document = DocumentDAO().find_by_id(document_id)
            if not document:
                raise FileNotFoundError("文档不存在")
            
            # 删除MinIO中的文件
            if document["minio_path"]:
                self.minio_client.delete_file(document["minio_path"])
            
            # 删除文档记录（会级联删除文档块）
            DocumentDAO().delete(document_id)
            
            return True
        except FileNotFoundError:
            raise
        except Exception as e:
            log_.error(f"删除文档失败: {str(e)}")
            raise APIException(ErrorCode.SYSTEM_ERROR, msg=f"删除文档失败: {str(e)}")
    
    def get_presigned_url_cached(self, minio_path):
        """获取带缓存的预签名URL"""
        current_time = time.time()
        
        # 检查缓存中是否有未过期的URL
        if minio_path in self._presigned_url_cache and self._cache_expiry.get(minio_path, 0) > current_time:
            return self._presigned_url_cache[minio_path]
        
        # 生成新的预签名URL
        url = self.minio_client.get_presigned_url(minio_path)
        
        # 缓存URL，设置15分钟过期
        self._presigned_url_cache[minio_path] = url
        self._cache_expiry[minio_path] = current_time + 15 * 60
        
        return url

    def get_documents(self, kb_id=None):
        """获取文档列表"""
        try:
            if kb_id:
                documents = DocumentDAO().find_by_kb_id(kb_id)
            else:
                # 获取所有文档（实际项目中应该分页）
                documents = []
                log_.warning("获取所有文档的功能暂未实现")
            
            # 为每个文档添加预签名URL
            for doc in documents:
                if doc["minio_path"]:
                    try:
                        doc["url"] = self.get_presigned_url_cached(doc["minio_path"])
                    except Exception as e:
                        log_.error(f"为文档 {doc['id']} 生成预签名URL失败: {str(e)}")
                        # 使用静态URL作为回退
                        doc["url"] = f"{self.minio_client.client._endpoint_url}/{self.minio_client.default_bucket}/{doc['minio_path']}"
            
            return documents
        except Exception as e:
            log_.error(f"获取文档列表失败: {str(e)}")
            # 返回空列表而不是抛出异常，避免整个服务崩溃
            return []
    
    def search_similar_chunks(self, query, limit=5):
        """搜索相似的文档块"""
        try:
            # 获取查询的嵌入向量
            embedding = self.embeddings_model.embed_query(query)
            
            # 搜索相似文档块
            similar_chunks = DocumentChunkDAO().search_similar(embedding, limit)
            
            return similar_chunks
        except Exception as e:
            log_.error(f"搜索相似文档块失败: {str(e)}")
            raise APIException(ErrorCode.SYSTEM_ERROR, msg=f"搜索相似文档块失败: {str(e)}")
    
    def get_document(self, document_id):
        """获取单个文档详情"""
        try:
            document = DocumentDAO().find_by_id(document_id)
            if not document:
                raise FileNotFoundError("文档不存在")
            
            # 添加预签名URL
            if document["minio_path"]:
                try:
                    document["url"] = self.minio_client.get_presigned_url(document["minio_path"])
                except Exception as e:
                    log_.error(f"为文档 {document_id} 生成预签名URL失败: {str(e)}")
                    # 使用静态URL作为回退
                    document["url"] = f"{self.minio_client.client._endpoint_url}/{self.minio_client.default_bucket}/{document['minio_path']}"
            
            return document
        except FileNotFoundError:
            raise
        except Exception as e:
            log_.error(f"获取文档详情失败: {str(e)}")
            raise APIException(ErrorCode.SYSTEM_ERROR, msg=f"获取文档详情失败: {str(e)}")

    def is_knowledge_base_used_by_bot(self, kb_id):
        """检查知识库是否被机器人使用"""
        try:
            from common.db_utils import get_db_connection
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT bot_id FROM dodo_bot_knowledge_bases
                        WHERE kb_id = %s
                        LIMIT 1
                    """, (kb_id,))
                    result = cursor.fetchone()
                    
                return result is not None
        except Exception as e:
            log_.error(f"检查知识库使用状态失败: {str(e)}")
            # 如果查询失败，为安全起见返回True，阻止删除
            return True

    def get_knowledge_bases_with_count(self, user_id=None):
        """获取知识库基本信息列表和文件计数（不包含文档内容）"""
        try:
            if user_id:
                kb_list = KnowledgeBaseDAO().find_by_user_id(user_id, include_public=True)
            else:
                kb_list = KnowledgeBaseDAO().find_public_only()
            
            # 为每个知识库添加文件计数
            for kb in kb_list:
                kb_id = kb["id"]
                # 获取知识库中的文档数量
                doc_count = DocumentDAO().count_by_kb_id(kb_id)
                kb["doc_count"] = doc_count
            
            return kb_list
        except Exception as e:
            log_.error(f"获取知识库列表失败: {str(e)}")
            raise APIException(ErrorCode.SYSTEM_ERROR, msg=f"获取知识库列表失败: {str(e)}")