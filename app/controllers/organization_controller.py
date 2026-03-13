from flask import g
from .base import BaseResource
from app.core.decorators import api_exception_handler, login_required
from common import log_
from common.error_codes import APIException, ErrorCode
from app.services.organization_service import OrganizationService
from app.entity.dto.organization_dto import OrganizationCreateDTO, OrganizationUpdateDTO, OrganizationMemberUpdateDTO


class OrganizationListResource(BaseResource):
    """组织列表资源控制器"""
    
    @api_exception_handler
    @login_required
    def get(self):
        """获取用户所属的所有组织"""
        user_id = g.user_id
        orgs = OrganizationService.get_user_organizations(user_id)
        return {
            "code": ErrorCode.SUCCESS.code,
            "message": "获取组织列表成功",
            "data": orgs
        }
    
    @api_exception_handler
    @login_required
    def post(self):
        """创建新组织"""
        user_id = g.user_id
        data = self.get_params()
        dto = OrganizationCreateDTO.from_request(data)
        result = OrganizationService.create_organization(user_id, dto)
        return {
            "code": ErrorCode.SUCCESS.code,
            "message": "创建组织成功",
            "data": result
        }


class OrganizationDetailResource(BaseResource):
    """组织详情资源控制器"""
    
    @api_exception_handler
    @login_required
    def get(self, org_id):
        """获取组织详情"""
        user_id = g.user_id
        org = OrganizationService.get_organization_detail(org_id, user_id)
        return {
            "code": ErrorCode.SUCCESS.code,
            "message": "获取组织详情成功",
            "data": org
        }
    
    @api_exception_handler
    @login_required
    def put(self, org_id):
        """更新组织信息"""
        user_id = g.user_id
        data = self.get_params()
        dto = OrganizationUpdateDTO.from_request(data)
        result = OrganizationService.update_organization(org_id, user_id, dto)
        return {
            "code": ErrorCode.SUCCESS.code,
            "message": "更新组织信息成功",
            "data": result
        }
    
    @api_exception_handler
    @login_required
    def delete(self, org_id):
        """解散组织"""
        user_id = g.user_id
        OrganizationService.delete_organization(org_id, user_id)
        return {
            "code": ErrorCode.SUCCESS.code,
            "message": "解散组织成功"
        }


class OrganizationMemberResource(BaseResource):
    """组织成员资源控制器"""
    
    @api_exception_handler
    @login_required
    def put(self, org_id, member_id):
        """更新成员角色"""
        user_id = g.user_id
        data = self.get_params()
        dto = OrganizationMemberUpdateDTO.from_request(data)
        OrganizationService.update_member_role(org_id, member_id, user_id, dto)
        return {
            "code": ErrorCode.SUCCESS.code,
            "message": "更新成员角色成功"
        }
    
    @api_exception_handler
    @login_required
    def delete(self, org_id, member_id):
        """移除成员"""
        user_id = g.user_id
        OrganizationService.remove_member(org_id, member_id, user_id)
        return {
            "code": ErrorCode.SUCCESS.code,
            "message": "移除成员成功"
        }
