"""
文件解析工具 - 提取文件内容
"""
import chardet
from common import log_


class FileParser:
    """文件内容解析器"""
    
    @staticmethod
    def parse_txt(file_content: bytes) -> str:
        """解析TXT文件内容
        
        参数:
            file_content: 文件字节内容
        
        返回:
            文本内容
        """
        try:
            # 检测编码
            detected = chardet.detect(file_content)
            encoding = detected['encoding'] or 'utf-8'
            
            # 解码
            text = file_content.decode(encoding, errors='ignore')
            return text.strip()
        except Exception as e:
            log_.error(f"解析TXT文件失败: {str(e)}")
            # 如果检测失败，尝试常见编码
            for encoding in ['utf-8', 'gbk', 'gb2312', 'latin-1']:
                try:
                    text = file_content.decode(encoding, errors='ignore')
                    return text.strip()
                except:
                    continue
            
            raise Exception(f"无法解析文件内容，所有编码尝试都失败")
    
    @staticmethod
    def parse_file(file_content: bytes, file_type: str) -> str:
        """根据文件类型解析文件内容
        
        参数:
            file_content: 文件字节内容
            file_type: 文件类型（txt, pdf, docx等）
        
        返回:
            文本内容
        """
        file_type = file_type.lower()
        
        if file_type in ['txt', 'text']:
            return FileParser.parse_txt(file_content)
        elif file_type in ['md', 'markdown']:
            return FileParser.parse_txt(file_content)
        elif file_type in ['log']:
            return FileParser.parse_txt(file_content)
        elif file_type in ['pdf']:
            # TODO: 后续实现PDF解析
            raise NotImplementedError("PDF文件解析功能暂未实现")
        elif file_type in ['doc', 'docx']:
            # TODO: 后续实现Word解析
            raise NotImplementedError("Word文件解析功能暂未实现")
        elif file_type in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']:
            # 图片不需要解析文本内容
            return "[图片文件]"
        else:
            raise ValueError(f"不支持的文件类型: {file_type}")
    
    @staticmethod
    def is_supported_type(file_type: str) -> bool:
        """检查是否支持该文件类型
        
        参数:
            file_type: 文件类型
        
        返回:
            是否支持
        """
        supported_types = [
            'txt', 'text', 'md', 'markdown', 'log',  # 文本文件
            'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp',  # 图片文件
            # 'pdf', 'doc', 'docx'  # TODO: 后续支持
        ]
        return file_type.lower() in supported_types
