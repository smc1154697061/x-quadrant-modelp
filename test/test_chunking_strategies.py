#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试三种分块策略效果的脚本
"""
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

class MockLogger:
    def error(self, msg):
        print(f"[ERROR] {msg}")
    def warning(self, msg):
        print(f"[WARNING] {msg}")
    def info(self, msg):
        print(f"[INFO] {msg}")
    def debug(self, msg):
        pass

import types
mock_common = types.ModuleType('common')
mock_common.log_ = MockLogger()
sys.modules['common'] = mock_common
sys.modules['common.log_'] = mock_common.log_

from abc import ABC, abstractmethod
from typing import List
from langchain.schema import Document
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    SentenceTransformersTokenTextSplitter,
    TextSplitter
)

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200
log_ = MockLogger()


class BaseChunker(ABC):
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size if chunk_size is not None else DEFAULT_CHUNK_SIZE
        self.chunk_overlap = chunk_overlap if chunk_overlap is not None else DEFAULT_CHUNK_OVERLAP
    
    @abstractmethod
    def chunk(self, documents: List[Document]) -> List[Document]:
        pass


class FixedChunker(BaseChunker):
    def chunk(self, documents: List[Document]) -> List[Document]:
        try:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
            return text_splitter.split_documents(documents)
        except Exception as e:
            log_.error(f"固定长度分块失败: {str(e)}")
            raise


class SemanticChunker(BaseChunker):
    def chunk(self, documents: List[Document]) -> List[Document]:
        try:
            try:
                from langchain_experimental.text_splitter import SemanticChunker
                from langchain.embeddings import HuggingFaceEmbeddings
                
                embeddings = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2"
                )
                
                text_splitter = SemanticChunker(
                    embeddings,
                    chunk_size=self.chunk_size
                )
                return text_splitter.split_documents(documents)
            except ImportError:
                log_.warning("未安装langchain_experimental，使用固定长度分块作为替代")
                return FixedChunker(self.chunk_size, self.chunk_overlap).chunk(documents)
        except Exception as e:
            log_.error(f"语义分块失败: {str(e)}，使用固定长度分块作为替代")
            return FixedChunker(self.chunk_size, self.chunk_overlap).chunk(documents)


class SentenceChunker(BaseChunker):
    def chunk(self, documents: List[Document]) -> List[Document]:
        try:
            import nltk
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                nltk.download('punkt')
            
            combined_text = ""
            for doc in documents:
                combined_text += doc.page_content + "\n\n"
            
            sentences = nltk.sent_tokenize(combined_text)
            
            chunks = []
            current_chunk = ""
            current_chars = 0
            
            for sentence in sentences:
                sentence_len = len(sentence)
                
                if current_chars + sentence_len > self.chunk_size and current_chunk:
                    chunks.append(Document(page_content=current_chunk.strip()))
                    overlap_text = ""
                    overlap_chars = 0
                    sentences_list = nltk.sent_tokenize(current_chunk)
                    for s in reversed(sentences_list):
                        if overlap_chars + len(s) <= self.chunk_overlap:
                            overlap_text = s + " " + overlap_text
                            overlap_chars += len(s) + 1
                        else:
                            break
                    current_chunk = overlap_text
                    current_chars = overlap_chars
                
                current_chunk += sentence + " "
                current_chars += sentence_len + 1
            
            if current_chunk.strip():
                chunks.append(Document(page_content=current_chunk.strip()))
            
            return chunks
        except Exception as e:
            log_.error(f"句子分块失败: {str(e)}，使用固定长度分块作为替代")
            return FixedChunker(self.chunk_size, self.chunk_overlap).chunk(documents)


def get_chunker(strategy: str = 'fixed', chunk_size: int = None, chunk_overlap: int = None) -> BaseChunker:
    strategy = strategy.lower() if strategy else 'fixed'
    
    chunkers = {
        'fixed': FixedChunker,
        'semantic': SemanticChunker,
        'sentence': SentenceChunker
    }
    
    chunker_class = chunkers.get(strategy, FixedChunker)
    return chunker_class(chunk_size, chunk_overlap)


TEST_TEXT = """
人工智能（Artificial Intelligence，简称AI）是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。
该领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。人工智能从诞生以来，理论和技术日益成熟，应用领域也不断扩大。
可以设想，未来人工智能带来的科技产品，将会是人类智慧的“容器”。人工智能可以对人的意识、思维的信息过程的模拟。人工智能不是人的智能，但能像人那样思考、也可能超过人的智能。

