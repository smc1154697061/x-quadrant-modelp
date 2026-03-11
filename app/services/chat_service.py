from app.models.llm.model_factory import get_llm_model
from app.models.embeddings.modelfactory import EmbeddingModelFactory
from app.models.vector_store.povector_store import PVectorStore
from app.services.knowledge_service import KnowledgeService
from app.services.extraction_service import ExtractionService
from app.services.prompt_service import PromptService
from app.dao.bot_dao import BotDAO
from app.dao.conversation_dao import ConversationDAO
from app.dao.message_dao import MessageDAO
from app.dao.message_document_dao import MessageDocumentDAO
from app.dao.knowledge_dao import DocumentDAO
from app.entity.knowledge_base import Document
from common.minio_client import MinioClient
from common import log_
import os
import threading
import traceback

class ChatService:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ChatService, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        # 优先从Flask g对象获取
        try:
            from flask import g
            if hasattr(g, 'embedding_model'):
                self.embeddings = g.embedding_model
            if hasattr(g, 'llm_model'):
                self.llm_model = g.llm_model
            if hasattr(g, 'vector_store'):
                self.vector_store = g.vector_store
        except:
            pass
        
        # 如果g对象中没有，则从应用上下文获取
        try:
            from flask import current_app
            if not hasattr(self, 'embeddings') and hasattr(current_app, 'embedding_model'):
                self.embeddings = current_app.embedding_model
            if not hasattr(self, 'llm_model') and hasattr(current_app, 'llm_model'):
                self.llm_model = current_app.llm_model
            if not hasattr(self, 'vector_store') and hasattr(current_app, 'vector_store'):
                self.vector_store = current_app.vector_store
        except:
            pass
        
        # 如果仍然没有，则创建新的实例
        if not hasattr(self, 'embeddings'):
            self.embeddings = EmbeddingModelFactory.get_embeddings()
        if not hasattr(self, 'llm_model'):
            self.llm_model = get_llm_model()
        if not hasattr(self, 'vector_store'):
            self.vector_store = PVectorStore()
        
        # 初始化其他服务和DAO
        self.knowledge_service = KnowledgeService()
        self.extraction_service = ExtractionService()
        self.bot_dao = BotDAO()
        self.conversation_dao = ConversationDAO()
        self.message_dao = MessageDAO()
        self.message_document_dao = MessageDocumentDAO()
        self.document_dao = DocumentDAO()
        self.minio_client = MinioClient()
        
        # 默认设置
        self.search_k = 5  # 检索结果数量
        self.max_history_messages = 10  # 最大历史消息数量
        
        # 当前使用的知识库ID列表
        self.current_kb_ids = []
        
        # 当前机器人ID
        self.current_bot_id = None
        
        # 当前对话ID  
        self.current_conversation_id = None
        
        # 当前角色标识（用于提示词模板）
        self.current_role_key = None
        
        # 自定义系统提示词（优先级高于角色模板）
        self.custom_system_prompt = None
        
        self._initialized = True
        self.max_history_messages = 10  # 默认历史消息数量限制
        
        self._initialized = True
    
    # 重置会话上下文
    def reset_context(self):
        """重置会话上下文，用于每次请求开始前"""
        self.current_kb_ids = []
        self.current_bot_id = None
        self.current_conversation_id = None
        self.current_user_id = None
        self.current_role_key = None
        self.custom_system_prompt = None
    
    def set_user_context(self, user_id):
        """设置用户上下文"""
        if user_id:
            self.current_user_id = user_id
            
    def set_system_prompt(self, system_prompt):
        """设置自定义系统提示词（优先级最高）"""
        self.custom_system_prompt = system_prompt
    
    def set_role(self, role_key):
        """设置角色标识（writer, english_expert等）"""
        self.current_role_key = role_key

    def load_bot_by_id(self, bot_id, user_id=None):
        """加载机器人配置"""
        try:
            # 获取机器人信息
            bot = self.bot_dao.get_bot(bot_id)
            if not bot:
                log_.error(f"机器人不存在: {bot_id}")
                return False
            
            # 设置当前机器人ID
            self.current_bot_id = bot_id
            
            # 检查权限（私有机器人只有创建者可访问）
            if not bot['is_public'] and bot['created_by'] != user_id:
                log_.warning(f"无权访问私有机器人: {bot_id}, 用户: {user_id}")
                return False
            
            # 获取关联的知识库
            kb_ids = bot.get('kb_ids', [])
            
            # 创建或获取对话
            if user_id and bot_id:
                conversation = self.conversation_dao.find_or_create_conversation(
                    user_id=user_id,
                    bot_id=bot_id
                )
                if conversation:
                    self.current_conversation_id = conversation['id']
            
            # 清空当前知识库ID列表
            self.current_kb_ids = []
            
            # 加载机器人关联的所有知识库
            for kb_id in kb_ids:
                self.load_knowledge_base_by_id(kb_id)
            
            return True
        except Exception as e:
            log_.error(f"加载机器人失败: {str(e)}")
            return False
    
    def load_knowledge_base_by_id(self, kb_id):
        """加载知识库"""
        try:
            # 获取知识库信息
            kb = self.knowledge_service.get_knowledge_base(kb_id)
            if not kb:
                log_.warning(f"知识库不存在: {kb_id}")
                return False
            
            # 检查知识库是否有向量化的文档块
            try:
                from common.db_utils import get_db_connection
                with get_db_connection() as conn:
                    with conn.cursor() as cursor:
                        # 通过document_chunks、documents和kb_documents关联表查询是否有此知识库的文档块
                        cursor.execute("""
                            SELECT COUNT(*) 
                            FROM dodo_document_chunks dc
                            JOIN dodo_documents d ON dc.document_id = d.id
                            JOIN dodo_kb_documents kd ON d.id = kd.document_id
                            WHERE kd.kb_id = %s
                        """, (kb_id,))
                        
                        count = cursor.fetchone()[0]
                        
                        if count > 0:
                            if kb_id not in self.current_kb_ids:
                                self.current_kb_ids.append(kb_id)
                            return True
                        else:
                            log_.warning(f"知识库 {kb_id} 没有可用的向量化文档块")
                            return False
            except Exception as e:
                log_.warning(f"检查知识库文档块失败: {str(e)}")
                return False
        except Exception as e:
            log_.error(f"加载知识库失败: {str(e)}")
            return False
    
    def load_knowledge_base(self, txt_path):
        """
        兼容旧版API: 从txt文件加载知识库
        注: 这个方法现在会创建临时知识库并保存到知识库系统中
        """
        try:
            if not os.path.exists(txt_path):
                log_.error(f"文件不存在: {txt_path}")
                return False
                
            file_name = os.path.basename(txt_path)
            kb_name = f"从{file_name}创建的知识库"
            
            result = self.knowledge_service.import_data_files(kb_name)
            if result and result.get("success"):
                kb_id = result["knowledge_base"]["id"]
                return self.load_knowledge_base_by_id(kb_id)
            else:
                log_.error("创建临时知识库失败")
                return False
        except Exception as e:
            log_.error(f"加载知识库失败: {str(e)}")
            return False
    
    def get_chat_response(self, question, conversation_id=None):
        """
        获取聊天回答，使用RAG（检索增强生成）流程
        
        Args:
            question: 用户问题
            conversation_id: 会话ID
            
        Returns:
            str: 回答内容
        """
        try:
            # 设置当前会话ID
            self.current_conversation_id = conversation_id
            
            # 获取角色提示词
            role_prompt = PromptService.get_role_prompt(
                role_key=self.current_role_key,
                custom_prompt=self.custom_system_prompt
            )
            
            # 获取历史对话上下文（无论是否有知识库都需要）
            history_context = ""
            if self.current_conversation_id:
                try:
                    history_messages = self.message_dao.get_recent_messages(
                        conversation_id=self.current_conversation_id,
                        limit=self.max_history_messages
                    )
                    
                    if history_messages:
                        history_context = PromptService.build_history_context(
                            history_messages,
                            max_pairs=5
                        )
                except Exception as e:
                    log_.error(f"获取历史消息失败: {str(e)}")
                    log_.error(traceback.format_exc())
            
            # 如果没有关联知识库，使用直接回答模式（但会带上历史对话）
            if not self.current_kb_ids:
                log_.warning("没有选择知识库，使用直接回答模式")
                answer = self.get_direct_response(question, role_prompt, history_context)
                
                return answer
            
            # 从所有关联的知识库中检索相关文档
            all_results = []
            for kb_id in self.current_kb_ids:
                try:
                    # 不要使用kb_7这样的表名，而是使用document_chunks表并按kb_id筛选
                    # 这里假设vector_store.similarity_search_by_kb_id方法存在
                    # 如果不存在，需要修改PVectorStore类添加此方法
                    results = self.vector_store.similarity_search_by_kb_id(
                        query=question,
                        kb_id=kb_id,
                        k=self.search_k
                    )
                    
                    if results and len(results) > 0:
                        all_results.extend(results)
                except Exception as e:
                    log_.warning(f"从知识库 {kb_id} 检索失败: {str(e)}")
            
            # 如果没有找到相关文档，使用直接回答模式（但会带上历史对话）
            if not all_results:
                log_.warning("向量检索未找到相关文档，切换到直接回答模式")
                answer = self.get_direct_response(question, role_prompt, history_context)
                
                return answer
            
            # 对结果按相似度排序并取前K个
            all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
            top_results = all_results[:self.search_k]
            
            # 构建知识库上下文
            knowledge_context = PromptService.build_knowledge_context(top_results)
            
            # 构建完整提示词（RAG模式）
            prompt = PromptService.build_rag_prompt(
                role_prompt=role_prompt,
                history_context=history_context,
                knowledge_context=knowledge_context,
                file_context="",  # 文件内容已经在question中了
                question=question
            )
            
            # 调用模型生成回答
            log_.debug(f"=== 发送给AI的完整Prompt ===\n{prompt}\n=== Prompt结束 ===")
            answer = self.llm_model.invoke(prompt)
            return answer
                
        except Exception as e:
            log_.error(f"知识库聊天处理失败: {str(e)}")
            log_.error(traceback.format_exc())
            # 异常时也尝试带上历史对话
            role_prompt = PromptService.get_role_prompt()
            answer = self.get_direct_response(question, role_prompt, "")
            
            return answer
    
    def get_direct_response(self, question, role_prompt, history_context=""):
        """直接调用模型获取回答，不使用知识库但支持历史对话
        
        Args:
            question: 用户问题
            role_prompt: 角色提示词
            history_context: 历史对话上下文（可选）
        """
        try:
            # 构建提示词：使用PromptService统一构建
            prompt = PromptService.build_direct_prompt(
                role_prompt=role_prompt,
                history_context=history_context,
                file_context="",  # 文件内容已经在question中了
                question=question
            )
            
            log_.debug(f"=== 发送给AI的完整Prompt(直接回答模式) ===\n{prompt}\n=== Prompt结束 ===")
            response = self.llm_model.invoke(prompt)
            return response
        except Exception as e:
            log_.error(f"直接回答处理失败: {str(e)}")
            log_.error(traceback.format_exc())
            return f"抱歉，我无法理解您的问题。错误信息: {str(e)}"
            
    def get_conversation_history(self, conversation_id, limit=50):
        """获取对话历史记录"""
        try:
            if not conversation_id:
                log_.warning("未提供对话ID，无法获取对话历史")
                return []
                
            messages = self.message_dao.get_messages(conversation_id, limit)
            return messages
        except Exception as e:
            log_.error(f"获取对话历史失败: {str(e)}")
            log_.error(traceback.format_exc())
            return []
    
    def get_user_conversations(self, user_id, bot_id=None, limit=20):
        """获取用户的所有对话
        
        Args:
            user_id: 用户ID
            bot_id: 机器人ID，如果提供则只返回该机器人的对话
            limit: 返回的最大对话数量
            
        Returns:
            list: 对话列表
        """
        try:
            return self.conversation_dao.get_user_conversations(user_id, bot_id=bot_id, limit=limit)
        except Exception as e:
            log_.error(f"获取用户对话列表失败: {str(e)}")
            log_.error(traceback.format_exc())
            return []
    
    def upload_message_file(self, file, user_id, bot_name=None, original_filename=None):
        """上传对话中的文件
        
        Args:
            file: 文件对象 (Flask request.files)
            user_id: 用户ID
            
        Returns:
            dict: 包含document_id、filename、file_content等信息
        """
        try:
            import mimetypes, os, re, uuid
            
            # 获取原始文件名（优先使用前端传来的 original_filename）
            raw_name = original_filename or getattr(file, 'filename', None) or 'uploaded_file'
            
            # 自定义安全文件名处理：保留中文和Unicode字符，只移除特殊符号
            def safe_filename_unicode(filename):
                """保留中文等Unicode字符的安全文件名处理"""
                # 分离文件名和扩展名
                name, ext = os.path.splitext(filename)
                # 移除不安全的路径字符，但保留中文、字母、数字、下划线、连字符
                name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', name)
                # 去除首尾空格
                name = name.strip()
                # 如果文件名为空，使用UUID
                if not name:
                    name = str(uuid.uuid4())[:8]
                return name + ext
            
            filename = safe_filename_unicode(raw_name)
            
            # 读取文件内容
            file_content_bytes = file.read()
            file_size = len(file_content_bytes)
            
            # 先根据文件名推断类型
            _, ext = os.path.splitext(filename)
            file_type = ext[1:].lower() if ext else 'unknown'

            # 再结合mimetype兜底修正（解决没有扩展名时始终是 unknown 的问题）
            content_type = getattr(file, 'mimetype', None) or mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            if file_type == 'unknown' and content_type:
                if content_type.startswith('text/'):
                    file_type = 'txt'
                    # 确保文件名带上 .txt 方便后续展示
                    if not ext:
                        filename = f"{filename}.txt"
            
            # 解析文件内容（提取文本）
            try:
                # 使用ExtractionService提取文件内容
                # 重置文件指针到开头
                file.seek(0)
                file_content_text = self.extraction_service.extract_file_content(file, file_type)
                # 输出前100个字符用于调试
                if len(file_content_text) > 0:
                    full_log = str(os.getenv('LOG_FULL_FILE_CONTENT', '')).strip().lower() in ('1', 'true', 'yes', 'on')
                    preview_chars = int(os.getenv('LOG_FILE_CONTENT_PREVIEW_CHARS', '100') or '100')
                    if full_log:
                        chunk_size = int(os.getenv('LOG_FILE_CONTENT_CHUNK_SIZE', '1000') or '1000')
                        max_chars = int(os.getenv('LOG_FILE_CONTENT_MAX_CHARS', '0') or '0')
                        text_to_log = file_content_text
                        if max_chars > 0:
                            text_to_log = text_to_log[:max_chars]
                        total_len = len(text_to_log)
                        if total_len == 0:
                            log_.debug(f"文件内容为空: {filename}")
                        else:
                            total_chunks = (total_len + chunk_size - 1) // chunk_size
                            for idx in range(total_chunks):
                                start = idx * chunk_size
                                end = min(start + chunk_size, total_len)
                                chunk = text_to_log[start:end].replace('\n', '\\n')
                                log_.debug(f"文件内容[{filename}]({idx+1}/{total_chunks})[{start}:{end}]: {chunk}")
                            if max_chars > 0 and len(file_content_text) > max_chars:
                                log_.debug(f"文件内容[{filename}]已截断输出，原始长度={len(file_content_text)}, 输出长度={max_chars}")
                    else:
                        preview = file_content_text[:preview_chars].replace('\n', '\\n')
                        log_.debug(f"文件内容预览: {preview}...")
                else:
                    log_.warning(f"文件内容为空: {filename}")
            except Exception as e:
                log_.error(f"文件内容提取失败: {filename}, 错误: {str(e)}")
                import traceback
                log_.error(f"提取错误详情: {traceback.format_exc()}")
                # 对于图片文件，使用占位符
                if file_type.lower() in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'tiff', 'ico']:
                    file_content_text = "[图片文件]"
                else:
                    file_content_text = ""
            
            # 上传到MinIO（使用 upload_bytes），按机器人名称分目录，便于管理
            # 为MinIO对象名添加时间戳，避免重名覆盖
            import time
            timestamp = int(time.time())
            base_name, ext = os.path.splitext(filename)
            unique_filename = f"{base_name}_{timestamp}{ext}"
            
            safe_bot_name = None
            if bot_name:
                try:
                    # 对机器人名称也使用Unicode安全处理
                    safe_bot_name = safe_filename_unicode(str(bot_name))
                except Exception:
                    safe_bot_name = None
            folder = safe_bot_name or f"user_{user_id}"
            minio_object_name = f"chat_files/{folder}/{unique_filename}"
            minio_url = self.minio_client.upload_bytes(
                data=file_content_bytes,
                object_name=minio_object_name,
                content_type=content_type
            )
            minio_path = minio_object_name  # 保存对象名称而非完整URL
            
            # 创建Document记录（使用知识库统一的文档实体/DAO）
            doc_entity = Document(
                name=filename,
                minio_path=minio_path,
                file_type=file_type,
                file_size=file_size,
                status="uploaded"
            )
            document = DocumentDAO().create(doc_entity)
            document_id = document["id"]
            
            return {
                'document_id': document_id,
                'filename': filename,
                'file_type': file_type,
                'file_size': file_size,
                'minio_path': minio_path,
                'file_content_text': file_content_text
            }
        except Exception as e:
            log_.error(f"上传文件失败: {str(e)}")
            log_.error(traceback.format_exc())
            raise
    
    def get_chat_response_with_files(self, question, file_contents=None, conversation_id=None):
        """获取聊天回答（支持文件上传）
        
        Args:
            question: 用户问题文本
            file_contents: 文件内容列表 [{'filename': xx, 'content': xx}, ...]
            conversation_id: 会话ID
            
        Returns:
            str: 回答内容
        """
        try:
            # 构建完整的问题文本（包含文件内容）
            full_question = question or ""
            if file_contents:
                file_texts = []
                for i, file_info in enumerate(file_contents):
                    filename = file_info.get('filename', '未知文件')
                    content = file_info.get('content', '')
                    log_.debug(f"文件 {i+1}: {filename}, 内容长度: {len(content)}")
                    if content and content != "[图片文件]":
                        full_log = str(os.getenv('LOG_FULL_FILE_CONTENT', '')).strip().lower() in ('1', 'true', 'yes', 'on')
                        preview_chars = int(os.getenv('LOG_FILE_CONTENT_PREVIEW_CHARS', '100') or '100')
                        if full_log:
                            chunk_size = int(os.getenv('LOG_FILE_CONTENT_CHUNK_SIZE', '1000') or '1000')
                            max_chars = int(os.getenv('LOG_FILE_CONTENT_MAX_CHARS', '0') or '0')
                            text_to_log = content
                            if max_chars > 0:
                                text_to_log = text_to_log[:max_chars]
                            total_len = len(text_to_log)
                            total_chunks = (total_len + chunk_size - 1) // chunk_size if total_len else 0
                            for idx in range(total_chunks):
                                start = idx * chunk_size
                                end = min(start + chunk_size, total_len)
                                chunk = text_to_log[start:end].replace('\n', '\\n')
                                log_.debug(f"文件内容[{filename}]({idx+1}/{total_chunks})[{start}:{end}]: {chunk}")
                            if max_chars > 0 and len(content) > max_chars:
                                log_.debug(f"文件内容[{filename}]已截断输出，原始长度={len(content)}, 输出长度={max_chars}")
                        else:
                            content_preview = content[:preview_chars].replace('\n', '\\n')
                            log_.debug(f"文件内容预览: {content_preview}...")
                        file_texts.append(f"【文件：{filename}】\n{content}")
                    else:
                        log_.warning(f"文件内容为空或是图片: {filename}")
                
                if file_texts:
                    full_question = f"{question}\n\n附件内容:\n" + "\n\n".join(file_texts)
                else:
                    log_.warning("没有有效的文件内容可以合并")
            else:
                log_.warning("没有文件内容，使用原始问题")
            
            # 调用原有的get_chat_response方法
            return self.get_chat_response(full_question, conversation_id)
        except Exception as e:
            log_.error(f"处理带文件的聊天请求失败: {str(e)}")
            log_.error(traceback.format_exc())
            raise
