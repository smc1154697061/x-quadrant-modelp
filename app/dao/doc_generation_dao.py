from typing import Optional, List
from app.dao.mapper import BaseMapper
from app.entity.doc_generation import DocGeneration


class DocGenerationDAO(BaseMapper):
    """文档生成记录Mapper，继承BaseMapper获得通用CRUD"""
    
    entity_class = DocGeneration
    table_name = 'dodo_doc_generations'
    primary_key = 'id'
    
    def find_by_user(self, user_id: int, limit: int = 100, offset: int = 0) -> List[dict]:
        """通过用户ID查找文档生成记录"""
        results = self.select_list({'user_id': user_id}, order_by='created_at DESC', limit=limit, offset=offset)
        return [r.to_dict() for r in results]
    
    def find_by_id_and_user(self, record_id: int, user_id: int) -> Optional[dict]:
        """通过ID和用户ID查找文档生成记录"""
        result = self.select_one({'id': record_id, 'user_id': user_id})
        return result.to_dict() if result else None
    
    def create(self, doc_gen: DocGeneration):
        """创建新文档生成记录"""
        record_id = self.insert(doc_gen)
        doc_gen.id = record_id
        return doc_gen.to_dict()
    
    def update_status(self, record_id: int, status: str, user_id: int = None):
        """更新记录状态"""
        condition = {'id': record_id}
        if user_id:
            condition['user_id'] = user_id
        return self.update({'status': status}, condition) > 0
    
    def update_result(self, record_id: int, generated_content: str = None, 
                      word_minio_path: str = None, pdf_minio_path: str = None, status: str = None):
        """更新生成结果"""
        update_data = {}
        if generated_content is not None:
            update_data['generated_content'] = generated_content
        if word_minio_path is not None:
            update_data['word_minio_path'] = word_minio_path
        if pdf_minio_path is not None:
            update_data['pdf_minio_path'] = pdf_minio_path
        if status is not None:
            update_data['status'] = status
        
        return self.update(update_data, {'id': record_id}) > 0
    
    def find_all_by_user(self, user_id: int, limit: int = 100, offset: int = 0):
        """获取用户所有文档生成记录"""
        return self.find_by_user(user_id, limit, offset)
    
    def delete(self, record_id: int, user_id: int = None):
        """删除记录"""
        if user_id:
            return BaseMapper.delete(self, {'id': record_id, 'user_id': user_id}) > 0
        return self.delete_by_id(record_id) > 0
