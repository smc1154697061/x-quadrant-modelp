from common import log_
from common.error_codes import APIException, ErrorCode, ParameterError, ResourceNotFound, ForbiddenError
from app.dao.organization_dao import OrganizationDAO, OrganizationMemberDAO
from app.entity.organization import Organization
from app.entity.organization_member import OrganizationMember
from app.entity.dto.organization_dto import OrganizationCreateDTO, OrganizationUpdateDTO, OrganizationMemberUpdateDTO


class OrganizationService:
    """组织服务类"""
    
    @classmethod
    def get_user_organizations(cls, user_id: int):
        """获取用户所属的所有组织"""
        orgs = OrganizationMemberDAO().find_organizations_by_user_id(user_id)
        result = []
        for org in orgs:
            result.append({
                'id': org.get('id'),
                'name': org.get('name'),
                'description': org.get('description'),
                'member_count': org.get('member_count', 0),
                'my_role': org.get('my_role'),
                'created_at': org.get('created_at')
            })
        return result
    
    @classmethod
    def get_organization_detail(cls, org_id: int, user_id: int):
        """获取组织详情"""
        org = OrganizationDAO().find_by_id(org_id)
        if not org:
            raise ResourceNotFound(msg="组织不存在")
        
        member = OrganizationMemberDAO().find_by_org_and_user(org_id, user_id)
        if not member:
            raise ForbiddenError(msg="您不是该组织成员")
        
        members = OrganizationMemberDAO().find_members_by_org_id(org_id)
        member_list = []
        for m in members:
            member_list.append({
                'id': m.get('id'),
                'user_id': m.get('user_id'),
                'email': m.get('email'),
                'nickname': m.get('user_name') or (m.get('email', '').split('@')[0] if m.get('email') else '用户'),
                'role': m.get('role'),
                'joined_at': m.get('joined_at'),
                'avatar': ''
            })
        
        return {
            'id': org.get('id'),
            'name': org.get('name'),
            'description': org.get('description'),
            'created_by': org.get('created_by'),
            'created_at': org.get('created_at'),
            'members': member_list,
            'my_role': member.role if hasattr(member, 'role') else member.get('role')
        }
    
    @classmethod
    def create_organization(cls, user_id: int, dto: OrganizationCreateDTO):
        """创建组织"""
        dto.validate()
        
        org = Organization(
            name=dto.name,
            description=dto.description,
            created_by=user_id
        )
        org_dict = OrganizationDAO().create(org)
        
        member = OrganizationMember(
            organization_id=org_dict['id'],
            user_id=user_id,
            role=OrganizationMember.ROLE_OWNER
        )
        OrganizationMemberDAO().create(member)
        
        return cls.get_organization_detail(org_dict['id'], user_id)
    
    @classmethod
    def update_organization(cls, org_id: int, user_id: int, dto: OrganizationUpdateDTO):
        """更新组织信息"""
        cls._check_admin_permission(org_id, user_id)
        
        org = Organization(id=org_id)
        if dto.name:
            org.name = dto.name
        if dto.description:
            org.description = dto.description
        
        updated = OrganizationDAO().update(org)
        if not updated:
            raise APIException(ErrorCode.DATABASE_ERROR, msg="更新组织信息失败")
        
        return cls.get_organization_detail(org_id, user_id)
    
    @classmethod
    def delete_organization(cls, org_id: int, user_id: int):
        """解散组织"""
        cls._check_owner_permission(org_id, user_id)
        
        OrganizationMemberDAO().delete_by_org_id(org_id)
        deleted = OrganizationDAO().delete(org_id)
        if not deleted:
            raise APIException(ErrorCode.DATABASE_ERROR, msg="解散组织失败")
        
        return True
    
    @classmethod
    def update_member_role(cls, org_id: int, member_id: int, user_id: int, dto: OrganizationMemberUpdateDTO):
        """更新成员角色"""
        cls._check_admin_permission(org_id, user_id)
        
        member = OrganizationMemberDAO().select_by_id(member_id)
        if not member:
            raise ResourceNotFound(msg="成员不存在")
        
        member.role = dto.role
        updated = OrganizationMemberDAO().update(member)
        if not updated:
            raise APIException(ErrorCode.DATABASE_ERROR, msg="更新成员角色失败")
        
        return True
    
    @classmethod
    def remove_member(cls, org_id: int, member_id: int, user_id: int):
        """移除成员"""
        cls._check_admin_permission(org_id, user_id)
        
        member = OrganizationMemberDAO().select_by_id(member_id)
        if not member:
            raise ResourceNotFound(msg="成员不存在")
        
        if member.role == OrganizationMember.ROLE_OWNER:
            raise ForbiddenError(msg="不能移除组织所有者")
        
        deleted = OrganizationMemberDAO().delete(member_id)
        if not deleted:
            raise APIException(ErrorCode.DATABASE_ERROR, msg="移除成员失败")
        
        return True
    
    @classmethod
    def _check_admin_permission(cls, org_id: int, user_id: int):
        """检查是否有管理员权限"""
        member = OrganizationMemberDAO().find_by_org_and_user(org_id, user_id)
        if not member:
            raise ForbiddenError(msg="您不是该组织成员")
        
        role = member.role if hasattr(member, 'role') else member.get('role')
        if role not in [OrganizationMember.ROLE_OWNER, OrganizationMember.ROLE_ADMIN]:
            raise ForbiddenError(msg="需要管理员权限")
    
    @classmethod
    def _check_owner_permission(cls, org_id: int, user_id: int):
        """检查是否有所有者权限"""
        member = OrganizationMemberDAO().find_by_org_and_user(org_id, user_id)
        if not member:
            raise ForbiddenError(msg="您不是该组织成员")
        
        role = member.role if hasattr(member, 'role') else member.get('role')
        if role != OrganizationMember.ROLE_OWNER:
            raise ForbiddenError(msg="需要所有者权限")