机器学习是人工智能的一个子集，它使用统计方法使计算机能够从数据中学习。深度学习又是机器学习的一个子集，它使用多层神经网络来模拟人脑的学习过程。
近年来，随着计算能力的提升和大数据的积累，深度学习在图像识别、语音识别、自然语言处理等领域取得了突破性进展。

自然语言处理（NLP）是人工智能的重要方向之一，它研究如何让计算机理解和处理人类语言。
RAG（检索增强生成）是当前NLP领域的热门技术，它结合了信息检索和生成模型的优势，能够提供更准确、更可靠的回答。
RAG系统通常包含三个核心步骤：文档分块、向量存储和检索增强生成。
"""

def create_test_document():
    return [Document(page_content=TEST_TEXT.strip())]

def test_fixed_chunker():
    print("=" * 60)
    print("测试 FixedChunker (固定长度分块器)")
    print("=" * 60)
    
    docs = create_test_document()
    chunker = FixedChunker(chunk_size=200, chunk_overlap=50)
    chunks = chunker.chunk(docs)
    
    print(f"文档总长度: {len(docs[0].page_content)} 字符")
    print(f"分块数量: {len(chunks)}")
    print("-" * 60)
    
    for i, chunk in enumerate(chunks, 1):
        print(f"[块 {i}] 长度: {len(chunk.page_content)}")
        preview = chunk.page_content[:50].replace('\n', ' ') + "..."
        print(f"     预览: {preview}")
    print()

def test_sentence_chunker():
    print("=" * 60)
    print("测试 SentenceChunker (句子分块器)")
    print("=" * 60)
    
    docs = create_test_document()
    chunker = SentenceChunker(chunk_size=200, chunk_overlap=50)
    chunks = chunker.chunk(docs)
    
    print(f"文档总长度: {len(docs[0].page_content)} 字符")
    print(f"分块数量: {len(chunks)}")
    print("-" * 60)
    
    for i, chunk in enumerate(chunks, 1):
        print(f"[块 {i}] 长度: {len(chunk.page_content)}")
        preview = chunk.page_content[:50].replace('\n', ' ') + "..."
        print(f"     预览: {preview}")
    print()

def test_semantic_chunker():
    print("=" * 60)
    print("测试 SemanticChunker (语义分块器)")
    print("=" * 60)
    
    docs = create_test_document()
    chunker = SemanticChunker(chunk_size=200, chunk_overlap=50)
    chunks = chunker.chunk(docs)
    
    print(f"文档总长度: {len(docs[0].page_content)} 字符")
    print(f"分块数量: {len(chunks)}")
    print("-" * 60)
    
    for i, chunk in enumerate(chunks, 1):
        print(f"[块 {i}] 长度: {len(chunk.page_content)}")
        preview = chunk.page_content[:50].replace('\n', ' ') + "..."
        print(f"     预览: {preview}")
    print()

def test_factory_function():
    print("=" * 60)
    print("测试工厂函数 get_chunker")
    print("=" * 60)
    
    strategies = ['fixed', 'semantic', 'sentence', 'invalid_strategy']
    
    for strategy in strategies:
        chunker = get_chunker(strategy, chunk_size=300, chunk_overlap=50)
        print(f"策略 '{strategy}' -> 分块器类型: {type(chunker).__name__}")
    print()

def main():
    print("分块策略测试脚本")
    print(f"测试文本长度: {len(TEST_TEXT.strip())} 字符")
    print()
    
    test_fixed_chunker()
    test_sentence_chunker()
    test_semantic_chunker()
    test_factory_function()
    
    print("=" * 60)
    print("所有测试完成!")
    print("=" * 60)

if __name__ == "__main__":
    main()
