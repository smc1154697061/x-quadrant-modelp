"""
文档加载和处理工具
"""
import os
from typing import List
import tempfile

from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    UnstructuredMarkdownLoader,
    UnstructuredHTMLLoader,
    CSVLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredExcelLoader,
    UnstructuredPowerPointLoader
)
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from common import log_
from common.document_extractor import DocumentExtractor

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200

LOADERS = {
    '.txt': TextLoader,
    '.pdf': PyPDFLoader,
    '.md': UnstructuredMarkdownLoader,
    '.html': UnstructuredHTMLLoader,
    '.htm': UnstructuredHTMLLoader,
    '.csv': CSVLoader,
    '.doc': UnstructuredWordDocumentLoader,
    '.docx': UnstructuredWordDocumentLoader,
    '.xls': UnstructuredExcelLoader,
    '.xlsx': UnstructuredExcelLoader,
    '.ppt': UnstructuredPowerPointLoader,
    '.pptx': UnstructuredPowerPointLoader
}

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}

def load_document(file_path: str) -> List[Document]:
    """
    根据文件类型加载文档
    
    Args:
        file_path: 文件路径
        
    Returns:
        List[Document]: 文档对象列表
    """
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    if os.path.getsize(file_path) == 0:
        raise ValueError(f"文件为空: {file_path}")
    
    if ext in IMAGE_EXTENSIONS:
        try:
            extractor = DocumentExtractor()
            text = extractor.extract_content(file_path, file_type="image")
            return [Document(page_content=text, metadata={"source": file_path})]
        except Exception as e:
            log_.error(f"图片OCR加载失败: {str(e)}")
            return [Document(page_content="[图片文件]", metadata={"source": file_path})]
    
    if ext in LOADERS:
        loader_cls = LOADERS[ext]
        try:
            loader = loader_cls(file_path)
            docs = loader.load()
            return docs
        except Exception as e:
            log_.error(f"加载文件 {file_path} 失败: {str(e)}")
            try:
                loader = TextLoader(file_path, encoding='utf-8')
                return loader.load()
            except Exception as e2:
                log_.error(f"使用文本加载器加载 {file_path} 失败: {str(e2)}")
                raise ValueError(f"无法加载文件: {str(e2)}")
    else:
        raise ValueError(f"不支持的文件类型: {ext}")

def split_document(docs: List[Document], chunk_size: int = None, chunk_overlap: int = None) -> List[Document]:
    """
    分割文档为小块
    
    Args:
        docs: 文档对象列表
        chunk_size: 块大小
        chunk_overlap: 块重叠大小
        
    Returns:
        List[Document]: 分割后的文档块列表
    """
    if chunk_size is None:
        chunk_size = DEFAULT_CHUNK_SIZE
    if chunk_overlap is None:
        chunk_overlap = DEFAULT_CHUNK_OVERLAP
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    
    chunks = text_splitter.split_documents(docs)
    
    return chunks


class DocumentLoader:
    """文档加载器类"""
    
    def load(self, file_path: str) -> str:
        """
        加载文档并返回文本内容
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 文档文本内容
        """
        docs = load_document(file_path)
        if docs:
            # 合并所有文档内容
            return "\n\n".join([doc.page_content for doc in docs])
        return ""
