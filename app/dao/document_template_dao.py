"""
文档模板数据访问对象
"""
from app.dao.base_dao import BaseDAO
from app.entity.document_template import DocumentTemplate, TemplateGeneration


class DocumentTemplateDao(BaseDAO):
    """文档模板DAO"""
    
    def __init__(self):
        super().__init__()
    
    def insert(self, template):
        """
        插入模板记录
        
        Args:
            template: DocumentTemplate对象
            
        Returns:
            int: 新插入记录的ID
        """
        sql = """
            INSERT INTO dodo_document_templates 
            (name, tags, file_type, file_size, minio_path, created_by, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            RETURNING id
        """
        params = [
            template.name,
            template.tags,
            template.file_type,
            template.file_size,
            template.minio_path,
            template.created_by
        ]
        return BaseDAO.execute_insert_returning(sql, params)
    
    def find_by_user(self, user_id, tag=None, search=None):
        """
        根据用户ID查询模板列表
        
        Args:
            user_id: 用户ID
            tag: 标签筛选
            search: 搜索关键词
        
        Returns:
            list: 模板列表
        """
        sql = "SELECT * FROM dodo_document_templates WHERE created_by = %s"
        params = [user_id]
        
        if tag:
            sql += " AND tags LIKE %s"
            params.append(f'%{tag}%')
        
        if search:
            sql += " AND name LIKE %s"
            params.append(f'%{search}%')
        
        sql += " ORDER BY created_at DESC"
        
        return self.execute_query(sql, params)
    
    def find_by_id_and_user(self, template_id, user_id):
        """
        根据ID和用户ID查询模板
        
        Args:
            template_id: 模板ID
            user_id: 用户ID
        
        Returns:
            DocumentTemplate: 模板对象或None
        """
        sql = "SELECT * FROM dodo_document_templates WHERE id = %s AND created_by = %s"
        results = self.execute_query(sql, [template_id, user_id])
        return results[0] if results else None
    
    def delete_by_id_and_user(self, template_id, user_id):
        """
        根据ID和用户ID删除模板
        
        Args:
            template_id: 模板ID
            user_id: 用户ID
        
        Returns:
            bool: 是否删除成功
        """
        sql = "DELETE FROM dodo_document_templates WHERE id = %s AND created_by = %s"
        result = self.execute_update(sql, [template_id, user_id])
        return result > 0


class TemplateGenerationDao(BaseDAO):
    """模板生成记录DAO"""
    
    def __init__(self):
        super().__init__()
    
    def insert(self, generation):
        """
        插入生成记录
        
        Args:
            generation: TemplateGeneration对象
            
        Returns:
            int: 新插入记录的ID
        """
        sql = """
            INSERT INTO dodo_template_generations 
            (template_id, user_id, user_input, generated_content, output_file_path, output_file_type, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            RETURNING id
        """
        params = [
            generation.template_id,
            generation.user_id,
            generation.user_input,
            generation.generated_content,
            generation.output_file_path,
            generation.output_file_type,
            generation.status
        ]
        return BaseDAO.execute_insert_returning(sql, params)
    
    def find_by_user(self, user_id, page=1, page_size=20):
        """
        根据用户ID查询生成记录列表
        
        Args:
            user_id: 用户ID
            page: 页码
            page_size: 每页数量
        
        Returns:
            list: 生成记录列表
        """
        offset = (page - 1) * page_size
        sql = """
            SELECT g.*, t.name as template_name, t.tags as template_tags
            FROM dodo_template_generations g
            LEFT JOIN dodo_document_templates t ON g.template_id = t.id
            WHERE g.user_id = %s
            ORDER BY g.created_at DESC
            LIMIT %s OFFSET %s
        """
        return self.execute_query(sql, [user_id, page_size, offset])
    
    def count_by_user(self, user_id):
        """
        统计用户的生成记录数量
        
        Args:
            user_id: 用户ID
        
        Returns:
            int: 记录数量
        """
        sql = "SELECT COUNT(*) as count FROM dodo_template_generations WHERE user_id = %s"
        result = self.execute_query(sql, [user_id])
        return result[0]['count'] if result else 0
    
    def find_by_id_and_user(self, generation_id, user_id):
        """
        根据ID和用户ID查询生成记录
        
        Args:
            generation_id: 生成记录ID
            user_id: 用户ID
        
        Returns:
            TemplateGeneration: 生成记录对象或None
        """
        sql = """
            SELECT g.*, t.name as template_name, t.tags as template_tags
            FROM dodo_template_generations g
            LEFT JOIN dodo_document_templates t ON g.template_id = t.id
            WHERE g.id = %s AND g.user_id = %s
        """
        results = self.execute_query(sql, [generation_id, user_id])
        return results[0] if results else None
    
    def update_status(self, generation_id, status, generated_content=None, output_file_path=None, output_file_type=None):
        """
        更新生成记录状态
        
        Args:
            generation_id: 生成记录ID
            status: 状态
            generated_content: 生成的内容
            output_file_path: 输出文件路径
            output_file_type: 输出文件类型
        
        Returns:
            bool: 是否更新成功
        """
        fields = ["status = %s"]
        params = [status]
        
        if generated_content is not None:
            fields.append("generated_content = %s")
            params.append(generated_content)
        
        if output_file_path is not None:
            fields.append("output_file_path = %s")
            params.append(output_file_path)
        
        if output_file_type is not None:
            fields.append("output_file_type = %s")
            params.append(output_file_type)
        
        params.append(generation_id)
        
        sql = f"UPDATE dodo_template_generations SET {', '.join(fields)} WHERE id = %s"
        result = self.execute_update(sql, params)
        return result > 0
