from app.controllers.base import BaseResource
from flask import request, g, send_file, Response
import io
from common import log_
from app.services.doc_generation_service import DocGenerationService
from app.core.decorators import api_exception_handler, login_required
from common.error_codes import APIException, ErrorCode, ParameterError


class DocGenerationController(BaseResource):
    """文档生成控制器"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.doc_generation_service = DocGenerationService()

    @api_exception_handler
    @login_required
    def get(self, result_id=None, format=None):
        """获取历史记录、结果详情或下载文档"""
        user_id = g.user_id

        if '/history' in request.path:
            limit = int(request.args.get('limit', 100))
            offset = int(request.args.get('offset', 0))
            history = self.doc_generation_service.get_history(user_id, limit, offset)
            return {
                "code": 0,
                "message": "获取成功",
                "data": history
            }, 200

        if '/download' in request.path and result_id and format:
            file_url = self.doc_generation_service.download_document(result_id, user_id, format)
            return {
                "code": 0,
                "message": "获取下载地址成功",
                "data": {
                    "download_url": file_url
                }
            }, 200

        if result_id:
            result = self.doc_generation_service.get_result_detail(result_id, user_id)
            return {
                "code": 0,
                "message": "获取成功",
                "data": result
            }, 200

        return {
            "code": "PARAM_ERROR",
            "message": "参数错误",
            "data": None
        }, 400

    @api_exception_handler
    @login_required
    def post(self, action=None):
        """生成文档"""
        user_id = g.user_id

        params = self.get_params()
        template_id = params.get('template_id')
        user_input = params.get('user_input', '')

        if not template_id:
            raise ParameterError(msg="请选择模板")
        if not user_input:
            raise ParameterError(msg="请输入用户信息")

        result = self.doc_generation_service.generate_document(user_id, template_id, user_input)

        return {
            "code": 0,
            "message": "生成成功",
            "data": result
        }, 200
