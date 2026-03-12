from typing import Optional, List
from app.dao.mapper import BaseMapper, select, select_one
from app.entity.template import Template


class TemplateDAO(BaseMapper):
    """模板Mapper，继承BaseMapper获得通用CRUD"""
    
    entity_class = Template
    table_name = 'dodo_templates'
    primary_key = 'id'
    
    @select("SELECT * FROM dodo_templates WHERE created_by = %s ORDER BY created_at DESC", Template)
    def find_by_user(self, user_id: int) -> List[Template]:
        """通过用户ID查找模板"""
        pass
    
    @select("SELECT * FROM dodo_templates WHERE created_by = %s AND tag = %s ORDER BY created_at DESC", Template)
    def find_by_user_and_tag(self, user_id: int, tag: str) -> List[Template]:
        """通过用户ID和标签查找模板"""
        pass
    
    def create(self, template: Template):
        """创建新模板"""
        template_id = self.insert(template)
        template.id = template_id
        return template.to_dict()
    
    def delete(self, template_id: int, user_id: int = None):
        """删除模板（用户只能删除自己的）"""
        if user_id:
            return BaseMapper.delete(self, {'id': template_id, 'created_by': user_id}) > 0
        return self.delete_by_id(template_id) > 0
    
    def find_all_by_user(self, user_id: int, tag: str = None, keyword: str = None, limit: int = 100, offset: int = 0):
        """获取用户所有模板（支持标签过滤和关键词搜索）"""
        conditions = {'created_by': user_id}
        if tag:
            conditions['tag'] = tag
        
        results = self.select_list(conditions, order_by='created_at DESC', limit=limit, offset=offset)
        
        if keyword:
            results = [r for r in results if keyword.lower() in r.name.lower()]
        
        return [r.to_dict() for r in results]
    
    def count_by_user(self, user_id: int, tag: str = None, keyword: str = None):
        """统计用户模板数量"""
        conditions = {'created_by': user_id}
        if tag:
            conditions['tag'] = tag
        return self.count(conditions)
