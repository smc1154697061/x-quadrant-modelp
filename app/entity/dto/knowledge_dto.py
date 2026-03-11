"""
知识库数据传输对象 - 接收前端请求参数
"""
from typing import Optional
from common.error_codes import ParameterError


class KnowledgeBaseCreateDTO:
    """创建知识库请求参数"""
    
    def __init__(self, name: str, description: Optional[str] = None):
        self.name = name
        self.description = description or ""
    
    def validate(self):
        """参数校验"""
        if not self.name:
            raise ParameterError(msg="知识库名称不能为空")
        if len(self.name) > 100:
            raise ParameterError(msg="知识库名称不能超过100个字符")
        return True
    
    @classmethod
    def from_request(cls, data: dict):
        """从请求数据创建"""
        return cls(
            name=data.get('name'),
            description=data.get('description')
        )


class KnowledgeBaseUpdateDTO:
    """更新知识库请求参数"""
    
    def __init__(self, name: Optional[str] = None, description: Optional[str] = None):
        self.name = name
        self.description = description
    
    def validate(self):
        """参数校验"""
        if self.name and len(self.name) > 100:
            raise ParameterError(msg="知识库名称不能超过100个字符")
        return True
    
    @classmethod
    def from_request(cls, data: dict):
        """从请求数据创建"""
        return cls(
            name=data.get('name'),
            description=data.get('description')
        )
