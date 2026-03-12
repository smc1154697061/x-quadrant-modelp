"""
分块策略测试脚本
验证三种分块策略的效果差异
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 直接导入分块器模块，避免依赖其他模块
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter


class BaseChunker:
    """文档分块器抽象基类"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def split(self, docs):
        raise NotImplementedError
    
    @property
    def strategy_name(self) -> str:
        raise NotImplementedError


class FixedChunker(BaseChunker):
    """固定长度分块器"""
    
    @property
    def strategy_name(self) -> str:
        return "fixed"
    
    def split(self, docs):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        return text_splitter.split_documents(docs)


class SentenceChunker(BaseChunker):
    """句子边界分块器"""
    
    @property
    def strategy_name(self) -> str:
        return "sentence"
    
    def split(self, docs):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=[
                "\n\n", "\n", "。", "？", "！", ".", "?", "!", "；", ";", " ", ""
            ]
        )
        return text_splitter.split_documents(docs)


class SemanticChunker(BaseChunker):
    """语义分块器"""
    
    @property
    def strategy_name(self) -> str:
        return "semantic"
    
    def split(self, docs):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=[
                "\n\n", "\n", "。 ", ". ", "；", ";", "，", ",", " ", ""
            ]
        )
        chunks = text_splitter.split_documents(docs)
        return self._optimize_chunks(chunks)
    
    def _optimize_chunks(self, chunks):
        if not chunks:
            return chunks
        
        optimized = []
        current_chunk = None
        min_chunk_size = self.chunk_size // 4
        
        for chunk in chunks:
            if current_chunk is None:
                current_chunk = chunk
            elif len(current_chunk.page_content) < min_chunk_size:
                combined_content = current_chunk.page_content + "\n\n" + chunk.page_content
                if len(combined_content) <= self.chunk_size:
                    current_chunk.page_content = combined_content
                    current_chunk.metadata.update(chunk.metadata)
                else:
                    optimized.append(current_chunk)
                    current_chunk = chunk
            else:
                optimized.append(current_chunk)
                current_chunk = chunk
        
        if current_chunk is not None:
            optimized.append(current_chunk)
        
        return optimized


