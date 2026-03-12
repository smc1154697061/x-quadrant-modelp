"""
分块策略单元测试
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain.schema import Document
from app.utils.chunkers import FixedChunker, SemanticChunker, SentenceChunker, get_chunker
from app.utils.document_loader import split_document, split_document_with_strategy


class TestFixedChunker(unittest.TestCase):
    """测试固定长度分块器"""
    
    def setUp(self):
        self.sample_text = """
人工智能是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。
该领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。
人工智能从诞生以来，理论和技术日益成熟，应用领域也不断扩大。
"""
        self.doc = Document(page_content=self.sample_text.strip(), metadata={"source": "test"})
    
    def test_strategy_name(self):
        """测试策略名称"""
        chunker = FixedChunker()
        self.assertEqual(chunker.strategy_name, "fixed")
    
    def test_basic_split(self):
        """测试基本分块功能"""
        chunker = FixedChunker(chunk_size=100, chunk_overlap=20)
        chunks = chunker.split([self.doc])
        
        self.assertGreater(len(chunks), 0)
        for chunk in chunks:
            self.assertIsInstance(chunk, Document)
            self.assertIn("source", chunk.metadata)
    
    def test_chunk_size_limit(self):
        """测试分块大小限制"""
        chunker = FixedChunker(chunk_size=50, chunk_overlap=10)
        chunks = chunker.split([self.doc])
        
        for chunk in chunks:
            self.assertLessEqual(len(chunk.page_content), 60)
    
    def test_overlap(self):
        """测试重叠功能"""
        chunker = FixedChunker(chunk_size=50, chunk_overlap=20)
        chunks = chunker.split([self.doc])
        
        if len(chunks) > 1:
            pass
    
    def test_empty_document(self):
        """测试空文档"""
        empty_doc = Document(page_content="", metadata={"source": "empty"})
        chunker = FixedChunker()
        chunks = chunker.split([empty_doc])
        
        self.assertEqual(len(chunks), 0)


class TestSentenceChunker(unittest.TestCase):
    """测试句子分块器"""
    
    def setUp(self):
        self.sample_text = """
人工智能是计算机科学的一个分支。它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器！
该领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。
人工智能从诞生以来，理论和技术日益成熟。应用领域也不断扩大，可以设想，未来人工智能带来的科技产品，将会是人类智慧的"容器"。
"""
        self.doc = Document(page_content=self.sample_text.strip(), metadata={"source": "test"})
    
    def test_strategy_name(self):
        """测试策略名称"""
        chunker = SentenceChunker()
        self.assertEqual(chunker.strategy_name, "sentence")
    
    def test_basic_split(self):
        """测试基本分块功能"""
        chunker = SentenceChunker(chunk_size=100, chunk_overlap=20)
        chunks = chunker.split([self.doc])
        
        self.assertGreater(len(chunks), 0)
        for chunk in chunks:
            self.assertIsInstance(chunk, Document)
    
    def test_sentence_boundaries(self):
        """测试句子边界"""
        chunker = SentenceChunker(chunk_size=1000, chunk_overlap=0)
        chunks = chunker.split([self.doc])
        
        self.assertGreater(len(chunks), 0)
    
    def test_split_into_sentences(self):
        """测试句子分割"""
        chunker = SentenceChunker()
        text = "这是第一句。这是第二句！这是第三句？"
        sentences = chunker._split_into_sentences(text)
        
        self.assertEqual(len(sentences), 3)


class TestSemanticChunker(unittest.TestCase):
    """测试语义分块器"""
    
    def setUp(self):
        self.sample_text = """
