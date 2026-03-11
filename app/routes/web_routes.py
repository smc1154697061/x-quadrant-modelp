from flask import Blueprint, current_app
from flask_restful import Api
import os
import json
from datetime import datetime, date
from app.controllers.chat_controller import ChatController
from app.controllers.extraction_controller import ExtractionController
from app.controllers.knowledge_controller import SimpleKnowledgeController, KnowledgeBaseController, KnowledgeBaseFilesController, KnowledgeBaseBasicController
from app.controllers.auth_controller import AuthCodeResource, AuthLoginRegisterResource, AuthVerifyTokenResource
from app.controllers.file_controller import FileController

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

# 流式聊天API - 必须放在普通conversation路由之前，使用不同的URL结构
api.add_resource(ChatController, '/llm/stream/conversations/<int:conversation_id>', endpoint='conversation_stream')

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

# 这里可以添加更多前端需要的路由