from typing import Optional
from common.error_codes import ParameterError


class OrganizationCreateDTO:
    """创建组织请求参数"""
    
    def __init__(self, name: str, description: Optional[str] = None):
        self.name = name
        self.description = description
    
    def validate(self):
        if not self.name:
            raise ParameterError(msg="组织名称不能为空")
        if len(self.name) > 100:
            raise ParameterError(msg="组织名称不能超过100个字符")
        return True
    
    @classmethod
    def from_request(cls, data: dict):
        return cls(
            name=data.get('name'),
            description=data.get('description')
        )


class OrganizationUpdateDTO:
    """更新组织请求参数"""
    
    def __init__(self, name: Optional[str] = None, description: Optional[str] = None):
        self.name = name
        self.description = description
    
    def validate(self):
        if self.name and len(self.name) > 100:
            raise ParameterError(msg="组织名称不能超过100个字符")
        return True
    
    @classmethod
    def from_request(cls, data: dict):
        return cls(
            name=data.get('name'),
            description=data.get('description')
        )


class OrganizationMemberUpdateDTO:
    """更新组织成员请求参数"""
    
    def __init__(self, role: str):
        self.role = role
    
    def validate(self):
        if not self.role:
            raise ParameterError(msg="角色不能为空")
        if self.role not in ['owner', 'admin', 'member']:
            raise ParameterError(msg="角色必须是owner、admin或member")
        return True
    
    @classmethod
    def from_request(cls, data: dict):
        return cls(
            role=data.get('role')
        )