人工智能是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。
该领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。
"""
        self.doc = Document(page_content=self.sample_text.strip(), metadata={"source": "test"})
    
    def test_strategy_name(self):
        """测试策略名称"""
        chunker = SemanticChunker()
        self.assertEqual(chunker.strategy_name, "semantic")
    
    def test_fallback_to_fixed(self):
        """测试回退到固定分块（当没有嵌入模型时）"""
        chunker = SemanticChunker(chunk_size=100, chunk_overlap=20, embeddings_model=None)
        chunks = chunker.split([self.doc])
        
        self.assertGreater(len(chunks), 0)


class TestGetChunker(unittest.TestCase):
    """测试分块器工厂函数"""
    
    def test_get_fixed_chunker(self):
        """测试获取固定分块器"""
        chunker = get_chunker('fixed')
        self.assertIsInstance(chunker, FixedChunker)
    
    def test_get_sentence_chunker(self):
        """测试获取句子分块器"""
        chunker = get_chunker('sentence')
        self.assertIsInstance(chunker, SentenceChunker)
    
    def test_get_semantic_chunker(self):
        """测试获取语义分块器"""
        chunker = get_chunker('semantic')
        self.assertIsInstance(chunker, SemanticChunker)
    
    def test_default_to_fixed(self):
        """测试未知策略默认使用固定分块"""
        chunker = get_chunker('unknown')
        self.assertIsInstance(chunker, FixedChunker)
    
    def test_chunk_parameters(self):
        """测试分块参数传递"""
        chunker = get_chunker('fixed', chunk_size=500, chunk_overlap=100)
        self.assertEqual(chunker.chunk_size, 500)
        self.assertEqual(chunker.chunk_overlap, 100)


class TestDocumentLoader(unittest.TestCase):
    """测试 document_loader 中的分块函数"""
    
    def setUp(self):
        self.sample_text = """
知识库是一种用于存储和组织知识的系统。它可以帮助用户快速查找和获取所需的信息。
知识库通常包含结构化和非结构化的数据，如文档、文章、问答对等。
"""
        self.docs = [Document(page_content=self.sample_text.strip(), metadata={"source": "test"})]
    
    def test_split_document_default(self):
        """测试默认分块函数"""
        chunks = split_document(self.docs)
        
        self.assertGreater(len(chunks), 0)
        for chunk in chunks:
            self.assertIsInstance(chunk, Document)
    
    def test_split_document_with_params(self):
        """测试带参数的分块函数"""
        chunks = split_document(self.docs, chunk_size=100, chunk_overlap=20)
        
        self.assertGreater(len(chunks), 0)
    
    def test_split_document_with_strategy_fixed(self):
        """测试使用策略分块 - fixed"""
        chunks = split_document_with_strategy(
            self.docs,
            strategy='fixed',
            chunk_size=100,
            chunk_overlap=20
        )
        
        self.assertGreater(len(chunks), 0)
    
    def test_split_document_with_strategy_sentence(self):
        """测试使用策略分块 - sentence"""
        chunks = split_document_with_strategy(
            self.docs,
            strategy='sentence',
            chunk_size=100,
            chunk_overlap=20
        )
        
        self.assertGreater(len(chunks), 0)
    
    def test_split_document_with_strategy_semantic(self):
        """测试使用策略分块 - semantic"""
        chunks = split_document_with_strategy(
            self.docs,
            strategy='semantic',
            chunk_size=100,
            chunk_overlap=20
        )
        
        self.assertGreater(len(chunks), 0)


class TestChunkQuality(unittest.TestCase):
    """测试分块质量"""
    
    def test_no_content_loss(self):
        """测试内容不丢失"""
        original_text = "这是第一句。这是第二句。这是第三句。这是第四句。"
        doc = Document(page_content=original_text, metadata={"source": "test"})
        
        chunker = FixedChunker(chunk_size=20, chunk_overlap=5)
        chunks = chunker.split([doc])
        
        combined = "".join(c.page_content for c in chunks)
        self.assertIn("第一句", combined)
        self.assertIn("第四句", combined)
    
    def test_metadata_preserved(self):
        """测试元数据保留"""
        doc = Document(
            page_content="测试内容，用于验证元数据是否正确保留。",
            metadata={"source": "test_file.txt", "author": "test"}
        )
        
        chunker = FixedChunker(chunk_size=20, chunk_overlap=5)
        chunks = chunker.split([doc])
        
        for chunk in chunks:
            self.assertEqual(chunk.metadata.get("source"), "test_file.txt")


if __name__ == "__main__":
    unittest.main(verbosity=2)
