from typing import Optional, List
from app.dao.mapper import BaseMapper, select_one, select
from app.entity.organization import Organization
from app.entity.organization_member import OrganizationMember


class OrganizationDAO(BaseMapper):
    """组织DAO类"""
    
    entity_class = Organization
    table_name = 'dodo_organizations'
    primary_key = 'id'
    
    def find_by_id(self, org_id):
        org = self.select_by_id(org_id)
        return org.to_dict() if org else None
    
    def create(self, org: Organization):
        org_id = self.insert(org)
        org.id = org_id
        return org.to_dict()
    
    def update(self, org: Organization):
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
    
    def delete(self, org_id):
        return self.delete_by_id(org_id) > 0
    
    @select("SELECT * FROM dodo_organizations WHERE created_by = %s ORDER BY created_at DESC", Organization)
    def find_by_created_by(self, user_id: int) -> List[Organization]:
        pass


class OrganizationMemberDAO(BaseMapper):
    """组织成员DAO类"""
    
    entity_class = OrganizationMember
    table_name = 'dodo_organization_members'
    primary_key = 'id'
    
    def create(self, member: OrganizationMember):
        member_id = self.insert(member)
        member.id = member_id
        return member.to_dict()
    
    def delete(self, member_id):
        return self.delete_by_id(member_id) > 0
    
    @select("""
        SELECT om.*, u.email, COALESCE(u.name, u.email) as user_name 
        FROM dodo_organization_members om
        LEFT JOIN dodo_users u ON om.user_id = u.id
        WHERE om.organization_id = %s
        ORDER BY om.created_at DESC
    """)
    def find_members_by_org_id(self, org_id: int) -> List[dict]:
        pass
    
    @select("""
        SELECT o.*, om.role as my_role, 
               (SELECT COUNT(*) FROM dodo_organization_members WHERE organization_id = o.id) as member_count
        FROM dodo_organizations o
        INNER JOIN dodo_organization_members om ON o.id = om.organization_id
        WHERE om.user_id = %s
        ORDER BY o.created_at DESC
    """)
    def find_organizations_by_user_id(self, user_id: int) -> List[dict]:
        pass
    
    @select_one("""
        SELECT * FROM dodo_organization_members 
        WHERE organization_id = %s AND user_id = %s
    """, OrganizationMember)
    def find_by_org_and_user(self, org_id: int, user_id: int) -> Optional[OrganizationMember]:
        pass
    
    def delete_by_org_id(self, org_id: int):
        return self.delete({'organization_id': org_id})
