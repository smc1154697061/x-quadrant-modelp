from app.controllers.base import BaseResource
from flask import request, g
from common import log_
from app.services.template_service import TemplateService
from app.core.decorators import api_exception_handler, login_required
from common.error_codes import APIException, ErrorCode, ParameterError


class TemplateController(BaseResource):
    """模板管理控制器"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.template_service = TemplateService()

    @api_exception_handler
    @login_required
    def get(self, template_id=None):
        """获取模板列表或模板详情"""
        user_id = g.user_id

        if template_id:
            template = self.template_service.get_template_detail(template_id, user_id)
            return {
                "code": 0,
                "message": "获取成功",
                "data": template
            }, 200
        else:
            tag = request.args.get('tag')
            keyword = request.args.get('keyword')
            limit = int(request.args.get('limit', 100))
            offset = int(request.args.get('offset', 0))

            templates = self.template_service.get_templates(user_id, tag, keyword, limit, offset)
            return {
                "code": 0,
                "message": "获取成功",
                "data": templates
            }, 200

    @api_exception_handler
    @login_required
    def post(self):
        """上传模板"""
        user_id = g.user_id

        if 'file' not in request.files:
            raise ParameterError(msg="请上传模板文件")

        file = request.files['file']
        if file.filename == '':
            raise ParameterError(msg="未选择文件")

        name = request.form.get('name', '')
        tag = request.form.get('tag', 'other')

        result = self.template_service.upload_template(file, name, tag, user_id)

        return {
            "code": 0,
            "message": "上传成功",
            "data": result
        }, 200

    @api_exception_handler
    @login_required
    def delete(self, template_id):
        """删除模板"""
        user_id = g.user_id

        if not template_id:
            raise ParameterError(msg="请提供模板ID")

        result = self.template_service.delete_template(template_id, user_id)

        return {
            "code": 0,
            "message": "删除成功",
            "data": result
        }, 200
