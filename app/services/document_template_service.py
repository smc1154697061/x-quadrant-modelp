"""
文档模板服务
"""
import os
import uuid
from datetime import datetime
from common import log_
from common.minio_client import MinioClient
from app.dao.document_template_dao import DocumentTemplateDao, TemplateGenerationDao
from app.entity.document_template import DocumentTemplate, TemplateGeneration
from app.models.llm.model_factory import get_llm_model
from app.utils.document_loader import DocumentLoader


class DocumentTemplateService:
    """文档模板服务类"""
    
    def __init__(self):
        self.template_dao = DocumentTemplateDao()
        self.generation_dao = TemplateGenerationDao()
        self.minio_client = MinioClient()
        self.document_loader = DocumentLoader()
    
    def upload_template(self, user_id, file_path, file_name, tags, file_size):
        """
        上传文档模板
        
        Args:
            user_id: 用户ID
            file_path: 本地文件路径
            file_name: 文件名
            tags: 标签
            file_size: 文件大小
        
        Returns:
            dict: 上传结果
        """
        try:
            # 确定文件类型
            file_ext = os.path.splitext(file_name)[1].lower()
            if file_ext in ['.doc', '.docx']:
                file_type = 'word'
            elif file_ext == '.pdf':
                file_type = 'pdf'
            else:
                return {'success': False, 'message': '不支持的文件格式，仅支持Word和PDF'}
            
            # 生成MinIO存储路径
            object_name = f"templates/{user_id}/{uuid.uuid4()}{file_ext}"
            
            # 上传到MinIO
            self.minio_client.upload_file(file_path, object_name)
            
            # 保存到数据库
            template = DocumentTemplate(
                name=file_name,
                tags=tags,
                file_type=file_type,
                file_size=file_size,
                minio_path=object_name,
                created_by=user_id
            )
            template_id = self.template_dao.insert(template)
            
            return {
                'success': True,
                'template_id': template_id,
                'message': '上传成功'
            }
        
        except Exception as e:
            log_.error(f"上传模板失败: {str(e)}")
            return {'success': False, 'message': f'上传失败: {str(e)}'}
    
    def get_template_list(self, user_id, tag=None, search=None):
        """
        获取模板列表
        
        Args:
            user_id: 用户ID
            tag: 标签筛选
            search: 搜索关键词
        
        Returns:
            list: 模板列表
        """
        templates = self.template_dao.find_by_user(user_id, tag, search)
        return templates
    
    def get_template_detail(self, template_id, user_id):
        """
        获取模板详情
        
        Args:
            template_id: 模板ID
            user_id: 用户ID
        
        Returns:
            dict: 模板详情
        """
        template = self.template_dao.find_by_id_and_user(template_id, user_id)
        return template
    
    def delete_template(self, template_id, user_id):
        """
        删除模板
        
        Args:
            template_id: 模板ID
            user_id: 用户ID
        
        Returns:
            dict: 删除结果
        """
        try:
            # 获取模板信息
            template = self.template_dao.find_by_id_and_user(template_id, user_id)
            if not template:
                return {'success': False, 'message': '模板不存在或无权限'}
            
            # 删除MinIO文件
            try:
                self.minio_client.delete_file(template['minio_path'])
            except Exception as e:
                log_.warning(f"删除MinIO文件失败: {str(e)}")
            
            # 删除数据库记录
            success = self.template_dao.delete_by_id_and_user(template_id, user_id)
            
            if success:
                return {'success': True, 'message': '删除成功'}
            else:
                return {'success': False, 'message': '删除失败'}
        
        except Exception as e:
            log_.error(f"删除模板失败: {str(e)}")
            return {'success': False, 'message': f'删除失败: {str(e)}'}
    
    def generate_document(self, user_id, template_id, user_input):
        """
        生成文档
        
        Args:
            user_id: 用户ID
            template_id: 模板ID
            user_input: 用户输入的个人信息
        
        Returns:
            dict: 生成结果
        """
        try:
            # 获取模板信息
            template = self.template_dao.find_by_id_and_user(template_id, user_id)
            if not template:
                return {'success': False, 'message': '模板不存在或无权限'}
            
            # 创建生成记录
            generation = TemplateGeneration(
                template_id=template_id,
                user_id=user_id,
                user_input=user_input,
                status='generating'
            )
            generation_id = self.generation_dao.insert(generation)
            
            # 下载模板文件
            local_template_path = f"/tmp/{uuid.uuid4()}_{template['name']}"
            self.minio_client.download_file(template['minio_path'], local_template_path)
            
            # 读取模板内容
            template_content = self.document_loader.load(local_template_path)
            
            # 清理临时文件
            try:
                os.remove(local_template_path)
            except:
                pass
            
            # 调用LLM生成文档
            llm = get_llm_model()
            
            prompt = f"""你是一个专业的文档生成助手。请根据以下模板格式和用户信息，生成一份完整的文档。

模板格式参考：
{template_content}

用户提供的信息：
{user_input}

要求：
1. 严格按照模板的格式和结构生成文档
2. 将用户提供的信息填充到模板相应位置
3. 保持专业、正式的文档风格
4. 如果用户信息不完整，请合理补充或标注待填写
5. 直接输出文档内容，不要包含解释说明

请生成完整的文档内容："""
            
            generated_content = llm.invoke(prompt)
            
            # 更新生成记录
            self.generation_dao.update_status(
                generation_id,
                'completed',
                generated_content=generated_content
            )
            
            return {
                'success': True,
                'generation_id': generation_id,
                'content': generated_content,
                'message': '生成成功'
            }
        
        except Exception as e:
            log_.error(f"生成文档失败: {str(e)}")
            # 更新失败状态
            if 'generation_id' in locals():
                self.generation_dao.update_status(generation_id, 'failed')
            return {'success': False, 'message': f'生成失败: {str(e)}'}
    
    def get_generation_history(self, user_id, page=1, page_size=20):
        """
        获取生成历史
        
        Args:
            user_id: 用户ID
            page: 页码
            page_size: 每页数量
        
        Returns:
            dict: 历史记录和总数
        """
        history = self.generation_dao.find_by_user(user_id, page, page_size)
        total = self.generation_dao.count_by_user(user_id)
        
        return {
            'list': history,
            'total': total,
            'page': page,
            'page_size': page_size
        }
    
    def get_generation_detail(self, generation_id, user_id):
        """
        获取生成记录详情
        
        Args:
            generation_id: 生成记录ID
            user_id: 用户ID
        
        Returns:
            dict: 生成记录详情
        """
        generation = self.generation_dao.find_by_id_and_user(generation_id, user_id)
        return generation
    
    def get_template_file_url(self, template_id, user_id):
        """
        获取模板文件下载URL
        
        Args:
            template_id: 模板ID
            user_id: 用户ID
        
        Returns:
            str: 下载URL
        """
        template = self.template_dao.find_by_id_and_user(template_id, user_id)
        if not template:
            return None
        
        return self.minio_client.get_presigned_url(template['minio_path'])
