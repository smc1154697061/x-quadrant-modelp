"""
组织服务类 - 处理组织相关的业务逻辑
"""
from typing import List, Dict, Optional
from common import log_
from common.error_codes import APIException, ErrorCode, ParameterError, ResourceNotFound
from app.dao.organization_dao import OrganizationDAO, OrganizationMemberDAO
from app.dao.user_dao import UserDAO
from app.entity.organization import Organization, OrganizationMember


class PermissionDenied(APIException):
    """权限不足异常"""
    def __init__(self, msg="权限不足"):
        super().__init__(ErrorCode.PERMISSION_DENIED, msg=msg)


class OrganizationService:
    """组织服务类，处理组织相关的业务逻辑"""
    
    @classmethod
    def create_organization(cls, user_id: int, name: str, description: str = None) -> Dict:
        """创建组织
        
        参数:
            user_id: 创建者用户ID
            name: 组织名称
            description: 组织描述
            
        返回:
            组织信息字典
        """
        if not name or not name.strip():
            raise ParameterError(msg="组织名称不能为空")
        
        org_dao = OrganizationDAO()
        member_dao = OrganizationMemberDAO()
        
        org = Organization(
            name=name.strip(),
            description=description.strip() if description else None,
            created_by=user_id
        )
        
        org_dict = org_dao.create(org)
        
        member = OrganizationMember(
            org_id=org_dict['id'],
            user_id=user_id,
            role='admin'
        )
        member_dao.add_member(member)
        
        result = org_dict.copy()
        result['member_count'] = 1
        result['my_role'] = 'admin'
        
        return result
    
    @classmethod
    def get_organization_detail(cls, org_id: int, user_id: int) -> Dict:
        """获取组织详情
        
        参数:
            org_id: 组织ID
            user_id: 当前用户ID
            
        返回:
            组织详情字典
        """
        org_dao = OrganizationDAO()
        member_dao = OrganizationMemberDAO()
        
        org_dict = org_dao.find_by_id(org_id)
        if not org_dict:
            raise ResourceNotFound(msg="组织不存在")
        
        member_relation = member_dao.find_by_org_and_user(org_id, user_id)
        if not member_relation:
            raise PermissionDenied(msg="您不是该组织的成员")
        
        members = member_dao.find_members_by_org(org_id)
        user_dao = UserDAO()
        
        member_list = []
        for member in members:
            user = user_dao.find_by_id(member['user_id'])
            if user:
                member_list.append({
                    'user_id': user['id'],
                    'email': user['email'],
                    'name': user.get('name', user['email'].split('@')[0]),
                    'role': member['role'],
                    'joined_at': member['joined_at']
                })
        
        result = org_dict.copy()
        result['members'] = member_list
        result['member_count'] = len(member_list)
        result['my_role'] = member_relation['role']
        result['is_admin'] = member_relation['role'] == 'admin'
        
        return result
    
    @classmethod
    def list_user_organizations(cls, user_id: int) -> List[Dict]:
        """获取用户所属的所有组织
        
        参数:
            user_id: 用户ID
            
        返回:
            组织列表
        """
        member_dao = OrganizationMemberDAO()
        org_dao = OrganizationDAO()
        
        member_relations = member_dao.find_orgs_by_user(user_id)
        
        result = []
        for relation in member_relations:
            org_id = relation['org_id']
            org_dict = org_dao.find_by_id(org_id)
            
            if org_dict:
                member_count = member_dao.count_members_by_org(org_id)
                
                org_info = org_dict.copy()
                org_info['member_count'] = member_count
                org_info['my_role'] = relation['role']
                result.append(org_info)
        
        return result
    
    @classmethod
    def update_organization(cls, org_id: int, user_id: int, name: str = None, description: str = None) -> Dict:
        """更新组织信息（仅管理员可操作）
        
        参数:
            org_id: 组织ID
            user_id: 当前用户ID
            name: 新名称
            description: 新描述
            
        返回:
            更新后的组织信息
        """
        org_dao = OrganizationDAO()
        member_dao = OrganizationMemberDAO()
        
        org_dict = org_dao.find_by_id(org_id)
        if not org_dict:
            raise ResourceNotFound(msg="组织不存在")
        
        member_relation = member_dao.find_by_org_and_user(org_id, user_id)
        if not member_relation or member_relation['role'] != 'admin':
            raise PermissionDenied(msg="只有管理员可以编辑组织信息")
        
        org = Organization(id=org_id)
        if name is not None:
            if not name.strip():
                raise ParameterError(msg="组织名称不能为空")
            org.name = name.strip()
        if description is not None:
            org.description = description.strip() if description else None
        
        org_dao.update_org(org)
        
        return cls.get_organization_detail(org_id, user_id)
    
    @classmethod
    def dissolve_organization(cls, org_id: int, user_id: int) -> bool:
        """解散组织（仅管理员可操作）
        
        参数:
            org_id: 组织ID
            user_id: 当前用户ID
            
        返回:
            是否成功
        """
        org_dao = OrganizationDAO()
        member_dao = OrganizationMemberDAO()
        
        org_dict = org_dao.find_by_id(org_id)
        if not org_dict:
            raise ResourceNotFound(msg="组织不存在")
        
        member_relation = member_dao.find_by_org_and_user(org_id, user_id)
        if not member_relation or member_relation['role'] != 'admin':
            raise PermissionDenied(msg="只有管理员可以解散组织")
        
        member_dao.remove_all_members(org_id)
        
        org_dao.delete_org(org_id)
        
        return True
    
    @classmethod
    def add_member(cls, org_id: int, operator_id: int, target_user_id: int, role: str = 'member') -> Dict:
        """添加成员（仅管理员可操作）
        
        参数:
            org_id: 组织ID
            operator_id: 操作者用户ID
            target_user_id: 目标用户ID
            role: 角色
            
        返回:
            成员信息
        """
        member_dao = OrganizationMemberDAO()
        org_dao = OrganizationDAO()
        
        org_dict = org_dao.find_by_id(org_id)
        if not org_dict:
            raise ResourceNotFound(msg="组织不存在")
        
        operator_relation = member_dao.find_by_org_and_user(org_id, operator_id)
        if not operator_relation or operator_relation['role'] != 'admin':
            raise PermissionDenied(msg="只有管理员可以添加成员")
        
        existing = member_dao.find_by_org_and_user(org_id, target_user_id)
        if existing:
            raise ParameterError(msg="该用户已是组织成员")
        
        user_dao = UserDAO()
        user = user_dao.find_by_id(target_user_id)
        if not user:
            raise ResourceNotFound(msg="用户不存在")
        
        if role not in ['admin', 'member']:
            raise ParameterError(msg="角色只能是 admin 或 member")
        
        member = OrganizationMember(
            org_id=org_id,
            user_id=target_user_id,
            role=role
        )
        member_dao.add_member(member)
        
        return {
            'user_id': target_user_id,
            'email': user['email'],
            'name': user.get('name', user['email'].split('@')[0]),
            'role': role
        }
    
    @classmethod
    def remove_member(cls, org_id: int, operator_id: int, target_user_id: int) -> bool:
        """移除成员（仅管理员可操作，不能移除自己）
        
        参数:
            org_id: 组织ID
            operator_id: 操作者用户ID
            target_user_id: 目标用户ID
            
        返回:
            是否成功
        """
        member_dao = OrganizationMemberDAO()
        org_dao = OrganizationDAO()
        
        org_dict = org_dao.find_by_id(org_id)
        if not org_dict:
            raise ResourceNotFound(msg="组织不存在")
        
        operator_relation = member_dao.find_by_org_and_user(org_id, operator_id)
        if not operator_relation or operator_relation['role'] != 'admin':
            raise PermissionDenied(msg="只有管理员可以移除成员")
        
        if operator_id == target_user_id:
            raise ParameterError(msg="不能移除自己")
        
        return member_dao.remove_member(org_id, target_user_id)
    
    @classmethod
    def leave_organization(cls, org_id: int, user_id: int) -> bool:
        """退出组织
        
        参数:
            org_id: 组织ID
            user_id: 用户ID
            
        返回:
            是否成功
        """
        member_dao = OrganizationMemberDAO()
        org_dao = OrganizationDAO()
        
        org_dict = org_dao.find_by_id(org_id)
        if not org_dict:
            raise ResourceNotFound(msg="组织不存在")
        
        member_relation = member_dao.find_by_org_and_user(org_id, user_id)
        if not member_relation:
            raise ParameterError(msg="您不是该组织的成员")
        
        if member_relation['role'] == 'admin':
            member_count = member_dao.count_members_by_org(org_id)
            if member_count > 1:
                raise ParameterError(msg="管理员退出前请先转让管理员权限或解散组织")
        
        return member_dao.remove_member(org_id, user_id)
    
    @classmethod
    def search_users_by_email(cls, email: str, limit: int = 10) -> List[Dict]:
        """根据邮箱搜索用户
        
        参数:
            email: 邮箱关键字
            limit: 返回数量限制
            
        返回:
            用户列表
        """
        if not email or len(email) < 2:
            return []
        
        user_dao = UserDAO()
        users = user_dao.search_by_email(email, limit)
        
        return [{
            'id': user['id'],
            'email': user['email'],
            'name': user.get('name', user['email'].split('@')[0])
        } for user in users]
