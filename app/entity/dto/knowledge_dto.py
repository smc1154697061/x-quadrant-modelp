"""
知识库数据传输对象 - 接收前端请求参数
"""
from typing import Optional
from common.error_codes import ParameterError


class KnowledgeBaseCreateDTO:
    """创建知识库请求参数"""
    
    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        chunking_strategy: Optional[str] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ):
        self.name = name
        self.description = description or ""
        self.chunking_strategy = chunking_strategy or 'fixed'
        self.chunk_size = chunk_size or 1000
        self.chunk_overlap = chunk_overlap or 200
    
    def validate(self):
        """参数校验"""
        if not self.name:
            raise ParameterError(msg="知识库名称不能为空")
        if len(self.name) > 100:
            raise ParameterError(msg="知识库名称不能超过100个字符")
        
        # 校验分块策略
        valid_strategies = ['fixed', 'semantic', 'sentence']
        if self.chunking_strategy not in valid_strategies:
            raise ParameterError(msg=f"无效的分块策略，可选值: {', '.join(valid_strategies)}")
        
        # 校验分块大小
        if self.chunk_size < 100 or self.chunk_size > 8000:
            raise ParameterError(msg="分块大小必须在100-8000之间")
        
        # 校验重叠大小
        if self.chunk_overlap < 0 or self.chunk_overlap >= self.chunk_size:
            raise ParameterError(msg="重叠大小必须大于等于0且小于分块大小")
        
        return True
    
    @classmethod
    def from_request(cls, data: dict):
        """从请求数据创建"""
        return cls(
            name=data.get('name'),
            description=data.get('description'),
            chunking_strategy=data.get('chunking_strategy'),
            chunk_size=data.get('chunk_size'),
            chunk_overlap=data.get('chunk_overlap')
        )


class KnowledgeBaseUpdateDTO:
    """更新知识库请求参数"""
    
    def __init__(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        chunking_strategy: Optional[str] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ):
        self.name = name
        self.description = description
        self.chunking_strategy = chunking_strategy
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def validate(self):
        """参数校验"""
        if self.name and len(self.name) > 100:
            raise ParameterError(msg="知识库名称不能超过100个字符")
        
        # 校验分块策略
        if self.chunking_strategy is not None:
            valid_strategies = ['fixed', 'semantic', 'sentence']
            if self.chunking_strategy not in valid_strategies:
                raise ParameterError(msg=f"无效的分块策略，可选值: {', '.join(valid_strategies)}")
        
        # 校验分块大小
        if self.chunk_size is not None:
            if self.chunk_size < 100 or self.chunk_size > 8000:
                raise ParameterError(msg="分块大小必须在100-8000之间")
        
        # 校验重叠大小
        if self.chunk_overlap is not None and self.chunk_size is not None:
            if self.chunk_overlap < 0 or self.chunk_overlap >= self.chunk_size:
                raise ParameterError(msg="重叠大小必须大于等于0且小于分块大小")
        
        return True
    
    @classmethod
    def from_request(cls, data: dict):
        """从请求数据创建"""
        return cls(
            name=data.get('name'),
            description=data.get('description'),
            chunking_strategy=data.get('chunking_strategy'),
            chunk_size=data.get('chunk_size'),
            chunk_overlap=data.get('chunk_overlap')
        )
    
    def to_dict(self) -> dict:
        """转换为字典，只包含非None的字段"""
        result = {}
        if self.name is not None:
            result['name'] = self.name
        if self.description is not None:
            result['description'] = self.description
        if self.chunking_strategy is not None:
            result['chunking_strategy'] = self.chunking_strategy
        if self.chunk_size is not None:
            result['chunk_size'] = self.chunk_size
        if self.chunk_overlap is not None:
            result['chunk_overlap'] = self.chunk_overlap
        return result
