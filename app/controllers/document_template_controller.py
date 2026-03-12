"""
文档模板控制器
"""
import os
import uuid
from flask import request, g
from app.controllers.base import BaseResource
from common import log_
from app.services.document_template_service import DocumentTemplateService


class DocumentTemplateController(BaseResource):
    """文档模板控制器"""
    
    def __init__(self):
        self.service = DocumentTemplateService()
    
    def get(self, template_id=None):
        """
        获取模板列表或详情
        """
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return {'code': 'UNAUTHORIZED', 'message': '请先登录'}, 401
        
        try:
            if template_id:
                # 获取单个模板详情
                template = self.service.get_template_detail(template_id, user_id)
                if not template:
                    return {'code': 'NOT_FOUND', 'message': '模板不存在'}, 404
                
                return {
                    'code': 'SUCCESS',
                    'message': '获取成功',
                    'data': template
                }
            else:
                # 获取模板列表
                tag = request.args.get('tag')
                search = request.args.get('search')
                
                templates = self.service.get_template_list(user_id, tag, search)
                
                return {
                    'code': 'SUCCESS',
                    'message': '获取成功',
                    'data': templates
                }
        
        except Exception as e:
            log_.error(f"获取模板失败: {str(e)}")
            return {'code': 'SYSTEM_ERROR', 'message': f'获取失败: {str(e)}'}, 500
    
    def post(self):
        """
        上传模板
        """
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return {'code': 'UNAUTHORIZED', 'message': '请先登录'}, 401
        
        try:
            # 检查是否有文件
            if 'file' not in request.files:
                return {'code': 'PARAMETER_ERROR', 'message': '请上传文件'}, 400
            
            file = request.files['file']
            if file.filename == '':
                return {'code': 'PARAMETER_ERROR', 'message': '文件名不能为空'}, 400
            
            # 获取表单数据
            name = request.form.get('name', file.filename)
            tags = request.form.get('tags', '')
            
            # 保存临时文件（使用系统临时目录，兼容Windows）
            import tempfile
            temp_dir = tempfile.gettempdir()
            os.makedirs(temp_dir, exist_ok=True)
            temp_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{file.filename}")
            file.save(temp_path)
            
            # 获取文件大小
            file_size = os.path.getsize(temp_path)
            
            # 调用服务上传
            result = self.service.upload_template(
                user_id=user_id,
                file_path=temp_path,
                file_name=name,
                tags=tags,
                file_size=file_size
            )
            
            # 清理临时文件
            try:
                os.remove(temp_path)
            except:
                pass
            
            if result['success']:
                return {
                    'code': 'SUCCESS',
                    'message': result['message'],
                    'data': {'template_id': result['template_id']}
                }
            else:
                return {'code': 'SYSTEM_ERROR', 'message': result['message']}, 500
        
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            log_.error(f"上传模板失败: {str(e)}\n详细错误:\n{error_detail}")
            return {'code': 'SYSTEM_ERROR', 'message': f'上传失败: {str(e)}'}, 500
    
    def delete(self, template_id):
        """
        删除模板
        """
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return {'code': 'UNAUTHORIZED', 'message': '请先登录'}, 401
        
        try:
            result = self.service.delete_template(template_id, user_id)
            
            if result['success']:
                return {
                    'code': 'SUCCESS',
                    'message': result['message']
                }
            else:
                return {'code': 'SYSTEM_ERROR', 'message': result['message']}, 500
        
        except Exception as e:
            log_.error(f"删除模板失败: {str(e)}")
            return {'code': 'SYSTEM_ERROR', 'message': f'删除失败: {str(e)}'}, 500


class DocumentGenerationController(BaseResource):
    """文档生成控制器"""
    
    def __init__(self):
        self.service = DocumentTemplateService()
    
    def post(self):
        """
        生成文档
        """
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return {'code': 'UNAUTHORIZED', 'message': '请先登录'}, 401
        
        try:
            data = request.get_json()
            if not data:
                return {'code': 'PARAMETER_ERROR', 'message': '请求体不能为空'}, 400
            
            template_id = data.get('template_id')
            user_input = data.get('user_input')
            
            if not template_id:
                return {'code': 'PARAMETER_ERROR', 'message': '请选择模板'}, 400
            
            if not user_input:
                return {'code': 'PARAMETER_ERROR', 'message': '请输入个人信息'}, 400
            
            result = self.service.generate_document(user_id, template_id, user_input)
            
            if result['success']:
                return {
                    'code': 'SUCCESS',
                    'message': result['message'],
                    'data': {
                        'generation_id': result['generation_id'],
                        'content': result['content']
                    }
                }
            else:
                return {'code': 'SYSTEM_ERROR', 'message': result['message']}, 500
        
        except Exception as e:
            log_.error(f"生成文档失败: {str(e)}")
            return {'code': 'SYSTEM_ERROR', 'message': f'生成失败: {str(e)}'}, 500


class GenerationHistoryController(BaseResource):
    """生成历史控制器"""
    
    def __init__(self):
        self.service = DocumentTemplateService()
    
    def get(self, generation_id=None):
        """
        获取生成历史列表或详情
        """
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return {'code': 'UNAUTHORIZED', 'message': '请先登录'}, 401
        
        try:
            if generation_id:
                # 获取单个生成记录详情
                generation = self.service.get_generation_detail(generation_id, user_id)
                if not generation:
                    return {'code': 'NOT_FOUND', 'message': '记录不存在'}, 404
                
                return {
                    'code': 'SUCCESS',
                    'message': '获取成功',
                    'data': generation
                }
            else:
                # 获取历史列表
                page = request.args.get('page', 1, type=int)
                page_size = request.args.get('page_size', 20, type=int)
                
                result = self.service.get_generation_history(user_id, page, page_size)
                
                return {
                    'code': 'SUCCESS',
                    'message': '获取成功',
                    'data': result
                }
        
        except Exception as e:
            log_.error(f"获取生成历史失败: {str(e)}")
            return {'code': 'SYSTEM_ERROR', 'message': f'获取失败: {str(e)}'}, 500


class DocumentExportController(BaseResource):
    """文档导出控制器"""
    
    def __init__(self):
        self.service = DocumentTemplateService()
    
    def get(self, generation_id):
        """
        导出生成的文档为Word或PDF
        """
        from flask import send_file
        
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return {'code': 'UNAUTHORIZED', 'message': '请先登录'}, 401
        
        try:
            export_format = request.args.get('format', 'word')
            
            result = self.service.export_generation(generation_id, user_id, export_format)
            
            if not result['success']:
                return {'code': 'SYSTEM_ERROR', 'message': result['message']}, 500
            
            # 返回文件下载
            return send_file(
                result['file_path'],
                mimetype=result['content_type'],
                as_attachment=True,
                download_name=result['file_name']
            )
        
        except Exception as e:
            log_.error(f"导出文档失败: {str(e)}")
            return {'code': 'SYSTEM_ERROR', 'message': f'导出失败: {str(e)}'}, 500
