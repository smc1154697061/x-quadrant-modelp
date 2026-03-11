import os
import io
import traceback

import numpy as np
from PIL import Image
from common import log_
from common.error_codes import OCRError, ErrorCode, FileError
from config.base import TESSERACT_PATH, OCR_LANGUAGES, MAX_PDF_PAGES
from config.base import IMAGE_PREPROCESS, INVERT_COLORS, SUPPORTED_TYPES
import subprocess

# 保存需要按需导入的模块，减少不必要的依赖加载
OPTIONAL_MODULES = {
    'docx': None,
    'markdown': None,
    'PyPDF2': None,
    'pdf2image': None,
    'easyocr': None
}

def load_module(name):
    """按需加载模块"""
    global OPTIONAL_MODULES
    if OPTIONAL_MODULES[name] is None:
        try:
            if name == 'pdf2image':
                from pdf2image import convert_from_path, convert_from_bytes
                OPTIONAL_MODULES[name] = {'convert_from_path': convert_from_path, 'convert_from_bytes': convert_from_bytes}
            else:
                OPTIONAL_MODULES[name] = __import__(name)
        except ImportError:
            log_.error(f"未能加载模块: {name}，请确保已安装此依赖")
            raise ImportError(f"请安装依赖: pip install {name}")
    return OPTIONAL_MODULES[name]

