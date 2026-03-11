"""
文件控制器 - 处理文件预览和下载
"""
from app.controllers.base import BaseResource
from common.minio_client import MinioClient
from app.dao.knowledge_dao import DocumentDAO
from common import log_
from app.core.decorators import api_exception_handler, login_required
from common.error_codes import APIException, ErrorCode, ResourceNotFound
from flask import request, g, send_file, Response
import io


class FileController(BaseResource):
    """文件控制器 - 处理文件相关请求"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.minio_client = MinioClient()
        self.document_dao = DocumentDAO()
    
    @api_exception_handler
    @login_required
    def get(self, document_id=None):
        """获取文件预览URL或下载文件
        
        Args:
            document_id: 文档ID
        """
        if not document_id:
            return {
                "code": "PARAM_ERROR",
                "message": "请提供文档ID",
                "data": None
            }, 400
        
        try:
            # 获取文档信息
            document = self.document_dao.get_document_by_id(document_id)
            if not document:
                return {
                    "code": "RESOURCE_NOT_FOUND",
                    "message": "文档不存在",
                    "data": None
                }, 404
            
            # 检查权限（可选：验证用户是否有权访问此文件）
            user_id = g.user_id
            if document.get('uploaded_by') and document['uploaded_by'] != user_id:
                log_.warning(f"用户 {user_id} 尝试访问其他用户的文件 {document_id}")
                # 这里可以根据业务需求决定是否允许访问
                # 如果要严格控制，可以返回403错误
            
            # 获取MinIO路径
            minio_path = document.get('minio_path')
            if not minio_path:
                return {
                    "code": "FILE_NOT_FOUND",
                    "message": "文件路径不存在",
                    "data": None
                }, 404
            
            # 检查是否需要下载（query参数）
            download = request.args.get('download', 'false').lower() == 'true'
            
            if download:
                # 直接下载文件
                file_content = self.minio_client.download_file(minio_path)
                return send_file(
                    io.BytesIO(file_content),
                    download_name=document.get('filename', 'file'),
                    as_attachment=True
                )
            else:
                # 返回预览URL（生成临时访问URL）
                preview_url = self.minio_client.get_presigned_url(minio_path, expires=3600)  # 1小时有效期
                
                return {
                    "code": "SUCCESS",
                    "message": "获取文件预览URL成功",
                    "data": {
                        "document_id": document_id,
                        "filename": document.get('filename'),
                        "file_type": document.get('file_type'),
                        "file_size": document.get('file_size'),
                        "preview_url": preview_url,
                        "download_url": f"/api/llm/files/{document_id}?download=true"
                    }
                }, 200
        except Exception as e:
            log_.error(f"获取文件失败: {str(e)}")
            return {
                "code": "SYSTEM_ERROR",
                "message": f"获取文件失败: {str(e)}",
                "data": None
            }, 500