class ChunkerFactory:
    """分块器工厂类"""
    
    _chunkers = {
        'fixed': FixedChunker,
        'sentence': SentenceChunker,
        'semantic': SemanticChunker,
    }
    
    DEFAULT_CHUNK_SIZE = 1000
    DEFAULT_CHUNK_OVERLAP = 200
    DEFAULT_STRATEGY = 'fixed'
    
    @classmethod
    def create_chunker(cls, strategy=None, chunk_size=None, chunk_overlap=None):
        strategy = strategy or cls.DEFAULT_STRATEGY
        chunk_size = chunk_size or cls.DEFAULT_CHUNK_SIZE
        chunk_overlap = chunk_overlap or cls.DEFAULT_CHUNK_OVERLAP
        strategy = strategy.lower().strip()
        
        chunker_class = cls._chunkers.get(strategy, FixedChunker)
        return chunker_class(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    
    @classmethod
    def get_available_strategies(cls):
        return [
            {'value': 'fixed', 'label': '固定长度', 'description': '按固定字符长度分割，适合大多数场景'},
            {'value': 'sentence', 'label': '句子边界', 'description': '优先按句子边界分割，保持语义完整性'},
            {'value': 'semantic', 'label': '语义分块', 'description': '基于段落和语义边界分割，适合长文档'},
        ]


# 测试文本 - 包含多个段落和句子
TEST_TEXT = """
人工智能（Artificial Intelligence，简称AI）是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。

该领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。人工智能从诞生以来，理论和技术日益成熟，应用领域也不断扩大。

机器学习是人工智能的一个重要分支。它使用算法来解析数据，从中学习，然后对真实世界中的事件做出决策和预测。与传统的为解决特定任务、硬编码的软件程序不同，机器学习是用大量的数据来"训练"，通过各种算法从数据中学习如何完成任务。

深度学习是机器学习的一种特殊类型。它受到人类大脑结构的启发，使用人工神经网络来处理数据。神经网络包含多个层，每一层都从数据中提取不同的特征。深度学习在图像识别、语音识别和自然语言处理等领域取得了突破性进展。

自然语言处理（NLP）是人工智能和语言学领域的分支学科。它研究能实现人与计算机之间用自然语言进行有效通信的各种理论和方法。自然语言处理包括机器翻译、情感分析、问答系统等多个应用方向。
"""


def create_test_documents():
    """创建测试文档"""
    return [Document(page_content=TEST_TEXT.strip(), metadata={"source": "test.txt"})]


def analyze_chunks(chunks, strategy_name):
    """分析分块结果"""
    print(f"\n{'='*60}")
    print(f"分块策略: {strategy_name}")
    print(f"{'='*60}")
    print(f"总分块数: {len(chunks)}")
    print(f"\n各块详情:")
    print("-" * 60)
    
    for i, chunk in enumerate(chunks):
        content = chunk.page_content
        lines = content.count('\n') + 1
        sentences = content.count('。') + content.count('.') + content.count('？') + content.count('?')
        
        print(f"\n块 {i+1}:")
        print(f"  字符数: {len(content)}")
        print(f"  行数: {lines}")
        print(f"  句子数(估算): {sentences}")
        print(f"  内容预览: {content[:100]}...")
    
    # 统计信息
    sizes = [len(c.page_content) for c in chunks]
    avg_size = sum(sizes) / len(sizes) if sizes else 0
    max_size = max(sizes) if sizes else 0
    min_size = min(sizes) if sizes else 0
    
    print(f"\n统计信息:")
    print(f"  平均块大小: {avg_size:.1f} 字符")
    print(f"  最大块大小: {max_size} 字符")
    print(f"  最小块大小: {min_size} 字符")


def test_fixed_chunker():
    """测试固定长度分块器"""
    print("\n" + "="*60)
    print("测试固定长度分块策略")
    print("="*60)
    
    docs = create_test_documents()
    chunker = FixedChunker(chunk_size=200, chunk_overlap=50)
    chunks = chunker.split(docs)
    
    analyze_chunks(chunks, "固定长度 (chunk_size=200, overlap=50)")
    return chunks


def test_sentence_chunker():
    """测试句子边界分块器"""
    print("\n" + "="*60)
    print("测试句子边界分块策略")
    print("="*60)
    
    docs = create_test_documents()
    chunker = SentenceChunker(chunk_size=300, chunk_overlap=50)
    chunks = chunker.split(docs)
    
    analyze_chunks(chunks, "句子边界 (chunk_size=300, overlap=50)")
    return chunks


def test_semantic_chunker():
    """测试语义分块器"""
    print("\n" + "="*60)
    print("测试语义分块策略")
    print("="*60)
    
    docs = create_test_documents()
    chunker = SemanticChunker(chunk_size=400, chunk_overlap=100)
    chunks = chunker.split(docs)
    
    analyze_chunks(chunks, "语义分块 (chunk_size=400, overlap=100)")
    return chunks


def test_chunker_factory():
    """测试分块器工厂"""
    print("\n" + "="*60)
    print("测试分块器工厂")
    print("="*60)
    
    docs = create_test_documents()
    
    # 测试各种策略创建
    strategies = ['fixed', 'sentence', 'semantic', 'unknown']
    
    for strategy in strategies:
        print(f"\n策略: {strategy}")
        chunker = ChunkerFactory.create_chunker(
            strategy=strategy,
            chunk_size=200,
            chunk_overlap=50
        )
        print(f"  创建成功: {type(chunker).__name__}")
        print(f"  策略名称: {chunker.strategy_name}")
        
        # 简单测试
        chunks = chunker.split(docs)
        print(f"  分块数量: {len(chunks)}")


def test_edge_cases():
    """测试边界情况"""
    print("\n" + "="*60)
    print("测试边界情况")
    print("="*60)
    
    # 空文档
    empty_docs = [Document(page_content="", metadata={})]
    chunker = FixedChunker(chunk_size=100, chunk_overlap=20)
    chunks = chunker.split(empty_docs)
    print(f"\n空文档分块数: {len(chunks)}")
    
    # 短文本
    short_docs = [Document(page_content="这是一个短文本。", metadata={})]
    chunks = chunker.split(short_docs)
    print(f"短文本分块数: {len(chunks)}")
    if chunks:
        print(f"短文本块内容: '{chunks[0].page_content}'")
    
    # 长文本（无换行）
    long_text = "这是一句话。" * 100
    long_docs = [Document(page_content=long_text, metadata={})]
    chunks = chunker.split(long_docs)
    print(f"长文本(无换行)分块数: {len(chunks)}")


def compare_strategies():
    """对比三种策略的差异"""
    print("\n" + "="*60)
    print("三种策略对比总结")
    print("="*60)
    
    docs = create_test_documents()
    
    configs = [
        ('fixed', 300, 50),
        ('sentence', 300, 50),
        ('semantic', 300, 50),
    ]
    
    print(f"\n{'策略':<12} {'块数':>6} {'平均大小':>10} {'最大':>8} {'最小':>8}")
    print("-" * 60)
    
    for strategy, size, overlap in configs:
        chunker = ChunkerFactory.create_chunker(strategy, size, overlap)
        chunks = chunker.split(docs)
        
        sizes = [len(c.page_content) for c in chunks]
        avg = sum(sizes) / len(sizes) if sizes else 0
        max_s = max(sizes) if sizes else 0
        min_s = min(sizes) if sizes else 0
        
        print(f"{strategy:<12} {len(chunks):>6} {avg:>10.1f} {max_s:>8} {min_s:>8}")


def main():
    """主函数"""
    print("="*60)
    print("分块策略测试脚本")
    print("="*60)
    
    # 运行各项测试
    test_fixed_chunker()
    test_sentence_chunker()
    test_semantic_chunker()
    test_chunker_factory()
    test_edge_cases()
    compare_strategies()
    
    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)


if __name__ == "__main__":
    main()