class DocumentExtractor:
    """
    文档内容提取工具类 - 支持多种文件格式的内容提取
    支持格式：
    - 文本文件（.txt, .text等）
    - Word文档（.docx, .doc）
    - Markdown文件（.md, .markdown）
    - PDF文件（.pdf）
    - 图片文件（.jpg, .jpeg, .png, .bmp, .tiff, .tif, .gif）
    """
    
    def __init__(self):
        """初始化文档提取器"""
        self.tesseract_path = TESSERACT_PATH
        self.ocr_languages = OCR_LANGUAGES
        self.max_pdf_pages = MAX_PDF_PAGES
        self.image_preprocess = IMAGE_PREPROCESS
        self.invert_colors = INVERT_COLORS
        self.supported_types = SUPPORTED_TYPES
    
    def get_file_type(self, file_name):
        """
        通过文件名确定文件类型
        
        Args:
            file_name: 文件名
            
        Returns:
            str: 文件类型（'text', 'word', 'markdown', 'pdf', 'image' 或 'unknown'）
        """
        ext = os.path.splitext(file_name)[1].lower()
        
        for file_type, extensions in self.supported_types.items():
            if ext in extensions:
                return file_type
        
        return "unknown"
    
    def extract_content(self, file_object, file_type=None):
        """
        从文件中提取文本内容
        
        Args:
            file_object: 文件对象、文件路径或二进制数据
            file_type: 文件类型，如果为None则尝试从文件名推断
            
        Returns:
            str: 提取的文本内容
        """
        try:
            # 确定文件类型
            if file_type is None:
                if hasattr(file_object, 'filename'):
                    file_name = file_object.filename
                    file_type = self.get_file_type(file_name)
                elif isinstance(file_object, str) and os.path.exists(file_object):
                    file_type = self.get_file_type(file_object)
                else:
                    file_type = "unknown"
            
            # 全局异常处理
            try:
                # 根据文件类型选择不同的处理方法
                if file_type == "text":
                    content = self._extract_from_text(file_object)
                elif file_type == "word":
                    content = self._extract_from_docx(file_object)
                elif file_type == "markdown":
                    content = self._extract_from_markdown(file_object)
                elif file_type == "pdf":
                    content = self._extract_from_pdf(file_object)
                elif file_type == "image":
                    content = self._extract_from_image(file_object)
                else:
                    # 未知类型，尝试作为文本处理
                    log_.warning(f"未知文件类型: {file_type}，尝试作为文本处理")
                    content = self._extract_from_text(file_object)
            except Exception as e:
                log_.error(f"内容提取失败: {str(e)}")
                raise
            
            return content
            
        except (OCRError, FileError) as e:
            # 对于已知的业务错误，直接抛出而不是返回错误信息
            log_.error(f"内容提取失败: {str(e)}")
            raise
        except Exception as e:
            log_.error(f"文件处理失败: {str(e)}")
            raise OCRError(ErrorCode.OCR_PROCESS_ERROR, msg=f"提取失败: {str(e)}")
    
    def _extract_from_text(self, file_object):
        """从文本文件提取内容"""
        if isinstance(file_object, str):
            # 如果是文件路径
            if os.path.exists(file_object):
                with open(file_object, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            else:
                # 如果是字符串内容
                return file_object
        elif hasattr(file_object, 'read'):
            # 如果是文件对象，直接读取
            content = file_object.read()
            # 如果是二进制内容，尝试解码
            if isinstance(content, bytes):
                return content.decode('utf-8', errors='ignore')
            return content
        else:
            # 假设是字符串或二进制数据
            if isinstance(file_object, bytes):
                return file_object.decode('utf-8', errors='ignore')
            return str(file_object)
    
    def _extract_from_docx(self, file_object):
        """从Word文档提取内容"""
        import tempfile
        
        if not file_object:
            raise FileError(ErrorCode.FILE_NOT_FOUND, msg="文件对象或路径为空")
            
        try:
            # 加载模块并更详细的记录日志
            docx = load_module("docx")
            temp_file = None
            
            if isinstance(file_object, str) and os.path.exists(file_object):
                # 如果是文件路径，直接使用
                log_.debug(f"使用文件路径处理Word文档: {file_object}")
                doc = docx.Document(file_object)
            else:
                # 对于文件对象或二进制数据，先保存到临时文件
                temp_fd, temp_path = tempfile.mkstemp(suffix='.docx')
                temp_file = temp_path
                
                if hasattr(file_object, 'read'):
                    # 如果是文件对象
                    content = file_object.read()
                    if not isinstance(content, bytes):
                        log_.error("文件对象内容不是二进制格式，无法处理docx文件")
                        raise FileError(ErrorCode.FILE_READ_ERROR, msg="文件对象内容格式错误")
                else:
                    # 假设是二进制数据
                    content = file_object

                # 验证文件头（docx文件应该以PK开头）
                if isinstance(content, bytes) and not content.startswith(b'PK'):
                    log_.error("文件头不符合docx格式（应该以PK开头）")
                    raise FileError(ErrorCode.FILE_READ_ERROR, msg="文件格式错误：不是有效的docx文件")
                
                # 写入临时文件
                with os.fdopen(temp_fd, 'wb') as tmp:
                    tmp.write(content)
                
                # 从临时文件读取文档
                try:
                    doc = docx.Document(temp_path)
                except Exception as e:
                    log_.error(f"python-docx加载Word文档失败: {str(e)}")
                    log_.error(f"错误详情: {traceback.format_exc()}")
                    raise FileError(ErrorCode.FILE_READ_ERROR, msg=f"Word文档解析失败: {str(e)}")
            
            # 提取所有段落文本
            log_.debug("开始提取Word文档中的段落")
            full_text = []
            para_count = 0
            
            for para in doc.paragraphs:
                para_count += 1
                if para_count % 100 == 0:
                    log_.debug(f"已处理 {para_count} 个段落")
                full_text.append(para.text)
            
            log_.debug(f"成功提取 {para_count} 个段落")
            
            # 返回连接后的文本
            result = '\n'.join(full_text)

            # 验证提取的内容是否是有效文本（不是二进制数据）
            if result.startswith('PK') or len([c for c in result[:100] if ord(c) < 32 and c not in '\n\r\t']) > 10:
                log_.error("提取的内容疑似为二进制数据，docx处理可能失败")
                raise FileError(ErrorCode.FILE_READ_ERROR, msg="Word文档处理失败：提取到的是二进制数据而非文本")
            
            # 输出前200字符用于调试
            preview = result[:200].replace('\n', '\\n').replace('\r', '\\r')

            return result
            
        except Exception as e:
            log_.error(f"Word文档处理失败: {str(e)}")
            log_.error(f"详细错误信息: {traceback.format_exc()}")
            # 抛出FileError而不是返回错误字符串
            raise FileError(ErrorCode.FILE_READ_ERROR, msg=f"Word文档处理失败: {str(e)}")
        finally:
            # 清理临时文件
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    log_.debug(f"临时文件已删除: {temp_file}")
                except Exception as e:
                    log_.warning(f"删除临时文件失败: {str(e)}")
    
    def _is_valid_text_line(self, line):
        """判断是否是有效的文本行（包含中文、英文单词等）"""
        if not line or not line.strip():
            return True  # 空行认为是有效的
        
        line = line.strip()
        
        # 如果包含中文字符，认为是有效的
        if any('\u4e00' <= c <= '\u9fff' for c in line):
            return True
        
        # 如果包含常见的英文单词模式，认为是有效的
        import re
        if re.search(r'\b[a-zA-Z]{2,}\b', line):  # 包含2个或更多字母的单词
            return True
        
        # 如果包含数字和字母的组合（但不是纯随机字符），认为是有效的
        if re.search(r'\d+', line) and len(line) < 50 and ' ' in line:
            return True
        
        # 如果是纯数字、日期等格式，认为是有效的
        if re.match(r'^[\d\-/\s\.,]+$', line):
            return True
        
        # 其他情况，如果行太长且包含大量随机字符，可能是垃圾
        if len(line) > 30 and not re.search(r'[aeiouAEIOU]', line):  # 没有元音字母的长行可能是垃圾
            return False
        
        return True  # 默认认为是有效的
    
    def _extract_from_markdown(self, file_object):
        """从Markdown文件提取内容"""
        # Markdown直接作为文本处理即可，无需转换
        return self._extract_from_text(file_object)
    
    def _extract_from_pdf(self, file_object):
        """
        从PDF文件提取内容，先判断类型再走对应分支
        """
        import tempfile

        # 1) 将流/二进制写入临时PDF文件
        if isinstance(file_object, str) and os.path.exists(file_object):
            pdf_path = file_object
        else:
            fd, pdf_path = tempfile.mkstemp(suffix=".pdf")
            with os.fdopen(fd, "wb") as f:
                data = file_object.read() if hasattr(file_object, "read") else file_object
                f.write(data)

        try:
            # 2) 判断是文字型还是扫描型
            if self._is_scanned_pdf(pdf_path):
                return self._extract_from_pdf_with_ocr(pdf_path)
            else:
                return self._extract_text_only_pdf(pdf_path)
        finally:
            # 删除临时文件
            if os.path.exists(pdf_path) and pdf_path != file_object:
                try: os.remove(pdf_path)
                except: pass

    def _is_scanned_pdf(self, pdf_path):
        """
        判断PDF是否为扫描版。调用 pdffonts：
        如果输出行数 <= 2 (只有表头)，说明没有嵌入字体。
        """
        try:
            proc = subprocess.run(
                ["pdffonts", pdf_path],
                capture_output=True, text=True, check=True
            )
            lines = proc.stdout.strip().splitlines()
            # 前两行是表头，如果后面没有字体条目则认为扫描版
            return len(lines) <= 2
        except Exception as e:
            log_.warning(f"pdffonts 检测失败，回退至简单文本检测: {e}")
            return not self._is_text_pdf_simple(pdf_path)

    def _is_text_pdf_simple(self, pdf_path):
        """
        回退检测：尝试提取第1页文本，若长度足够则认为文字型PDF
        """
        try:
            PyPDF2 = load_module("PyPDF2")
            reader = PyPDF2.PdfReader(pdf_path)
            txt = reader.pages[0].extract_text() or ""
            return len(txt.strip()) > 0
        except:
            return False

    def _extract_text_only_pdf(self, pdf_path):
        """
        只用 PyPDF2 提取文字，不走 OCR
        """
        PyPDF2 = load_module("PyPDF2")
        text = []
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            page_count = min(len(reader.pages), self.max_pdf_pages)
            for i in range(page_count):
                text.append(reader.pages[i].extract_text() or "")
        content = "\n".join(text)
        if len(content.strip()) < 1:
            log_.warning("文字型PDF提取到的文本为空或过少")
        return content

    def _extract_from_pdf_with_ocr(self, file_object):
        """使用OCR从PDF文件提取内容（优化版）"""
        try:
            # 加载必要模块
            pdf2image = load_module("pdf2image")
            easyocr = load_module("easyocr")

            # 语言代码转换（兼容旧配置）
            lang_mapping = {
                'chi_sim': 'ch_sim',
                'eng': 'en'
            }

            ocr_langs = []
            for lang in self.ocr_languages:
                ocr_langs.append(lang_mapping.get(lang, lang))

            # 初始化Reader（使用CPU模式）
            try:
                reader = easyocr.Reader(ocr_langs, gpu=False)
            except Exception as e:
                log_.error(f"EasyOCR初始化失败: {str(e)}")
                raise OCRError(ErrorCode.OCR_PROCESS_ERROR, msg=f"OCR初始化失败: {str(e)}")

            # 转换参数
            dpi = 100  # 降低DPI提高处理速度
            max_side = 1024  # 限制图像最大边长

            # PDF转为图片
            try:
                if isinstance(file_object, str) and os.path.exists(file_object):
                    # 如果是文件路径
                    images = pdf2image["convert_from_path"](
                        file_object,
                        dpi=dpi,
                        first_page=1,
                        last_page=self.max_pdf_pages
                    )
                elif hasattr(file_object, 'read'):
                    # 如果是文件对象
                    images = pdf2image["convert_from_bytes"](
                        file_object.read(),
                        dpi=dpi
                    )
                else:
                    # 二进制数据
                    images = pdf2image["convert_from_bytes"](
                        file_object,
                        dpi=dpi
                    )
            except Exception as e:
                log_.error(f"PDF转图片失败: {str(e)}")
                raise OCRError(ErrorCode.OCR_PROCESS_ERROR, msg=f"PDF转图片失败: {str(e)}")

            # 对每一页进行OCR处理
            text = []
            for i, pil_img in enumerate(images):
                try:
                    # 限制最大尺寸，避免内存暴涨
                    w, h = pil_img.size
                    if max(w, h) > max_side:
                        pil_img.thumbnail((max_side, max_side))  # 等比例缩放

                    # 转为numpy数组（RGB）直接处理，避免临时文件
                    img_array = np.array(pil_img)

                    # 使用EasyOCR识别文本
                    results = reader.readtext(img_array)

                    # 提取文本内容
                    texts = [text for _, text, confidence in results if confidence > 0.01]
                    page_text = '\n'.join(texts)
                    text.append(page_text)

                    # 及时释放大对象，降低峰值内存
                    del img_array, results

                except Exception as e:
                    log_.error(f"OCR处理PDF页面失败: {str(e)}")
                    text.append(f"[页面OCR失败] {str(e)}")

                # 释放图片内存
                del pil_img

            return '\n\n'.join(text)

        except Exception as e:
            log_.error(f"PDF OCR处理失败: {str(e)}")
            raise OCRError(ErrorCode.OCR_PROCESS_ERROR, msg=f"PDF OCR处理失败: {str(e)}")
    
    def _extract_from_image(self, file_object):
        """从图片提取文本（OCR）"""
        try:
            # 加载easyocr
            easyocr = load_module("easyocr")
            
            # 语言代码转换（兼容旧配置）
            lang_mapping = {
                'chi_sim': 'ch_sim',
                'eng': 'en'
            }
            
            ocr_langs = []
            for lang in self.ocr_languages:
                ocr_langs.append(lang_mapping.get(lang, lang))
            
            # 初始化Reader
            try:
                reader = easyocr.Reader(ocr_langs)
            except Exception as e:
                log_.error(f"EasyOCR初始化失败: {str(e)}")
                raise OCRError(ErrorCode.OCR_PROCESS_ERROR, msg=f"OCR初始化失败: {str(e)}")
            
            # 加载图片
            if isinstance(file_object, str) and os.path.exists(file_object):
                # 如果是文件路径
                image_path = file_object
            elif hasattr(file_object, 'read'):
                # 如果是文件对象，保存到临时文件
                import tempfile
                tmp_fd, tmp_path = tempfile.mkstemp(suffix='.jpg')
                try:
                    with os.fdopen(tmp_fd, 'wb') as f:
                        content = file_object.read() if callable(getattr(file_object, 'read', None)) else file_object
                        if not isinstance(content, bytes):
                            content = content.encode('utf-8')
                        f.write(content)
                    image_path = tmp_path
                except Exception as e:
                    log_.error(f"保存临时文件失败: {str(e)}")
                    raise FileError(ErrorCode.FILE_WRITE_ERROR, msg=f"无法保存临时文件: {str(e)}")
            else:
                # 假设是二进制数据，保存到临时文件
                import tempfile
                tmp_fd, tmp_path = tempfile.mkstemp(suffix='.jpg')
                try:
                    with os.fdopen(tmp_fd, 'wb') as f:
                        f.write(file_object)
                    image_path = tmp_path
                except Exception as e:
                    log_.error(f"保存临时文件失败: {str(e)}")
                    raise FileError(ErrorCode.FILE_WRITE_ERROR, msg=f"无法保存临时文件: {str(e)}")
            
            # 使用EasyOCR进行文本识别
            try:
                results = reader.readtext(image_path)
                
                # 提取文本内容
                texts = [text for _, text, confidence in results if confidence > 0.01]  # 降低阈值
                full_text = '\n'.join(texts)

                # 删除临时文件
                if 'tmp_path' in locals() and os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except Exception as e:
                        log_.warning(f"删除临时文件失败: {str(e)}")
                
                return full_text
            except Exception as e:
                log_.error(f"EasyOCR处理失败: {str(e)}")
                raise OCRError(ErrorCode.OCR_PROCESS_ERROR, msg=f"OCR处理失败: {str(e)}")
            
        except ImportError as e:
            log_.error(f"EasyOCR模块加载失败: {str(e)}")
            raise ImportError(f"请安装EasyOCR: pip install easyocr")
        except Exception as e:
            log_.error(f"图片处理失败: {str(e)}")
            if "Cannot open" in str(e) or "cannot identify image file" in str(e):
                raise FileError(ErrorCode.FILE_READ_ERROR, msg=f"无法打开或识别图像文件: {str(e)}")
            else:
                raise OCRError(ErrorCode.OCR_PROCESS_ERROR, msg=f"OCR处理失败: {str(e)}")


# 创建一个全局实例，方便直接导入使用
extractor = DocumentExtractor()

# 便捷函数，使用全局实例提取内容
def extract_content(file_object, file_type=None):
    """从文件中提取文本内容（便捷函数）

    Args:
        file_object: 文件对象、文件路径或二进制数据
        file_type: 文件类型，可以是规范类型（text/word/pdf/...）或扩展名（docx/txt/...）

    Returns:
        str: 提取的文本内容
    """

    # 先规范化 file_type，支持直接传入扩展名（如 docx、txt 等）
    if file_type is not None:
        ft = str(file_type).lower()
        # 常见扩展名映射到内部类型
        if ft in ['doc', 'docx']:
            file_type = 'word'
        elif ft in ['txt', 'text', 'log', 'csv']:
            file_type = 'text'
        elif ft in ['md', 'markdown']:
            file_type = 'markdown'
        elif ft == 'pdf':
            file_type = 'pdf'
        elif ft in ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'tif', 'gif']:
            file_type = 'image'

    # 如果已提供规范化后的文件类型，直接调用底层提取器
    if file_type in ['text', 'word', 'markdown', 'pdf', 'image']:
        return extractor.extract_content(file_object, file_type)

    # 尝试从文件对象中推断类型（在 file_type 未提供或无法识别时）
    if file_type is None and hasattr(file_object, 'name'):
        _, ext = os.path.splitext(file_object.name)
        ext = ext.lower()
        if ext in ['.docx', '.doc']:
            file_type = 'word'
        elif ext in ['.pdf']:
            file_type = 'pdf'
        elif ext in ['.txt', '.text', '.log', '.csv']:
            file_type = 'text'
        elif ext in ['.md', '.markdown']:
            file_type = 'markdown'
        elif ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif']:
            file_type = 'image'

    # 如果仍然无法推断文件类型，且也不是简单字符串/二进制，则抛出异常
    if file_type is None and not isinstance(file_object, (str, bytes)) and not hasattr(file_object, 'filename'):
        log_.error("无法推断文件类型且未提供文件类型")
        raise FileError(ErrorCode.FILE_TYPE_ERROR, msg="无法推断文件类型且未提供文件类型")

    try:
        content = extractor.extract_content(file_object, file_type)
        return content
    except (FileError, OCRError) as e:
        # 错误处理
        log_.error(f"内容提取失败: {str(e)}")
        raise
