from flask import Blueprint, current_app, request, g, Response
from flask_restful import Api
import os
import json
from datetime import datetime, date
from app.controllers.chat_controller import ChatController
from app.controllers.extraction_controller import ExtractionController
from app.controllers.knowledge_controller import SimpleKnowledgeController, KnowledgeBaseController, KnowledgeBaseFilesController, KnowledgeBaseBasicController
from app.controllers.auth_controller import AuthCodeResource, AuthLoginRegisterResource, AuthVerifyTokenResource
from app.controllers.file_controller import FileController
from app.services.chat_service import ChatService
from app.services.bot_service import BotService
from common import log_

# 创建前端API的Blueprint
frontend_bp = Blueprint('frontend_api', __name__, url_prefix='/api')
# 在 Blueprint 上初始化 Api
api = Api(frontend_bp)

# 配置API使用自定义JSONEncoder
def output_json_with_dates(data, code, headers=None):
    resp = current_app.response_class(
        response=json.dumps(data, cls=current_app.json_encoder),
        status=code,
        headers=headers,
        mimetype='application/json'
    )
    return resp

# 设置API使用自定义的JSON表示
api.representations = {'application/json': output_json_with_dates}

# 使用统一的 /llm 前缀
# 机器人API - 使用ChatController处理
api.add_resource(ChatController, '/llm/bots', endpoint='bots')
api.add_resource(ChatController, '/llm/bots/<int:bot_id>', endpoint='bot_detail')

# 聊天API - ChatController负责处理对话功能
api.add_resource(ChatController, '/llm/conversations', endpoint='conversations')
api.add_resource(ChatController, '/llm/conversations/<int:conversation_id>', endpoint='conversation')

# 提取API - 修改为使用 /llm 前缀
api.add_resource(ExtractionController, '/llm/extract')

# 知识库管理API
api.add_resource(KnowledgeBaseController, '/llm/knowledge-bases', endpoint='knowledge_bases', methods=['GET', 'POST'])
api.add_resource(KnowledgeBaseController, '/llm/knowledge-bases/<string:kb_id>', endpoint='kb_detail', methods=['GET', 'PUT', 'DELETE'])
api.add_resource(KnowledgeBaseBasicController, '/llm/knowledge-bases/basic')

# 文档管理API - 保持 /llm 前缀
api.add_resource(SimpleKnowledgeController, '/llm/documents', endpoint='documents')
api.add_resource(SimpleKnowledgeController, '/llm/documents/<string:document_id>', endpoint='document_detail', methods=['GET', 'DELETE', 'PUT'])
api.add_resource(SimpleKnowledgeController, '/llm/upload-document', endpoint='upload_document', methods=['POST'])

# 知识库文件列表API
api.add_resource(KnowledgeBaseFilesController, '/llm/knowledge-bases/<string:kb_id>/files', endpoint='kb_files')

# 添加身份验证相关路由
api.add_resource(AuthCodeResource, '/auth/send-code', endpoint='send_code', methods=['POST', 'OPTIONS'])
api.add_resource(AuthLoginRegisterResource, '/auth/login-register', endpoint='login_register', methods=['POST', 'OPTIONS'])
api.add_resource(AuthVerifyTokenResource, '/auth/verify-token', endpoint='verify_token', methods=['POST', 'OPTIONS'])

# 添加处理未保存聊天的API
api.add_resource(ChatController, '/llm/chat', endpoint='unsaved_chat', methods=['POST'])

# 文件预览和下载API
api.add_resource(FileController, '/llm/files/<int:document_id>', endpoint='file_preview', methods=['GET'])

# 流式聊天API - 使用蓝图直接注册以避免RESTful的JSON序列化
stream_chat_service = ChatService()

@frontend_bp.route('/llm/chat/stream', methods=['POST'])
@frontend_bp.route('/llm/conversations/<int:conversation_id>/stream', methods=['POST'])
def stream_chat_endpoint(conversation_id=None):
    user_id = getattr(g, 'user_id', None)
    if not user_id:
        return Response(
            'data: {"code": "UNAUTHORIZED", "message": "请先登录"}\n\n',
            mimetype='text/event-stream'
        )
    
    try:
        params = request.get_json() or {}
        question = params.get('question', '')
        
        if not question:
            return Response(
                'data: {"code": "PARAM_ERROR", "message": "请提供问题内容"}\n\n',
                mimetype='text/event-stream'
            )
        
        bot_id = params.get('bot_id')
        if bot_id:
            try:
                bot = BotService.get_bot(bot_id, user_id)
                if bot:
                    kb_ids = bot.get('kb_ids', [])
                    stream_chat_service.reset_context()
                    for kb_id in kb_ids:
                        stream_chat_service.load_knowledge_base_by_id(kb_id)
                    system_prompt = bot.get('system_prompt')
                    if system_prompt:
                        stream_chat_service.set_system_prompt(system_prompt)
            except Exception as e:
                log_.warning(f"加载机器人配置失败: {str(e)}")
        
        def generate():
            try:
                for chunk in stream_chat_service.stream_chat_response(question, conversation_id):
                    yield f'data: {json.dumps({"content": chunk}, ensure_ascii=False)}\n\n'
            except Exception as e:
                log_.error(f"流式输出异常: {str(e)}")
                yield f'data: {json.dumps({"error": str(e)}, ensure_ascii=False)}\n\n'
        
        return Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*'
            }
        )
    except Exception as e:
        log_.error(f"流式聊天初始化失败: {str(e)}")
        return Response(
            f'data: {{"code": "SYSTEM_ERROR", "message": {json.dumps(str(e), ensure_ascii=False)}}}\n\n',
            mimetype='text/event-stream'
        )

# 这里可以添加更多前端需要的路由