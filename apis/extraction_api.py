from flask import Blueprint, request
from flask_restx import Api, Resource, fields
from app.services.extraction_service import ExtractionService
import json
import os
import tempfile
import io
from common import log_
from common.error_codes import APIException, ErrorCode, FileError, ExtractionError, ParameterError
from common.minio_utils import download_and_process_minio_file
from flask_cors import CORS
import time
import re
import urllib.parse
import requests

# 创建Blueprint
extraction_api_bp = Blueprint('extraction_api', __name__, url_prefix='/api/v1')

# 在Blueprint创建后应用CORS
CORS(extraction_api_bp)

# 在Blueprint上初始化API，添加Swagger UI支持
api = Api(extraction_api_bp, 
    version='1.0', 
    title='文本提取API',
    description='基于AI的结构化信息提取API',
    doc='/docs'
)

# 创建命名空间
ns = api.namespace('', description='文本提取操作')

# 直接在API文件中定义模型
def create_base_response_model(api):
    """基础响应对象"""
    return api.model('BaseResponse', {
        'code': fields.String(description='业务状态码', example=ErrorCode.SUCCESS.code),
        'message': fields.String(description='提示信息', example=ErrorCode.SUCCESS.message),
        'data': fields.Raw(description='返回的数据'),
    })

# 定义提取请求模型
extract_request_model = api.model('ExtractRequest', {
    'file_url': fields.String(
        required=True, 
        description='MinIO文件URL链接',
        example='http://minio-server:9000/documents/example.pdf'
    ),
    'schema': fields.String(
        required=True, 
        description='JSON结构模板',
        example='{"name":"","email":""}'
    )
})

# 服务实例
extraction_service = ExtractionService()

@ns.route('/extract')
class Extract(Resource):
    @ns.doc('extract_content')
    @ns.expect(extract_request_model)
    @ns.response(200, '提取成功', create_base_response_model(api))
    def post(self):
        """
        从MinIO文件链接中提取结构化信息
        
        接收MinIO文件URL和JSON结构模板，从文件内容中提取结构化信息。
        支持多种文件格式：PDF、图片、Word文档、文本文件等。
        """
        try:
            # 解析请求数据
            data = self._parse_request_data()
            
            # 验证必要参数
            file_url = data.get('file_url')
            schema = data.get('schema')
            
            if not file_url:
                raise ParameterError(msg='请提供文件URL')
            
            if not schema:
                raise ParameterError(msg='请提供JSON结构模板')
            
            # 检查schema是否为有效的JSON
            try:
                json.loads(schema)
            except json.JSONDecodeError:
                raise ParameterError(msg='提供的schema不是有效的JSON格式')
            
            # 使用工具函数下载并处理文件
            try:
                from common.minio_utils import download_and_process_minio_file
                
                # 使用统一的处理方法
                result, status_code = download_and_process_minio_file(
                    file_url,
                    extraction_service.process_file,
                    schema=schema
                )
                
            except Exception as e:
                log_.error(f"文件处理失败: {str(e)}")
                raise FileError(ErrorCode.FILE_PROCESS_ERROR, msg=f'文件处理失败: {str(e)}')
            
            # 处理结果
            if status_code == 200:
                return self._format_successful_result(result, schema)
            else:
                raise ExtractionError(msg="处理失败")
                
        except APIException as e:
            # 已经是APIException，直接返回
            return e.to_dict(), 200
        except Exception as e:
            # 其他异常，包装为APIException
            log_.error(f"内容提取失败: {str(e)}")
            error = ExtractionError(msg=f'内容提取失败: {str(e)}')
            return error.to_dict(), 200
            
    def _parse_request_data(self):
        """解析请求数据，支持多种格式"""
        # 尝试多种方式获取数据
        data = None
        
        # 1. 尝试JSON格式
        if request.is_json:
            data = request.json
        # 2. 尝试表单数据
        elif request.form:
            data = {k: v for k, v in request.form.items()}
        
        # 如果仍然没有数据，检查请求体
        if not data and request.data:
            try:
                data = json.loads(request.data)
            except json.JSONDecodeError:
                pass
        
        if not data:
            raise ParameterError(msg='无法解析请求数据，请提供正确格式的JSON请求体')
        
        return data
        
    def _format_successful_result(self, result, schema):
        """格式化成功的结果"""
        try:
            # 如果result已经是dict，直接使用
            if isinstance(result, dict):
                return {'code': ErrorCode.SUCCESS.code, 'message': '操作成功', 'data': result}, 200
            # 如果result是JSON字符串，解析它
            result_dict = json.loads(result)
            return {'code': ErrorCode.SUCCESS.code, 'message': '操作成功', 'data': result_dict}, 200
        except (json.JSONDecodeError, TypeError):
            # 如果解析失败，返回空的schema结构
            empty_schema = json.loads(schema)
            for key in empty_schema:
                if isinstance(empty_schema[key], str):
                    empty_schema[key] = ""
                elif isinstance(empty_schema[key], (int, float)):
                    empty_schema[key] = 0
                elif isinstance(empty_schema[key], list):
                    empty_schema[key] = []
            return {'code': ErrorCode.SUCCESS.code, 'message': '操作成功', 'data': empty_schema}, 200
