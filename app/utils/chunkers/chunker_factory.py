"""
分块器工厂
根据策略名称创建对应的分块器实例
"""
from typing import Optional
from app.utils.chunkers.base_chunker import BaseChunker
from app.utils.chunkers.fixed_chunker import FixedChunker
from app.utils.chunkers.sentence_chunker import SentenceChunker
from app.utils.chunkers.semantic_chunker import SemanticChunker
from common import log_


class ChunkerFactory:
    """分块器工厂类"""
    
    # 策略映射表
    _chunkers = {
        'fixed': FixedChunker,
        'sentence': SentenceChunker,
        'semantic': SemanticChunker,
    }
    
    # 默认配置
    DEFAULT_CHUNK_SIZE = 1000
    DEFAULT_CHUNK_OVERLAP = 200
    DEFAULT_STRATEGY = 'fixed'
    
    @classmethod
    def create_chunker(
        cls,
        strategy: Optional[str] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> BaseChunker:
        """
        创建分块器实例
        
        Args:
            strategy: 分块策略名称 (fixed/semantic/sentence)
            chunk_size: 分块大小
            chunk_overlap: 分块重叠大小
            
        Returns:
            BaseChunker: 分块器实例
        """
        # 使用默认值
        strategy = strategy or cls.DEFAULT_STRATEGY
        chunk_size = chunk_size or cls.DEFAULT_CHUNK_SIZE
        chunk_overlap = chunk_overlap or cls.DEFAULT_CHUNK_OVERLAP
        
        # 标准化策略名称
        strategy = strategy.lower().strip()
        
        # 获取分块器类
        chunker_class = cls._chunkers.get(strategy)
        
        if chunker_class is None:
            log_.warning(f"未知的分块策略: {strategy}，使用默认策略 fixed")
            chunker_class = FixedChunker
        
        # 创建实例
        return chunker_class(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    
    @classmethod
    def get_available_strategies(cls) -> list:
        """
        获取所有可用的分块策略
        
        Returns:
            list: 策略信息列表
        """
        return [
            {'value': 'fixed', 'label': '固定长度', 'description': '按固定字符长度分割，适合大多数场景'},
            {'value': 'sentence', 'label': '句子边界', 'description': '优先按句子边界分割，保持语义完整性'},
            {'value': 'semantic', 'label': '语义分块', 'description': '基于段落和语义边界分割，适合长文档'},
        ]
    
    @classmethod
    def validate_strategy(cls, strategy: str) -> bool:
        """
        验证分块策略是否有效
        
        Args:
            strategy: 策略名称
            
        Returns:
            bool: 是否有效
        """
        return strategy.lower().strip() in cls._chunkers
