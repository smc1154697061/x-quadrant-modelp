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
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

from common import log_

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif', '.webp'}


class ImageLoader:
    """图片文件加载器 - 使用OCR提取文本"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
    
    def load(self) -> List[Document]:
        from common.document_extractor import extract_content
        
        try:
            text = extract_content(self.file_path, 'image')
            
            if not text or not text.strip():
                log_.warning(f"图片OCR未提取到文本: {self.file_path}")
                text = "[图片内容无法识别]"
            
            metadata = {
                "source": self.file_path,
                "file_type": "image"
            }
            
            return [Document(page_content=text, metadata=metadata)]
        except Exception as e:
            log_.error(f"图片OCR处理失败: {str(e)}")
            return [Document(page_content=f"[图片处理失败: {str(e)}]", metadata={"source": self.file_path, "file_type": "image", "error": True})]


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
    '.pptx': UnstructuredPowerPointLoader,
    '.jpg': ImageLoader,
    '.jpeg': ImageLoader,
    '.png': ImageLoader,
    '.bmp': ImageLoader,
    '.tiff': ImageLoader,
    '.tif': ImageLoader,
    '.gif': ImageLoader,
    '.webp': ImageLoader
}


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


def split_document(docs: List[Document], 
                   chunk_size: int = DEFAULT_CHUNK_SIZE, 
                   chunk_overlap: int = DEFAULT_CHUNK_OVERLAP) -> List[Document]:
    """
    将文档分割成块
    
    Args:
        docs: 文档对象列表
        chunk_size: 块大小
        chunk_overlap: 块重叠大小
        
    Returns:
        List[Document]: 分割后的文档块列表
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    
    chunks = text_splitter.split_documents(docs)
    
    return chunks
