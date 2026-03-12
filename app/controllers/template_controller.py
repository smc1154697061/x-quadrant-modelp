"""
模板文档控制器
"""
from flask import request, send_file
import io
from app.controllers.base import BaseResource
from app.services.template_service import TemplateService
from app.core.decorators import api_exception_handler
from common import log_
from common.error_codes import APIException, ErrorCode, ParameterError


class TemplateController(BaseResource):
    """模板管理控制器"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.template_service = TemplateService()
    
    @api_exception_handler
    def get(self, template_id=None):
        """获取模板列表或单个模板"""
        user_id = getattr(request, 'user_id', None)
        if not user_id:
            raise APIException(ErrorCode.UNAUTHORIZED, msg="请先登录")
        
        if template_id:
            file_data, file_type, name = self.template_service.get_template_file(template_id, user_id)
            
            ext = 'docx' if file_type == 'word' else ('pdf' if file_type == 'pdf' else 'txt')
            filename = f"{name}.{ext}"
            
            return send_file(
                io.BytesIO(file_data),
                as_attachment=True,
                download_name=filename,
                mimetype=self._get_mimetype(ext)
            )
        else:
            category = request.args.get('category')
            keyword = request.args.get('keyword')
            
            templates = self.template_service.get_template_list(user_id, category, keyword)
            
            return {
                "code": 0,
                "message": "获取成功",
                "data": templates
            }, 200
    
    @api_exception_handler
    def post(self):
        """上传模板"""
        user_id = getattr(request, 'user_id', None)
        if not user_id:
            raise APIException(ErrorCode.UNAUTHORIZED, msg="请先登录")
        
        if 'file' not in request.files:
            raise ParameterError(msg="请上传模板文件")
        
        file = request.files['file']
        if file.filename == '':
            raise ParameterError(msg="未选择文件")
        
        name = request.form.get('name')
        category = request.form.get('category', '其他')
        description = request.form.get('description', '')
        is_public = request.form.get('is_public', 'false').lower() == 'true'
        
        if not name:
            raise ParameterError(msg="请填写模板名称")
        
        result = self.template_service.upload_template(
            file, name, category, description, user_id, is_public
        )
        
        return {
            "code": 0,
            "message": "上传成功",
            "data": result
        }, 200
    
    @api_exception_handler
    def delete(self, template_id):
        """删除模板"""
        user_id = getattr(request, 'user_id', None)
        if not user_id:
            raise APIException(ErrorCode.UNAUTHORIZED, msg="请先登录")
        
        result = self.template_service.delete_template(template_id, user_id)
        
        return {
            "code": 0,
            "message": "删除成功",
            "data": {"success": result}
        }, 200
    
    def _get_mimetype(self, ext):
        """获取MIME类型"""
        mimes = {
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'pdf': 'application/pdf',
            'txt': 'text/plain'
        }
        return mimes.get(ext, 'application/octet-stream')


class TemplateCategoryController(BaseResource):
    """模板分类控制器"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.template_service = TemplateService()
    
    @api_exception_handler
    def get(self):
        """获取所有分类"""
        user_id = getattr(request, 'user_id', None)
        
        categories = self.template_service.get_categories(user_id)
        
        return {
            "code": 0,
            "message": "获取成功",
            "data": categories
        }, 200


class DocumentGenerateController(BaseResource):
    """文档生成控制器"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.template_service = TemplateService()
    
    @api_exception_handler
    def post(self):
        """生成文档"""
        user_id = getattr(request, 'user_id', None)
        if not user_id:
            raise APIException(ErrorCode.UNAUTHORIZED, msg="请先登录")
        
        data = request.get_json() or {}
        template_id = data.get('template_id')
        user_input = data.get('user_input')
        output_format = data.get('output_format', 'word')
        
        if not template_id:
            raise ParameterError(msg="请选择模板")
        if not user_input:
            raise ParameterError(msg="请输入个人信息")
        
        result = self.template_service.generate_document(
            template_id, user_input, output_format, user_id
        )
        
        return {
            "code": 0,
            "message": "生成成功",
            "data": result
        }, 200


class GeneratedDocumentController(BaseResource):
    """生成文档管理控制器"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.template_service = TemplateService()
    
    @api_exception_handler
    def get(self, doc_id=None):
        """获取生成历史或下载文档"""
        user_id = getattr(request, 'user_id', None)
        if not user_id:
            raise APIException(ErrorCode.UNAUTHORIZED, msg="请先登录")
        
        if doc_id:
            file_data, filename, file_ext = self.template_service.download_generated_document(doc_id, user_id)
            
            return send_file(
                io.BytesIO(file_data),
                as_attachment=True,
                download_name=filename,
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document' if file_ext == 'docx' else 'application/pdf'
            )
        else:
            history = self.template_service.get_generation_history(user_id)
            
            return {
                "code": 0,
                "message": "获取成功",
                "data": history
            }, 200
    
    @api_exception_handler
    def delete(self, doc_id):
        """删除生成记录"""
        user_id = getattr(request, 'user_id', None)
        if not user_id:
            raise APIException(ErrorCode.UNAUTHORIZED, msg="请先登录")
        
        from app.dao.template_dao import GeneratedDocumentDAO
        result = GeneratedDocumentDAO.delete(doc_id)
        
        return {
            "code": 0,
            "message": "删除成功",
            "data": {"success": result}
        }, 200
