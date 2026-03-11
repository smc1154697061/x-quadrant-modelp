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
from common.document_extractor import extract_content

# 文本分割器配置
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200

# 文件扩展名到加载器的映射
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

# 图片文件扩展名列表
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif'}

def load_document(file_path: str) -> List[Document]:
    """
    根据文件类型加载文档，支持图片OCR解析
    
    Args:
        file_path: 文件路径
        
    Returns:
        List[Document]: 文档对象列表
    """
    # 获取文件扩展名
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    # 检查文件是否为空
    if os.path.getsize(file_path) == 0:
        raise ValueError(f"文件为空: {file_path}")
    
    # 处理图片文件 - 使用OCR提取文字
    if ext in IMAGE_EXTENSIONS:
        try:
            log_.info(f"检测到图片文件，使用OCR提取文字: {file_path}")
            # 使用document_extractor提取图片中的文字
            extracted_text = extract_content(file_path, file_type='image')
            
            if not extracted_text or extracted_text.strip() == '':
                log_.warning(f"图片中未识别到文字: {file_path}")
                extracted_text = "[图片中未识别到文字内容]"
            
            # 创建Document对象
            doc = Document(
                page_content=extracted_text,
                metadata={
                    'source': file_path,
                    'file_type': 'image',
                    'file_extension': ext
                }
            )
            log_.info(f"图片OCR解析成功，提取文字长度: {len(extracted_text)}")
            return [doc]
        except Exception as e:
            log_.error(f"图片OCR解析失败 {file_path}: {str(e)}")
            # 返回一个包含错误信息的文档，而不是抛出异常
            doc = Document(
                page_content=f"[图片解析失败: {str(e)}]",
                metadata={
                    'source': file_path,
                    'file_type': 'image',
                    'file_extension': ext,
                    'error': str(e)
                }
            )
            return [doc]
    
    # 根据文件类型选择加载器
    if ext in LOADERS:
        loader_cls = LOADERS[ext]
        try:
            loader = loader_cls(file_path)
            docs = loader.load()
            return docs
        except Exception as e:
            log_.error(f"加载文件 {file_path} 失败: {str(e)}")
            # 尝试使用文本加载器作为后备方案
            try:
                loader = TextLoader(file_path, encoding='utf-8')
                return loader.load()
            except Exception as e2:
                log_.error(f"使用文本加载器加载 {file_path} 失败: {str(e2)}")
                raise ValueError(f"无法加载文件: {str(e2)}")
    else:
        # 不支持的文件类型
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
    # 创建文本分割器
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    
    # 分割文档
    chunks = text_splitter.split_documents(docs)
    
    return chunks