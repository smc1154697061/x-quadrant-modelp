"""
模板文档数据访问对象
"""
from typing import List, Optional
from app.dao.mapper import BaseMapper
from app.entity.template import DocumentTemplate, GeneratedDocument
from common.db_utils import get_db_connection
from common import log_
from common.error_codes import APIException, ErrorCode


class DocumentTemplateDAO(BaseMapper):
    """文档模板Mapper"""
    
    entity_class = DocumentTemplate
    table_name = 'dodo_document_templates'
    primary_key = 'id'
    
    @classmethod
    def find_by_id(cls, template_id):
        """通过ID查找模板"""
        try:
            mapper = cls()
            template = mapper.select_by_id(template_id)
            return template.to_dict() if template else None
        except Exception as e:
            log_.error(f"查找模板失败: {str(e)}")
            return None
    
    @classmethod
    def find_by_user_id(cls, user_id, include_public=True):
        """查找用户的所有模板"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    if include_public:
                        sql = """
                            SELECT * FROM dodo_document_templates 
                            WHERE created_by = %s OR is_public = true 
                            ORDER BY created_at DESC
                        """
                        cursor.execute(sql, (int(user_id),))
                    else:
                        sql = """
                            SELECT * FROM dodo_document_templates 
                            WHERE created_by = %s 
                            ORDER BY created_at DESC
                        """
                        cursor.execute(sql, (int(user_id),))
                    
                    columns = [desc[0] for desc in cursor.description]
                    results = []
                    for row in cursor.fetchall():
                        row_dict = dict(zip(columns, row))
                        template = DocumentTemplate.from_dict(row_dict)
                        results.append(template.to_dict())
                    return results
        except Exception as e:
            log_.error(f"查找用户模板列表失败: {str(e)}")
            return []
    
    @classmethod
    def find_by_category(cls, category, user_id=None):
        """按分类查找模板"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    if user_id:
                        sql = """
                            SELECT * FROM dodo_document_templates 
                            WHERE category = %s AND (created_by = %s OR is_public = true)
                            ORDER BY created_at DESC
                        """
                        cursor.execute(sql, (category, int(user_id)))
                    else:
                        sql = """
                            SELECT * FROM dodo_document_templates 
                            WHERE category = %s AND is_public = true
                            ORDER BY created_at DESC
                        """
                        cursor.execute(sql, (category,))
                    
                    columns = [desc[0] for desc in cursor.description]
                    results = []
                    for row in cursor.fetchall():
                        row_dict = dict(zip(columns, row))
                        template = DocumentTemplate.from_dict(row_dict)
                        results.append(template.to_dict())
                    return results
        except Exception as e:
            log_.error(f"按分类查找模板失败: {str(e)}")
            return []
    
    @classmethod
    def search_templates(cls, keyword, user_id=None):
        """搜索模板"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    search_pattern = f"%{keyword}%"
                    if user_id:
                        sql = """
                            SELECT * FROM dodo_document_templates 
                            WHERE (name ILIKE %s OR description ILIKE %s)
                            AND (created_by = %s OR is_public = true)
                            ORDER BY created_at DESC
                        """
                        cursor.execute(sql, (search_pattern, search_pattern, int(user_id)))
                    else:
                        sql = """
                            SELECT * FROM dodo_document_templates 
                            WHERE (name ILIKE %s OR description ILIKE %s)
                            AND is_public = true
                            ORDER BY created_at DESC
                        """
                        cursor.execute(sql, (search_pattern, search_pattern))
                    
                    columns = [desc[0] for desc in cursor.description]
                    results = []
                    for row in cursor.fetchall():
                        row_dict = dict(zip(columns, row))
                        template = DocumentTemplate.from_dict(row_dict)
                        results.append(template.to_dict())
                    return results
        except Exception as e:
            log_.error(f"搜索模板失败: {str(e)}")
            return []
    
    @classmethod
    def get_all_categories(cls, user_id=None):
        """获取所有分类"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    if user_id:
                        sql = """
                            SELECT DISTINCT category FROM dodo_document_templates 
                            WHERE created_by = %s OR is_public = true
                            ORDER BY category
                        """
                        cursor.execute(sql, (int(user_id),))
                    else:
                        sql = """
                            SELECT DISTINCT category FROM dodo_document_templates 
                            WHERE is_public = true
                            ORDER BY category
                        """
                        cursor.execute(sql)
                    
                    return [row[0] for row in cursor.fetchall() if row[0]]
        except Exception as e:
            log_.error(f"获取分类列表失败: {str(e)}")
            return []
    
    @classmethod
    def create(cls, template: DocumentTemplate):
        """创建模板"""
        try:
            if template.created_by is not None:
                template.created_by = int(template.created_by)
            
            mapper = cls()
            template_id = mapper.insert(template)
            template.id = template_id
            return template.to_dict()
        except Exception as e:
            log_.error(f"创建模板失败: {str(e)}")
            raise APIException(ErrorCode.DATABASE_ERROR, msg=f"创建模板失败: {str(e)}")
    
    @classmethod
    def delete(cls, template_id):
        """删除模板"""
        try:
            mapper = cls()
            result = mapper.delete_by_id(template_id)
            return result > 0
        except Exception as e:
            log_.error(f"删除模板失败: {str(e)}")
            raise APIException(ErrorCode.DATABASE_ERROR, msg=f"删除模板失败: {str(e)}")


class GeneratedDocumentDAO(BaseMapper):
    """生成文档Mapper"""
    
    entity_class = GeneratedDocument
    table_name = 'dodo_generated_documents'
    primary_key = 'id'
    
    @classmethod
    def find_by_id(cls, doc_id):
        """通过ID查找生成文档"""
        try:
            mapper = cls()
            doc = mapper.select_by_id(doc_id)
            return doc.to_dict() if doc else None
        except Exception as e:
            log_.error(f"查找生成文档失败: {str(e)}")
            return None
    
    @classmethod
    def find_by_user_id(cls, user_id, limit=20):
        """查找用户的生成文档历史"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    sql = """
                        SELECT * FROM dodo_generated_documents 
                        WHERE created_by = %s
                        ORDER BY created_at DESC
                        LIMIT %s
                    """
                    cursor.execute(sql, (int(user_id), limit))
                    
                    columns = [desc[0] for desc in cursor.description]
                    results = []
                    for row in cursor.fetchall():
                        row_dict = dict(zip(columns, row))
                        doc = GeneratedDocument.from_dict(row_dict)
                        results.append(doc.to_dict())
                    return results
        except Exception as e:
            log_.error(f"查找生成文档历史失败: {str(e)}")
            return []
    
    @classmethod
    def create(cls, doc: GeneratedDocument):
        """创建生成文档记录"""
        try:
            if doc.created_by is not None:
                doc.created_by = int(doc.created_by)
            if doc.template_id is not None:
                doc.template_id = int(doc.template_id)
            
            mapper = cls()
            doc_id = mapper.insert(doc)
            doc.id = doc_id
            return doc.to_dict()
        except Exception as e:
            log_.error(f"创建生成文档记录失败: {str(e)}")
            raise APIException(ErrorCode.DATABASE_ERROR, msg=f"创建生成文档记录失败: {str(e)}")
    
    @classmethod
    def delete(cls, doc_id):
        """删除生成文档记录"""
        try:
            mapper = cls()
            result = mapper.delete_by_id(doc_id)
            return result > 0
        except Exception as e:
            log_.error(f"删除生成文档记录失败: {str(e)}")
            raise APIException(ErrorCode.DATABASE_ERROR, msg=f"删除生成文档记录失败: {str(e)}")
