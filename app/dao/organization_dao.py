"""
组织Mapper - MyBatis Plus风格
"""
from typing import Optional, List, Dict, Any
from common import log_
from common.db_utils import get_db_connection
from app.dao.mapper import BaseMapper
from app.entity.organization import Organization, OrganizationMember


class OrganizationDAO(BaseMapper):
    """组织Mapper，继承BaseMapper获得通用CRUD"""
    
    entity_class = Organization
    table_name = 'dodo_organizations'
    primary_key = 'id'
    
    def find_by_id(self, org_id: int) -> Optional[Dict]:
        """通过ID查找组织，返回字典"""
        org = self.select_by_id(org_id)
        return org.to_dict() if org else None
    
    def find_by_creator(self, user_id: int, limit: int = 100, offset: int = 0) -> List[Dict]:
        """查找用户创建的组织"""
        orgs = self.select_list(
            conditions={'created_by': user_id},
            order_by='created_at DESC',
            limit=limit,
            offset=offset
        )
        return [org.to_dict() for org in orgs]
    
    def create(self, org: Organization) -> Dict:
        """创建组织"""
        org_id = self.insert(org)
        org.id = org_id
        return org.to_dict()
    
    def update_org(self, org: Organization) -> bool:
        """更新组织信息"""
        if not org.id:
            raise ValueError("Organization实体必须包含id字段")
        
        update_data = org.to_dict()
        update_data.pop('id', None)
        update_data.pop('created_at', None)
        update_data.pop('created_by', None)
        
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        if not update_data:
            return True
        
        return super().update(update_data, {'id': org.id}) > 0
    
    def delete_org(self, org_id: int) -> bool:
        """删除组织"""
        return self.delete_by_id(org_id) > 0


class OrganizationMemberDAO(BaseMapper):
    """组织成员Mapper"""
    
    entity_class = OrganizationMember
    table_name = 'dodo_organization_members'
    primary_key = 'id'
    
    def find_by_org_and_user(self, org_id: int, user_id: int) -> Optional[Dict]:
        """查找组织成员关系"""
        member = self.select_one(conditions={'org_id': org_id, 'user_id': user_id})
        return member.to_dict() if member else None
    
    def find_members_by_org(self, org_id: int) -> List[Dict]:
        """获取组织所有成员"""
        members = self.select_list(
            conditions={'org_id': org_id},
            order_by='joined_at ASC'
        )
        return [member.to_dict() for member in members]
    
    def find_orgs_by_user(self, user_id: int) -> List[Dict]:
        """获取用户所属的所有组织"""
        members = self.select_list(
            conditions={'user_id': user_id},
            order_by='joined_at DESC'
        )
        return [member.to_dict() for member in members]
    
    def count_members_by_org(self, org_id: int) -> int:
        """统计组织成员数量"""
        return self.count(conditions={'org_id': org_id})
    
    def add_member(self, member: OrganizationMember) -> Dict:
        """添加成员"""
        member_id = self.insert(member)
        member.id = member_id
        return member.to_dict()
    
    def update_role(self, org_id: int, user_id: int, role: str) -> bool:
        """更新成员角色"""
        return super().update(
            {'role': role},
            {'org_id': org_id, 'user_id': user_id}
        ) > 0
    
    def remove_member(self, org_id: int, user_id: int) -> bool:
        """移除成员"""
        return self.delete(conditions={'org_id': org_id, 'user_id': user_id}) > 0
    
    def remove_all_members(self, org_id: int) -> int:
        """移除组织所有成员"""
        return self.delete(conditions={'org_id': org_id})
