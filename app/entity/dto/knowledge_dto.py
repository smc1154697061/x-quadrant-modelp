"""
知识库数据传输对象 - 接收前端请求参数
"""
from typing import Optional
from common.error_codes import ParameterError

CHUNKING_STRATEGIES = ['fixed', 'semantic', 'sentence']

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200
MIN_CHUNK_SIZE = 100
MAX_CHUNK_SIZE = 10000
MIN_CHUNK_OVERLAP = 0
MAX_CHUNK_OVERLAP = 2000


class KnowledgeBaseCreateDTO:
    """创建知识库请求参数"""
    
    def __init__(self, name: str, description: Optional[str] = None,
                 chunking_strategy: Optional[str] = 'fixed',
                 chunk_size: Optional[int] = DEFAULT_CHUNK_SIZE,
                 chunk_overlap: Optional[int] = DEFAULT_CHUNK_OVERLAP):
        self.name = name
        self.description = description or ""
        self.chunking_strategy = chunking_strategy or 'fixed'
        self.chunk_size = chunk_size if chunk_size is not None else DEFAULT_CHUNK_SIZE
        self.chunk_overlap = chunk_overlap if chunk_overlap is not None else DEFAULT_CHUNK_OVERLAP
    
    def validate(self):
        """参数校验"""
        if not self.name:
            raise ParameterError(msg="知识库名称不能为空")
        if len(self.name) > 100:
            raise ParameterError(msg="知识库名称不能超过100个字符")
        if self.chunking_strategy not in CHUNKING_STRATEGIES:
            raise ParameterError(msg=f"不支持的分块策略: {self.chunking_strategy}，支持: {CHUNKING_STRATEGIES}")
        if not MIN_CHUNK_SIZE <= self.chunk_size <= MAX_CHUNK_SIZE:
            raise ParameterError(msg=f"分块大小必须在 {MIN_CHUNK_SIZE}-{MAX_CHUNK_SIZE} 之间")
        if not MIN_CHUNK_OVERLAP <= self.chunk_overlap <= MAX_CHUNK_OVERLAP:
            raise ParameterError(msg=f"分块重叠必须在 {MIN_CHUNK_OVERLAP}-{MAX_CHUNK_OVERLAP} 之间")
        if self.chunk_overlap >= self.chunk_size:
            raise ParameterError(msg="分块重叠不能大于等于分块大小")
        return True
    
    @classmethod
    def from_request(cls, data: dict):
        """从请求数据创建"""
        return cls(
            name=data.get('name'),
            description=data.get('description'),
            chunking_strategy=data.get('chunking_strategy', 'fixed'),
            chunk_size=data.get('chunk_size', DEFAULT_CHUNK_SIZE),
            chunk_overlap=data.get('chunk_overlap', DEFAULT_CHUNK_OVERLAP)
        )


class KnowledgeBaseUpdateDTO:
    """更新知识库请求参数"""
    
    def __init__(self, name: Optional[str] = None, description: Optional[str] = None,
                 chunking_strategy: Optional[str] = None,
                 chunk_size: Optional[int] = None,
                 chunk_overlap: Optional[int] = None):
        self.name = name
        self.description = description
        self.chunking_strategy = chunking_strategy
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def validate(self):
        """参数校验"""
        if self.name and len(self.name) > 100:
            raise ParameterError(msg="知识库名称不能超过100个字符")
        if self.chunking_strategy is not None and self.chunking_strategy not in CHUNKING_STRATEGIES:
            raise ParameterError(msg=f"不支持的分块策略: {self.chunking_strategy}，支持: {CHUNKING_STRATEGIES}")
        if self.chunk_size is not None and not MIN_CHUNK_SIZE <= self.chunk_size <= MAX_CHUNK_SIZE:
            raise ParameterError(msg=f"分块大小必须在 {MIN_CHUNK_SIZE}-{MAX_CHUNK_SIZE} 之间")
        if self.chunk_overlap is not None and not MIN_CHUNK_OVERLAP <= self.chunk_overlap <= MAX_CHUNK_OVERLAP:
            raise ParameterError(msg=f"分块重叠必须在 {MIN_CHUNK_OVERLAP}-{MAX_CHUNK_OVERLAP} 之间")
        if self.chunk_size is not None and self.chunk_overlap is not None and self.chunk_overlap >= self.chunk_size:
            raise ParameterError(msg="分块重叠不能大于等于分块大小")
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
