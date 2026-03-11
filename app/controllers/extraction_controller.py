import os
from app.controllers.base import BaseResource
from flask import request
from common import log_
from app.services.extraction_service import ExtractionService
from app.core.decorators import api_exception_handler
from common.error_codes import APIException, ErrorCode, ParameterError, FileError

class ExtractionController(BaseResource):
    """文件内容提取控制器"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extraction_service = ExtractionService()
    
    @api_exception_handler
    def post(self):
        """处理文件提取请求"""
        # 检查是否有文件上传
        if 'file' not in request.files:
            raise ParameterError(msg="请上传文件")
        
        file = request.files['file']
        if file.filename == '':
            raise ParameterError(msg="未选择文件")
            
        # 获取JSON schema
        schema = request.form.get('schema')
        
        if not schema:
            raise ParameterError(msg="请提供JSON结构模板")
        
        # 直接调用服务层的process_file方法处理整个流程
        try:
            result, status_code = self.extraction_service.process_file(file, schema)
            if status_code != 200:
                raise APIException(ErrorCode.EXTRACT_ERROR, msg="处理失败")
                
            # 修改返回结果，确保code为0而不是0000
            return {
                "code": 0,
                "message": "操作成功",
                "data": result
            }, 200
        except APIException as e:
            log_.error(f"API异常: {str(e)}")
            raise
        except Exception as e:
            log_.error(f"提取处理失败: {str(e)}")
            error_msg = str(e)
            raise APIException(ErrorCode.EXTRACT_ERROR, msg=f"提取处理失败: {error_msg}")
