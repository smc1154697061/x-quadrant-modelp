"""
组织控制器 - 处理组织相关的请求
"""
from flask import g
from .base import BaseResource
from app.core.decorators import api_exception_handler, login_required
from common import log_
from common.error_codes import ErrorCode, ParameterError
from app.services.organization_service import OrganizationService


class OrganizationListResource(BaseResource):
    """组织列表资源控制器"""
    
    @api_exception_handler
    @login_required
    def get(self):
        """获取用户所属的组织列表"""
        user_id = g.user_id
        
        organizations = OrganizationService.list_user_organizations(user_id)
        
        return {
            "code": ErrorCode.SUCCESS.code,
            "message": "获取组织列表成功",
            "data": organizations
        }
    
    @api_exception_handler
    @login_required
    def post(self):
        """创建新组织"""
        user_id = g.user_id
        data = self.get_params()
        
        name = data.get('name', '').strip()
        description = data.get('description', '').strip() if data.get('description') else None
        
        org = OrganizationService.create_organization(user_id, name, description)
        
        return {
            "code": ErrorCode.SUCCESS.code,
            "message": "创建组织成功",
            "data": org
        }


class OrganizationDetailResource(BaseResource):
    """组织详情资源控制器"""
    
    @api_exception_handler
    @login_required
    def get(self, org_id):
        """获取组织详情"""
        user_id = g.user_id
        
        org_detail = OrganizationService.get_organization_detail(org_id, user_id)
        
        return {
            "code": ErrorCode.SUCCESS.code,
            "message": "获取组织详情成功",
            "data": org_detail
        }
    
    @api_exception_handler
    @login_required
    def put(self, org_id):
        """更新组织信息"""
        user_id = g.user_id
        data = self.get_params()
        
        name = data.get('name')
        description = data.get('description')
        
        updated_org = OrganizationService.update_organization(org_id, user_id, name, description)
        
        return {
            "code": ErrorCode.SUCCESS.code,
            "message": "更新组织成功",
            "data": updated_org
        }
    
    @api_exception_handler
    @login_required
    def delete(self, org_id):
        """解散组织"""
        user_id = g.user_id
        
        OrganizationService.dissolve_organization(org_id, user_id)
        
        return {
            "code": ErrorCode.SUCCESS.code,
            "message": "解散组织成功"
        }


class OrganizationMemberResource(BaseResource):
    """组织成员资源控制器"""
    
    @api_exception_handler
    @login_required
    def get(self, org_id):
        """获取组织成员列表"""
        user_id = g.user_id
        
        org_detail = OrganizationService.get_organization_detail(org_id, user_id)
        
        return {
            "code": ErrorCode.SUCCESS.code,
            "message": "获取成员列表成功",
            "data": org_detail.get('members', [])
        }
    
    @api_exception_handler
    @login_required
    def post(self, org_id):
        """添加成员"""
        user_id = g.user_id
        data = self.get_params()
        
        target_user_id = data.get('user_id')
        role = data.get('role', 'member')
        
        if not target_user_id:
            raise ParameterError(msg="请指定要添加的用户ID")
        
        member = OrganizationService.add_member(org_id, user_id, target_user_id, role)
        
        return {
            "code": ErrorCode.SUCCESS.code,
            "message": "添加成员成功",
            "data": member
        }
    
    @api_exception_handler
    @login_required
    def delete(self, org_id, user_id=None):
        """移除成员或退出组织"""
        operator_id = g.user_id
        data = self.get_params()
        target_user_id = user_id or data.get('user_id')
        
        if target_user_id and int(target_user_id) != operator_id:
            OrganizationService.remove_member(org_id, operator_id, int(target_user_id))
            return {
                "code": ErrorCode.SUCCESS.code,
                "message": "移除成员成功"
            }
        else:
            OrganizationService.leave_organization(org_id, operator_id)
            return {
                "code": ErrorCode.SUCCESS.code,
                "message": "退出组织成功"
            }


class UserSearchResource(BaseResource):
    """用户搜索资源控制器"""
    
    @api_exception_handler
    @login_required
    def get(self):
        """搜索用户"""
        data = self.get_params()
        email = data.get('email', '').strip()
        limit = int(data.get('limit', 10))
        
        users = OrganizationService.search_users_by_email(email, limit)
        
        return {
            "code": ErrorCode.SUCCESS.code,
            "message": "搜索用户成功",
            "data": users
        }
