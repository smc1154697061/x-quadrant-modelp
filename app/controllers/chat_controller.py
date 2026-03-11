from app.controllers.base import BaseResource
from app.services.chat_service import ChatService
from app.services.bot_service import BotService
from app.services.conversation_service import ConversationService
from app.services.message_service import MessageService
from app.services.knowledge_service import KnowledgeService
from app.entity.dto.bot_dto import BotCreateDTO, BotUpdateDTO
from app.entity.dto.chat_dto import ChatMessageDTO
from common import log_
from app.core.decorators import api_exception_handler, login_required, login_optional
from common.error_codes import APIException, ErrorCode, ParameterError, ResourceNotFound
import os
import json
import uuid
from flask import request, g, Response, stream_with_context
from datetime import datetime
import traceback
from common.db_utils import get_db_connection

# 创建全局服务实例
chat_service = ChatService()

class ChatController(BaseResource):
    """聊天控制器 - 处理对话功能（完全使用Service层，符合Java规范）"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            # 使用全局chat_service实例
            self.chat_service = chat_service
        except Exception as e:
            log_.error(f"初始化聊天控制器失败: {str(e)}")
            self.chat_service = None

    @api_exception_handler
    @login_required
    def post(self, conversation_id=None):
        """处理所有POST请求 - 创建对话和发送消息"""
        # 每次请求重置上下文，避免上下文混淆
        self.chat_service.reset_context()
        
        # 根据路径区分不同的POST操作
        if 'bots' in request.path:
            # 创建机器人请求
            return self.create_bot()
        elif 'chat' in request.path and conversation_id is None:
            # 处理不保存的对话
            return self.handle_unsaved_chat()
        elif '/stream/' in request.path:
            # 流式发送消息请求
            return self.send_message_stream(conversation_id)
        elif conversation_id is None:
            # 创建对话请求
            return self.create_conversation()
        else:
            # 发送消息请求
            return self.send_message(conversation_id)
    
    def create_bot(self):
        """创建新的对话机器人（Java风格）"""
        # 1. 接收请求转为DTO
        data = self.get_params()
        dto = BotCreateDTO.from_request(data)
        
        # 2. DTO自己校验
        dto.validate()
        
        # 3. 调用Service
        bot_vo = BotService.create_bot(dto, user_id=g.user_id)
        
        # 4. 返回VO
        return {
            "code": ErrorCode.SUCCESS.code,
            "message": "机器人创建成功",
            "data": bot_vo
        }, 200
            
    def handle_unsaved_chat(self):
        """处理不保存到数据库的对话"""
        # 1. 接收请求转为DTO
        data = self.get_params()
        dto = ChatMessageDTO.from_request(data)
        
        # 2. DTO校验
        dto.validate()
        
        try:
            # 3. 获取机器人信息（通过Service）
            bot_dict = BotService.get_bot(dto.bot_id, user_id=g.user_id)
            
            # 加载机器人关联的知识库
            kb_ids = bot_dict.get('kb_ids', [])
            
            # 重置服务上下文
            self.chat_service.reset_context()
            
            for kb_id in kb_ids:
                # 加载知识库并进行向量检索
                self.chat_service.load_knowledge_base_by_id(kb_id)
            
            # 设置系统提示词
            system_prompt = bot_dict.get('system_prompt')
            if system_prompt:
                self.chat_service.set_system_prompt(system_prompt)
            
            # 处理问题，但不保存到数据库
            response = self.chat_service.get_chat_response(dto.message, None)
            
            # 返回成功响应
            result = {
                "code": "SUCCESS",
                "message": "回复成功",
                "data": {
                    'answer': response,
                    'bot_id': dto.bot_id
                }
            }
            
            return result, 200
        except Exception as e:
            log_.error(f"处理不保存的对话失败: {str(e)}")
            return {
                "code": "SYSTEM_ERROR",
                "message": f"处理对话失败: {str(e)}",
                "data": None
            }, 200
            
    def send_message(self, conversation_id=None):
        """处理发送消息请求（支持文件上传）"""
        params = self.get_params()
        question = params.get('question', '')  # 允许只上传文件不输入文字
        
        # 检查是否有文件上传（兼容字段名 files 和 file）
        files = request.files.getlist('files')  # 支持多文件上传
        if not files:
            files = request.files.getlist('file')
        
        if not question and not files:
            return {
                "code": "PARAM_ERROR",
                "message": "请提供问题内容或上传文件",
                "data": None
            }, 200
        
        try:
            # 获取用户ID - 必须登录
            user_id = g.user_id
            
            # 验证对话（使用Service）
            conversation = ConversationService.get_conversation(conversation_id, user_id)
            if not conversation:
                return {
                    "code": "RESOURCE_NOT_FOUND",
                    "message": "对话不存在",
                    "data": None
                }, 200
            
            # 检查是否是当前用户的对话
            if conversation['user_id'] != user_id:
                return {
                    "code": "PERMISSION_DENIED",
                    "message": "无权访问此对话",
                    "data": None
                }, 200
            
            # 获取关联的机器人信息（使用Service）
            bot_id = conversation.get('bot_id')
            bot = None
            if bot_id:
                bot = BotService.get_bot(bot_id, user_id)
                if bot:
                    # 加载机器人关联的知识库
                    kb_ids = bot.get('kb_ids', [])
            
            # 重置服务上下文，确保每次对话都是基于最新的知识库
            self.chat_service.reset_context()
            
            for kb_id in kb_ids:
                # 加载知识库并进行向量检索
                self.chat_service.load_knowledge_base_by_id(kb_id)
            
            # 从请求中获取角色标识（前端可以传递 role_key 参数）
            role_key = params.get('role_key')  # 如: writer, english_expert, programmer 等
            if role_key:
                self.chat_service.set_role(role_key)
            
            # 设置系统提示词（优先级高于角色模板）
            system_prompt = bot.get('system_prompt')
            if system_prompt:
                self.chat_service.set_system_prompt(system_prompt)
            
            # 处理文件上传
            uploaded_files = []
            file_contents = []
            
            if files:
                # 从表单中获取前端传来的原始文件名（如果有）
                original_filename = request.form.get('original_filename')
                
                for file in files:
                    try:
                        file_info = self.chat_service.upload_message_file(
                            file=file,
                            user_id=user_id,
                            bot_name=bot.get('name') if bot else None,
                            original_filename=original_filename
                        )
                        uploaded_files.append(file_info)
                        
                        # 提取文件内容用于生成回答
                        if file_info.get('file_content_text'):
                            file_contents.append({
                                'filename': file_info['filename'],
                                'content': file_info['file_content_text']
                            })
                    except Exception as e:
                        log_.error(f"上传文件失败: {str(e)}")
                        return {
                            "code": "FILE_UPLOAD_ERROR",
                            "message": f"文件上传失败: {str(e)}",
                            "data": None
                        }, 200
            
            # 保存用户消息到数据库
            try:
                if uploaded_files and question:
                    # 情况1：既有文件又有文字 → 拆成两条消息
                    # 1) 先保存“文件消息”，只显示占位文案并关联附件
                    file_message = MessageService.save_message(
                        conversation_id=conversation_id,
                        role='user',
                        content='[已上传文件]'
                    )
                    file_message_id = file_message.get('id')
                    if file_message_id:
                        for file_info in uploaded_files:
                            self.chat_service.message_document_dao.create_message_document(
                                message_id=file_message_id,
                                document_id=file_info['document_id']
                            )

                    # 2) 再保存纯文本消息（不再额外关联附件）
                    user_message = MessageService.save_message(
                        conversation_id=conversation_id,
                        role='user',
                        content=question
                    )
                else:
                    # 情况2：只有文件 或 只有文字 → 保持原有一条消息逻辑
                    display_content = question if question else "[已上传文件]"
                    user_message = MessageService.save_message(
                        conversation_id=conversation_id,
                        role='user',
                        content=display_content
                    )
                    user_message_id = user_message.get('id')
                    if user_message_id and uploaded_files:
                        for file_info in uploaded_files:
                            self.chat_service.message_document_dao.create_message_document(
                                message_id=user_message_id,
                                document_id=file_info['document_id']
                            )
            except Exception as e:
                log_.error(f"保存用户消息异常: {str(e)}")
                log_.error(traceback.format_exc())
            
            # 调用chat_service处理请求（支持文件内容）
            if file_contents:
                response = self.chat_service.get_chat_response_with_files(
                    question=question,
                    file_contents=file_contents,
                    conversation_id=conversation_id
                )
            else:
                response = self.chat_service.get_chat_response(question, conversation_id)
            
            # 保存AI回复到数据库
            try:
                ai_message = MessageService.save_message(
                    conversation_id=conversation_id,
                    role='assistant',
                    content=response
                )
                ai_message_id = ai_message.get('id')
                if ai_message_id:
                    log_.debug(f"AI回复已成功保存到数据库，ID: {ai_message_id}")
                else:
                    log_.error(f"AI回复未能保存到数据库，返回ID为空")
            except Exception as e:
                log_.error(f"保存AI回复失败: {str(e)}")
            
            # 返回成功响应
            result = {
                "code": "SUCCESS",
                "message": "回复成功",
                "data": {
                    'answer': response,
                    'conversation_id': conversation_id
                }
            }
                
            return result, 200
        except Exception as e:
            log_.error(f"发送消息失败: {str(e)}")
            return {
                "code": "SYSTEM_ERROR",
                "message": f"发送消息失败: {str(e)}",
                "data": None
            }, 200

    def send_message_stream(self, conversation_id=None):
        """处理发送消息请求（流式响应）"""
        params = self.get_params()
        question = params.get('question', '')
        
        files = request.files.getlist('files')
        if not files:
            files = request.files.getlist('file')
        
        if not question and not files:
            def error_gen():
                yield f"data: {json.dumps({'code': 'PARAM_ERROR', 'message': '请提供问题内容或上传文件', 'data': None}, ensure_ascii=False)}\n\n"
            return Response(stream_with_context(error_gen()), mimetype='text/event-stream')
        
        try:
            user_id = g.user_id
            conversation = ConversationService.get_conversation(conversation_id, user_id)
            if not conversation:
                def error_gen():
                    yield f"data: {json.dumps({'code': 'RESOURCE_NOT_FOUND', 'message': '对话不存在', 'data': None}, ensure_ascii=False)}\n\n"
                return Response(stream_with_context(error_gen()), mimetype='text/event-stream')
            
            if conversation['user_id'] != user_id:
                def error_gen():
                    yield f"data: {json.dumps({'code': 'PERMISSION_DENIED', 'message': '无权访问此对话', 'data': None}, ensure_ascii=False)}\n\n"
                return Response(stream_with_context(error_gen()), mimetype='text/event-stream')
            
            bot_id = conversation.get('bot_id')
            bot = None
            if bot_id:
                bot = BotService.get_bot(bot_id, user_id)
                if bot:
                    kb_ids = bot.get('kb_ids', [])
            
            self.chat_service.reset_context()
            
            for kb_id in kb_ids:
                self.chat_service.load_knowledge_base_by_id(kb_id)
            
            role_key = params.get('role_key')
            if role_key:
                self.chat_service.set_role(role_key)
            
            system_prompt = bot.get('system_prompt')
            if system_prompt:
                self.chat_service.set_system_prompt(system_prompt)
            
            uploaded_files = []
            file_contents = []
            
            if files:
                original_filename = request.form.get('original_filename')
                
                for file in files:
                    try:
                        file_info = self.chat_service.upload_message_file(
                            file=file,
                            user_id=user_id,
                            bot_name=bot.get('name') if bot else None,
                            original_filename=original_filename
                        )
                        uploaded_files.append(file_info)
                        
                        if file_info.get('file_content_text'):
                            file_contents.append({
                                'filename': file_info['filename'],
                                'content': file_info['file_content_text']
                            })
                    except Exception as e:
                        log_.error(f"上传文件失败: {str(e)}")
                        def error_gen():
                            yield f"data: {json.dumps({'code': 'FILE_UPLOAD_ERROR', 'message': f'文件上传失败: {str(e)}', 'data': None}, ensure_ascii=False)}\n\n"
                        return Response(stream_with_context(error_gen()), mimetype='text/event-stream')
            
            try:
                if uploaded_files and question:
                    file_message = MessageService.save_message(
                        conversation_id=conversation_id,
                        role='user',
                        content='[已上传文件]'
                    )
                    file_message_id = file_message.get('id')
                    if file_message_id:
                        for file_info in uploaded_files:
                            self.chat_service.message_document_dao.create_message_document(
                                message_id=file_message_id,
                                document_id=file_info['document_id']
                            )

                    user_message = MessageService.save_message(
                        conversation_id=conversation_id,
                        role='user',
                        content=question
                    )
                else:
                    display_content = question if question else "[已上传文件]"
                    user_message = MessageService.save_message(
                        conversation_id=conversation_id,
                        role='user',
                        content=display_content
                    )
                    user_message_id = user_message.get('id')
                    if user_message_id and uploaded_files:
                        for file_info in uploaded_files:
                            self.chat_service.message_document_dao.create_message_document(
                                message_id=user_message_id,
                                document_id=file_info['document_id']
                            )
            except Exception as e:
                log_.error(f"保存用户消息异常: {str(e)}")
            
            full_response = []
            
            def generate():
                try:
                    if file_contents:
                        stream_gen = self.chat_service.get_chat_response_with_files_stream(
                            question=question,
                            file_contents=file_contents,
                            conversation_id=conversation_id
                        )
                    else:
                        stream_gen = self.chat_service.get_chat_response_stream(question, conversation_id)
                    
                    for chunk in stream_gen:
                        if chunk:
                            full_response.append(chunk)
                            yield f"data: {json.dumps({'code': 'STREAM', 'data': {'content': chunk}}, ensure_ascii=False)}\n\n"
                    
                    complete_response = ''.join(full_response)
                    try:
                        ai_message = MessageService.save_message(
                            conversation_id=conversation_id,
                            role='assistant',
                            content=complete_response
                        )
                        log_.debug(f"AI回复已成功保存到数据库，ID: {ai_message.get('id')}")
                    except Exception as e:
                        log_.error(f"保存AI回复失败: {str(e)}")
                    
                    yield f"data: {json.dumps({'code': 'DONE', 'data': {'conversation_id': conversation_id}}, ensure_ascii=False)}\n\n"
                    
                except Exception as e:
                    log_.error(f"流式响应生成失败: {str(e)}")
                    yield f"data: {json.dumps({'code': 'SYSTEM_ERROR', 'message': f'生成回复失败: {str(e)}', 'data': None}, ensure_ascii=False)}\n\n"
            
            return Response(stream_with_context(generate()), mimetype='text/event-stream')
            
        except Exception as e:
            log_.error(f"发送消息失败: {str(e)}")
            def error_gen():
                yield f"data: {json.dumps({'code': 'SYSTEM_ERROR', 'message': f'发送消息失败: {str(e)}', 'data': None}, ensure_ascii=False)}\n\n"
            return Response(stream_with_context(error_gen()), mimetype='text/event-stream')
            
    def create_conversation(self):
        """创建新对话"""
        try:
            params = self.get_params()
            bot_id = params.get('bot_id')
            
            if not bot_id:
                return {
                    "code": "PARAM_ERROR",
                    "message": "请提供机器人ID",
                    "data": None
                }, 200
                
            # 获取用户ID
            user_id = g.user_id
            
            # 验证机器人是否存在（使用Service）
            bot = BotService.get_bot(bot_id, user_id)
            
            # 创建对话（使用Service）
            conversation = ConversationService.create_conversation(user_id, bot_id)
            
            # 添加机器人信息到返回数据
            conversation['bot_name'] = bot.get('name', '')
            conversation['bot_description'] = bot.get('description', '')
            
            return {
                "code": "SUCCESS",
                "message": "对话创建成功",
                "data": conversation
            }, 200
        except Exception as e:
            log_.error(f"创建对话失败: {str(e)}")
            return {
                "code": "SYSTEM_ERROR",
                "message": f"创建对话失败: {str(e)}",
                "data": None
            }, 200
    
    @api_exception_handler
    @login_optional
    def get(self, conversation_id=None, bot_id=None):
        """获取对话或机器人信息"""
        # 根据路径区分不同的GET操作
        if 'bots' in request.path:
            # 获取机器人信息
            return self.get_bot(bot_id)
        elif conversation_id is not None:
            # 获取单个对话详情
            return self.get_conversation(conversation_id)
        else:
            # 获取用户的对话列表
            return self.get_user_conversations()
    
    # 添加获取机器人信息的方法
    def get_bot(self, bot_id=None):
        """获取机器人信息（使用Service层）"""
        user_id = getattr(g, 'user_id', None)
        
        # 获取单个机器人
        if bot_id:
            try:
                bot = BotService.get_bot(bot_id, user_id)
                return {
                    "code": "SUCCESS",
                    "message": "获取机器人成功",
                    "data": bot
                }, 200
            except ResourceNotFound:
                return {
                    "code": "RESOURCE_NOT_FOUND",
                    "message": "机器人不存在",
                    "data": None
                }, 404
            except APIException as e:
                return {
                    "code": e.code,
                    "message": e.message,
                    "data": None
                }, 403
        
        # 获取机器人列表
        else:
            # 使用正确的Service方法
            if user_id:
                bots = BotService.list_user_bots(user_id, include_public=True)
            else:
                bots = BotService.list_public_bots()
            
            return {
                "code": "SUCCESS",
                "message": "获取机器人列表成功",
                "data": {
                    "bots": bots
                }
            }, 200
    
    def get_conversation(self, conversation_id):
        """获取单个对话详情"""
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return {
                "code": "UNAUTHORIZED",
                "message": "获取对话需要登录",
                "data": None
            }, 200
        
        # 获取单个对话的消息（使用Service）
        conversation = ConversationService.get_conversation(conversation_id, user_id)
        if not conversation:
            return {
                "code": "RESOURCE_NOT_FOUND",
                "message": "对话不存在",
                "data": None
            }, 200
            
        # 检查是否是当前用户的对话
        if conversation['user_id'] != user_id:
            return {
                "code": "PERMISSION_DENIED",
                "message": "无权访问此对话",
                "data": None
            }, 200
        
        # 获取关联的机器人信息
        bot_id = conversation.get('bot_id')
        bot = None
        if bot_id:
            bot = BotService.get_bot(bot_id, user_id)
                
        messages = MessageService.get_messages(conversation_id)
            
        return {
            "code": "SUCCESS",
            "message": "获取对话成功",
            "data": {
                'conversation': conversation,
                'bot': bot,
                'messages': messages
            }
        }, 200
    
    def get_user_conversations(self):
        """获取用户的对话列表"""
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return {
                "code": "UNAUTHORIZED",
                "message": "获取对话列表需要登录",
                "data": None
            }, 200
        
        # 获取查询参数
        bot_id = request.args.get('bot_id')
        
        # 获取用户的所有对话（使用Service）
        conversations = ConversationService.get_user_conversations(user_id, bot_id)

        # 为每个对话添加机器人信息（使用Service）
        for conversation in conversations:
            conv_bot_id = conversation.get('bot_id')
            if conv_bot_id:
                try:
                    bot = BotService.get_bot(conv_bot_id, user_id)
                    conversation['bot_name'] = bot.get('name', '')
                    conversation['bot_description'] = bot.get('description', '')
                except:
                    pass
        
        return {
            "code": "SUCCESS",
            "message": "获取对话列表成功",
            "data": {
                'conversations': conversations
            }
        }, 200
    
    @api_exception_handler
    def put(self, conversation_id=None, bot_id=None):
        """更新机器人信息"""
        # 获取当前用户ID
        user_id = getattr(g, 'user_id', None)
        
        # 如果用户未登录，返回未授权错误
        if not user_id:
            return {
                "code": "UNAUTHORIZED",
                "message": "请先登录",
                "data": None
            }, 200
        
        # 优先使用路由参数中的 bot_id，如果没有再从路径提取
        if bot_id is None and '/bots/' in request.path:
            path_parts = request.path.split('/')
            for i, part in enumerate(path_parts):
                if part == 'bots' and i+1 < len(path_parts):
                    try:
                        bot_id = int(path_parts[i+1])
                    except:
                        pass
            
        if bot_id is not None:
            return self.update_bot(bot_id)
        else:
            return {
                "code": "PARAM_ERROR",
                "message": "无效的请求",
                "data": None
            }, 200
    
    # 添加更新机器人的方法（使用Service）
    def update_bot(self, bot_id):
        """更新机器人信息（Java风格）"""
        # 1. 接收请求转为DTO
        data = self.get_params()
        dto = BotUpdateDTO.from_request(data)
        
        # 2. DTO校验
        dto.validate()
        
        # 3. 调用Service
        try:
            updated = BotService.update_bot(bot_id, dto, user_id=g.user_id)
            return {
                "code": "SUCCESS",
                "message": "机器人更新成功",
                "data": updated
            }, 200
        except (ResourceNotFound, APIException) as e:
            return {
                "code": e.code if hasattr(e, 'code') else "ERROR",
                "message": e.message if hasattr(e, 'message') else str(e),
                "data": None
            }, 200
    
    @api_exception_handler
    def delete(self, conversation_id=None, bot_id=None):
        # 获取当前用户ID
        user_id = getattr(g, 'user_id', None)
        
        # 如果用户未登录，返回未授权错误
        if not user_id:
            return {
                "code": "UNAUTHORIZED",
                "message": "请先登录",
                "data": None
            }, 200
        
        # 如果直接提供了bot_id参数，则删除机器人
        if bot_id is not None:
            return self.delete_bot(bot_id)
        
        # 根据路径区分不同的DELETE操作
        if 'bots' in request.path:
            # 从路径中提取机器人ID
            extracted_bot_id = None
            if '/bots/' in request.path:
                path_parts = request.path.split('/')
                for i, part in enumerate(path_parts):
                    if part == 'bots' and i+1 < len(path_parts):
                        try:
                            extracted_bot_id = int(path_parts[i+1])
                        except:
                            pass
            if extracted_bot_id:
                return self.delete_bot(extracted_bot_id)
            else:
                return {
                    "code": "PARAM_ERROR",
                    "message": "无效的请求",
                    "data": None
                }, 200
        elif conversation_id is not None:
            # 删除对话
            return self.delete_conversation(conversation_id)
        else:
            return {
                "code": "PARAM_ERROR",
                "message": "无效的请求",
                "data": None
            }, 200
    
    # 添加删除机器人的方法
    def delete_bot(self, bot_id):
        """删除机器人（使用Service）"""
        try:
            # 调用Service
            BotService.delete_bot(bot_id, user_id=g.user_id)
            
            return {
                "code": "SUCCESS",
                "message": "机器人删除成功",
                "data": None
            }, 200
        except (ResourceNotFound, APIException) as e:
            return {
                "code": e.code if hasattr(e, 'code') else "ERROR",
                "message": e.message if hasattr(e, 'message') else str(e),
                "data": None
            }, 200
        except Exception as e:
            log_.error(f"删除机器人失败: {str(e)}")
            return {
                "code": "SYSTEM_ERROR",
                "message": f"删除机器人失败: {str(e)}",
                "data": None
            }, 200

    def delete_conversation(self, conversation_id):
        """删除对话（使用Service）"""
        try:
            # 先删除消息
            MessageService.delete_conversation_messages(conversation_id)
            
            # 再删除对话
            ConversationService.delete_conversation(conversation_id, user_id=g.user_id)
            
            return {
                "code": "SUCCESS",
                "message": "对话删除成功",
                "data": None
            }, 200
        except (ResourceNotFound, APIException) as e:
            return {
                "code": e.code if hasattr(e, 'code') else "ERROR",
                "message": e.message if hasattr(e, 'message') else str(e),
                "data": None
            }, 200
        except Exception as e:
            log_.error(f"删除对话失败: {str(e)}")
            return {
                "code": "SYSTEM_ERROR",
                "message": f"删除对话失败: {str(e)}",
                "data": None
            }, 200