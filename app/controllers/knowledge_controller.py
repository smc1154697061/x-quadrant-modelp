import os
import json
import uuid
import shutil
import time
from datetime import datetime
from app.controllers.base import BaseResource
from flask import request, g, send_file
from app.services.knowledge_service import KnowledgeService
from app.entity.dto.knowledge_dto import KnowledgeBaseCreateDTO
from common import log_
from app.core.decorators import api_exception_handler, login_required, login_optional
from common.error_codes import APIException, ErrorCode, ParameterError, ResourceNotFound
from app.dao.knowledge_dao import KnowledgeBaseDAO

class KnowledgeBaseController(BaseResource):
    """知识库控制器 - 处理知识库的CRUD操作"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.knowledge_service = KnowledgeService()
    
    @api_exception_handler
    @login_optional
    def get(self, kb_id=None):
        """获取知识库列表或单个知识库详情"""
        user_id = getattr(g, 'user_id', None)
        
        if kb_id:
            # 检查是否需要包含文档
            include_docs = request.args.get('include_docs', 'true').lower() == 'true'
            
            if include_docs:
                kb = self.knowledge_service.get_knowledge_base(kb_id)
            else:
                # 不包含文档的轻量版详情
                kb = self.knowledge_service.get_knowledge_base_without_docs(kb_id)
            
            return {
                "code": ErrorCode.SUCCESS.code,
                "message": ErrorCode.SUCCESS.message,
                "data": kb
            }, 200
        else:
            # 获取知识库列表（带文件计数）
            kb_list = self.knowledge_service.get_knowledge_bases_with_count(user_id)
            return {
                "code": ErrorCode.SUCCESS.code,
                "message": ErrorCode.SUCCESS.message,
                "data": kb_list
            }, 200
    
    @api_exception_handler
    @login_required
    def post(self):
        """创建新的知识库（Java风格）"""
        # 1. 接收请求转为DTO
        data = self.get_params()
        dto = KnowledgeBaseCreateDTO.from_request(data)
        
        # 2. DTO校验
        dto.validate()
        
        # 3. 调用Service
        kb = self.knowledge_service.create_knowledge_base(dto, user_id=g.user_id)
        
        # 4. 返回VO
        return {
            "code": ErrorCode.SUCCESS.code,
            "message": "知识库创建成功",
            "data": kb
        }, 200
    
    @api_exception_handler
    @login_required
    def delete(self, kb_id):
        """删除知识库"""
        try:
            # 检查知识库是否被机器人使用
            if self.knowledge_service.is_knowledge_base_used_by_bot(kb_id):
                return {
                    "code": ErrorCode.VALIDATION_ERROR.code,
                    "message": "该知识库已被机器人使用，无法删除",
                    "data": None
                }, 400
            
            # 执行删除操作
            self.knowledge_service.delete_knowledge_base(kb_id)
            
            return {
                "code": ErrorCode.SUCCESS.code,
                "message": "知识库删除成功",
                "data": None
            }, 200
        except FileNotFoundError:
            return {
                "code": ErrorCode.RESOURCE_NOT_FOUND.code,
                "message": "知识库不存在",
                "data": None
            }, 404
        except APIException as e:
            return {
                "code": e.code,
                "message": e.message,
                "data": None
            }, 400
        except Exception as e:
            log_.error(f"删除知识库失败: {str(e)}")
            return {
                "code": ErrorCode.SYSTEM_ERROR.code,
                "message": f"删除知识库失败: {str(e)}",
                "data": None
            }, 500
    
    @api_exception_handler
    @login_required
    def put(self, kb_id=None):
        """更新知识库"""
        if not kb_id:
            return {
                "code": ErrorCode.VALIDATION_ERROR.code,
                "message": "缺少知识库ID",
                "data": None
            }, 400
        
        from app.entity.dto.knowledge_dto import KnowledgeBaseUpdateDTO
        
        data = self.get_params()
        dto = KnowledgeBaseUpdateDTO.from_request(data)
        dto.validate()
        
        kb = self.knowledge_service.update_knowledge_base(kb_id, dto)
        
        return {
            "code": ErrorCode.SUCCESS.code,
            "message": "知识库更新成功",
            "data": kb
        }, 200

    @api_exception_handler
    @login_optional
    def get_basic_knowledge_bases(self):
        """只获取知识库基本信息列表，不包含文档"""
        user_id = getattr(g, 'user_id', None)
        
        kb_list = KnowledgeBaseDAO().find_by_user_id(user_id, include_public=True) if user_id else KnowledgeBaseDAO().find_public_only()
        
        # 不添加文档信息
        return {
            "code": ErrorCode.SUCCESS.code,
            "message": ErrorCode.SUCCESS.message,
            "data": kb_list
        }, 200

class SimpleKnowledgeController(BaseResource):
    """简化版知识库控制器 - 处理文档上传和处理"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.knowledge_service = KnowledgeService()
    
    @api_exception_handler
    def get(self, document_id=None):
        """获取文档列表或单个文档详情"""
        try:
            # 检查请求路径
            if 'documents' in request.path and not document_id:
                # 获取所有文档列表
                documents = self.knowledge_service.get_documents()
                
                return {
                    "code": ErrorCode.SUCCESS.code,
                    "message": ErrorCode.SUCCESS.message,
                    "data": documents
                }, 200
            elif document_id:
                # 获取单个文档详情
                document = self.knowledge_service.get_document(document_id)
                return {
                    "code": ErrorCode.SUCCESS.code,
                    "message": ErrorCode.SUCCESS.message,
                    "data": document
                }, 200
            else:
                # 请求路径不匹配
                log_.error(f"不支持的请求路径: {request.path}")
                return {
                    "code": ErrorCode.VALIDATION_ERROR.code,
                    "message": "不支持的请求",
                    "data": None
                }, 400
        except FileNotFoundError as e:
            log_.error(f"文档不存在: {str(e)}")
            return {
                "code": ErrorCode.RESOURCE_NOT_FOUND.code,
                "message": "文档不存在",
                "data": None
            }, 404
        except APIException as e:
            log_.error(f"API异常: {e.code} - {e.message}")
            return {
                "code": e.code,
                "message": e.message,
                "data": None
            }, 400
        except Exception as e:
            log_.error(f"获取文档信息失败: {str(e)}", exc_info=True)
            return {
                "code": ErrorCode.SYSTEM_ERROR.code,
                "message": f"获取文档信息失败: {str(e)}",
                "data": None
            }, 500

    @api_exception_handler
    def post(self, document_id=None):
        """处理文件上传请求 - 无需用户登录"""
        try:
            # 检查请求是否包含文件
            if 'file' not in request.files:
                log_.error("请求中没有文件")
                return {
                    "code": ErrorCode.VALIDATION_ERROR.code,
                    "message": "没有文件上传",
                    "data": None
                }, 400
            
            file = request.files['file']
            
            if file.filename == '':
                log_.error("文件名为空")
                return {
                    "code": ErrorCode.VALIDATION_ERROR.code,
                    "message": "没有选择文件",
                    "data": None
                }, 400
                
            # 获取知识库ID参数
            kb_id = request.form.get('knowledge_base_id')
            
            if not kb_id:
                log_.error("未指定知识库ID")
                return {
                    "code": ErrorCode.VALIDATION_ERROR.code,
                    "message": "未指定知识库ID",
                    "data": None
                }, 400
            
            # 设置最大文件大小限制，例如100MB
            max_content_length = 100 * 1024 * 1024
            if request.content_length and request.content_length > max_content_length:
                log_.error(f"文件过大: {request.content_length} 字节")
                return {
                    "code": ErrorCode.VALIDATION_ERROR.code,
                    "message": "文件过大，最大允许100MB",
                    "data": None
                }, 400
            
            # 将文件添加到指定知识库
            result = self.knowledge_service.add_file_to_knowledge_base(kb_id, file)
            
            return {
                "code": ErrorCode.SUCCESS.code,
                "message": "文件上传成功",
                "data": result
            }, 200
        except FileNotFoundError as e:
            log_.error(f"知识库不存在: {str(e)}")
            return {
                "code": ErrorCode.RESOURCE_NOT_FOUND.code,
                "message": f"知识库不存在: {str(e)}",
                "data": None
            }, 404
        except APIException as e:
            log_.error(f"API异常: {e.code} - {e.message}")
            return {
                "code": e.code,
                "message": e.message,
                "data": None
            }, 400
        except Exception as e:
            log_.error(f"文件上传失败: {str(e)}", exc_info=True)
            return {
                "code": ErrorCode.FILE_UPLOAD_ERROR.code,
                "message": f"文件上传失败: {str(e)}",
                "data": None
            }, 500

    @api_exception_handler
    def delete(self, document_id):
        """删除文件 - 无需用户登录"""
        try:
            if not document_id:
                log_.error("未指定文档ID")
                return {
                    "code": ErrorCode.VALIDATION_ERROR.code,
                    "message": "未指定文档ID",
                    "data": None
                }, 400
                
            self.knowledge_service.delete_document(document_id)

            return {
                "code": ErrorCode.SUCCESS.code,
                "message": "文档删除成功",
                "data": None
            }, 200
        except FileNotFoundError as e:
            log_.error(f"文件不存在: {str(e)}")
            return {
                "code": ErrorCode.RESOURCE_NOT_FOUND.code,
                "message": "文件不存在",
                "data": None
            }, 404
        except APIException as e:
            log_.error(f"API异常: {e.code} - {e.message}")
            return {
                "code": e.code,
                "message": e.message,
                "data": None
            }, 400
        except Exception as e:
            log_.error(f"删除文档失败: {str(e)}", exc_info=True)
            return {
                "code": ErrorCode.SYSTEM_ERROR.code,
                "message": f"删除文档失败: {str(e)}",
                "data": None
            }, 500

    @api_exception_handler
    def put(self, document_id=None):
        """处理文档向量化请求"""
        try:
            if not document_id:
                log_.error("未指定文档ID")
                return {
                    "code": ErrorCode.VALIDATION_ERROR.code,
                    "message": "未指定文档ID",
                    "data": None
                }, 400
            
            # 调用服务层方法处理文档
            result = self.knowledge_service.process_document(document_id)

            return {
                "code": ErrorCode.SUCCESS.code,
                "message": "文档处理请求已发送",
                "data": result
            }, 200
        except FileNotFoundError as e:
            log_.error(f"文档不存在: {str(e)}")
            return {
                "code": ErrorCode.RESOURCE_NOT_FOUND.code,
                "message": "文档不存在",
                "data": None
            }, 404
        except APIException as e:
            log_.error(f"API异常: {e.code} - {e.message}")
            return {
                "code": e.code,
                "message": e.message,
                "data": None
            }, 400
        except Exception as e:
            log_.error(f"处理文档失败: {str(e)}", exc_info=True)
            return {
                "code": ErrorCode.SYSTEM_ERROR.code,
                "message": f"处理文档失败: {str(e)}",
                "data": None
            }, 500

