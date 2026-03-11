"""
机器人数据传输对象 - 接收前端请求参数
"""
from typing import Optional, List
from common.error_codes import ParameterError


class BotCreateDTO:
    """创建机器人请求参数"""
    
    def __init__(self, name: str, description: Optional[str] = None,
                 system_prompt: Optional[str] = None, model_name: Optional[str] = None,
                 is_public: bool = False, kb_ids: List[int] = None):
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.model_name = model_name
        self.is_public = is_public
        self.kb_ids = kb_ids or []
    
    def validate(self):
        """参数校验"""
        if not self.name:
            raise ParameterError(msg="机器人名称不能为空")
        if len(self.name) > 50:
            raise ParameterError(msg="机器人名称不能超过50个字符")
        return True
    
    @classmethod
    def from_request(cls, data: dict):
        """从请求数据创建"""
        return cls(
            name=data.get('name'),
            description=data.get('description'),
            system_prompt=data.get('system_prompt'),
            model_name=data.get('model_name'),
            is_public=data.get('is_public', False),
            kb_ids=data.get('kb_ids', [])
        )


class BotUpdateDTO:
    """更新机器人请求参数"""
    
    def __init__(self, name: Optional[str] = None, description: Optional[str] = None,
                 system_prompt: Optional[str] = None, model_name: Optional[str] = None,
                 is_public: Optional[bool] = None, kb_ids: Optional[List[int]] = None):
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.model_name = model_name
        self.is_public = is_public
        self.kb_ids = kb_ids
    
    def validate(self):
        """参数校验"""
        # 如果传了 name，必须非空且不超过50字符
        if self.name is not None:
            if not self.name or not self.name.strip():
                raise ParameterError(msg="机器人名称不能为空")
            if len(self.name) > 50:
                raise ParameterError(msg="机器人名称不能超过50个字符")
        return True
    
    @classmethod
    def from_request(cls, data: dict):
        """从请求数据创建"""
        return cls(
            name=data.get('name'),
            description=data.get('description'),
            system_prompt=data.get('system_prompt'),
            model_name=data.get('model_name'),
            is_public=data.get('is_public'),
            kb_ids=data.get('kb_ids')
        )
