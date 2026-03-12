"""
模板服务 - 处理模板文件管理
"""
import os
import uuid
import tempfile
from werkzeug.utils import secure_filename
from datetime import datetime
from common import log_
from common.minio_client import MinioClient
from app.entity.template import Template
from app.dao.template_dao import TemplateDAO
from common.error_codes import APIException, ErrorCode

class TemplateService:
    """模板服务类"""
    
    def __init__(self):
        """初始化模板服务"""
        self.minio_client = MinioClient.get_instance()
        self.template_dao = TemplateDAO()
        self.allowed_extensions = {'doc', 'docx', 'pdf'}
    
    def _is_allowed_file(self, filename):
        """检查文件类型是否允许上传"""
        try:
            ext = os.path.splitext(filename)[1].lower().lstrip('.')
            return ext in self.allowed_extensions
        except Exception:
            return False
    
    def get_templates(self, user_id, tag=None, keyword=None, limit=100, offset=0):
        """获取用户模板列表"""
        try:
            templates = self.template_dao.find_all_by_user(user_id, tag, keyword, limit, offset)
            for template in templates:
                if template.get('minio_path'):
                    template['url'] = self.minio_client.get_presigned_url(template['minio_path'])
            return templates
        except Exception as e:
            log_.error(f"获取模板列表失败: {str(e)}")
            raise APIException(ErrorCode.SYSTEM_ERROR, msg=f"获取模板列表失败: {str(e)}")
    
    def get_template_detail(self, template_id, user_id):
        """获取模板详情"""
        try:
            template = self.template_dao.select_one({'id': template_id, 'created_by': user_id})
            if not template:
                raise FileNotFoundError("模板不存在")
            template_dict = template.to_dict()
            if template_dict.get('minio_path'):
                template_dict['url'] = self.minio_client.get_presigned_url(template_dict['minio_path'])
            return template_dict
        except FileNotFoundError:
            raise
        except Exception as e:
            log_.error(f"获取模板详情失败: {str(e)}")
            raise APIException(ErrorCode.SYSTEM_ERROR, msg=f"获取模板详情失败: {str(e)}")
    
    def upload_template(self, file, name, tag, user_id):
        """上传模板文件"""
        temp_file_path = None
        try:
            if not hasattr(file, 'filename') or not file.filename:
                raise APIException(ErrorCode.VALIDATION_ERROR, msg="文件名不能为空")
            
            original_filename = file.filename
            if not self._is_allowed_file(original_filename):
                raise APIException(ErrorCode.VALIDATION_ERROR, msg="不支持的文件类型，仅支持Word和PDF")
            
            file_ext = os.path.splitext(original_filename)[1]
            file_type = file_ext.lower().lstrip('.')
            
            temp_dir = os.path.abspath("./data/temp")
            os.makedirs(temp_dir, exist_ok=True)
            unique_filename = f"{uuid.uuid4().hex}{file_ext}"
            temp_file_path = os.path.join(temp_dir, unique_filename)
            
            file.save(temp_file_path)
            
            if not os.path.exists(temp_file_path):
                raise IOError("保存临时文件失败")
            
            file_size = os.path.getsize(temp_file_path)
            if file_size == 0:
                os.remove(temp_file_path)
                raise APIException(ErrorCode.VALIDATION_ERROR, msg="文件为空")
            
            minio_path = f"templates/{user_id}/{unique_filename}"
            self.minio_client.upload_file(file_path=temp_file_path, object_name=minio_path)
            
            template = Template(
                name=name or original_filename,
                tag=tag or 'other',
                file_type=file_type,
                minio_path=minio_path,
                file_size=file_size,
                created_by=user_id
            )
            
            result = self.template_dao.create(template)
            
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            
            return result
        except APIException:
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            raise
        except Exception as e:
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            log_.error(f"上传模板失败: {str(e)}")
            raise APIException(ErrorCode.SYSTEM_ERROR, msg=f"上传模板失败: {str(e)}")
    
    def delete_template(self, template_id, user_id):
        """删除模板"""
        try:
            template = self.template_dao.select_one({'id': template_id, 'created_by': user_id})
            if not template:
                raise FileNotFoundError("模板不存在")
            
            template_dict = template.to_dict()
            if template_dict.get('minio_path'):
                self.minio_client.delete_file(template_dict['minio_path'])
            
            result = self.template_dao.delete(template_id, user_id)
            if not result:
                raise Exception("删除数据库记录失败")
            
            return True
        except FileNotFoundError:
            raise
        except Exception as e:
            log_.error(f"删除模板失败: {str(e)}")
            raise APIException(ErrorCode.SYSTEM_ERROR, msg=f"删除模板失败: {str(e)}")