class KnowledgeBaseFilesController(BaseResource):
    """知识库文件管理控制器"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.knowledge_service = KnowledgeService()
    
    @api_exception_handler
    def get(self, kb_id):
        """获取知识库的文件列表"""
        try:
            # 获取当前用户ID
            user_id = getattr(g, 'user_id', None)
            
            # 获取知识库信息，检查权限
            try:
                kb = self.knowledge_service.get_knowledge_base(kb_id)
                if not kb:
                    raise ResourceNotFound(msg='知识库不存在')
                
                # 检查权限：需要验证用户是否为创建者
                if not kb.get('is_public') and (not user_id or (user_id != kb.get('created_by'))):
                    raise APIException(ErrorCode.UNAUTHORIZED, msg="无权访问该知识库")
            except FileNotFoundError:
                raise ResourceNotFound(msg='知识库不存在')
            except Exception as e:
                log_.error(f"获取知识库信息失败: {str(e)}")
                raise APIException(ErrorCode.SYSTEM_ERROR, msg=f'获取知识库信息失败: {str(e)}')
            
            # 获取知识库中的文件列表
            try:
                documents = self.knowledge_service.get_documents(kb_id)
                
                return {
                    "code": ErrorCode.SUCCESS.code,
                    "message": ErrorCode.SUCCESS.message,
                    "data": documents
                }, 200
            except Exception as e:
                log_.error(f"获取知识库文件列表失败: {str(e)}")
                return {
                    "code": ErrorCode.SYSTEM_ERROR.code,
                    "message": f"获取知识库文件列表失败: {str(e)}",
                    "data": []
                }, 500
        except ResourceNotFound as e:
            log_.error(f"资源不存在: {str(e)}")
            return {
                "code": ErrorCode.RESOURCE_NOT_FOUND.code,
                "message": str(e),
                "data": None
            }, 404
        except APIException as e:
            log_.error(f"API异常: {e.code} - {e.message}")
            return {
                "code": e.code,
                "message": e.message,
                "data": None
            }, 400
        except Exception as e:
            log_.error(f"获取知识库文件列表失败: {str(e)}")
            return {
                "code": ErrorCode.SYSTEM_ERROR.code,
                "message": f"获取知识库文件列表失败: {str(e)}",
                "data": []
            }, 500

class KnowledgeBaseBasicController(BaseResource):
    """基本知识库控制器 - 只返回知识库基本信息，不包含文档"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.knowledge_service = KnowledgeService()
    
    @api_exception_handler
    @login_optional
    def get(self):
        """获取知识库基本信息列表"""
        # 获取用户ID（可能为None，表示未登录用户）
        user_id = getattr(g, 'user_id', None)
        
        # 返回知识库列表
        kb_list = self.knowledge_service.get_knowledge_bases_with_count(user_id)
        return {
            "code": ErrorCode.SUCCESS.code,
            "message": ErrorCode.SUCCESS.message,
            "data": kb_list
        }, 200