import os
import urllib.request
import time
import hashlib
from common import log_
import requests
import shutil
import urllib.parse
import re
import base64
import tempfile

def download_from_minio_url(url, temp_dir='./data/minio', clean_dir=True, keep_extension=True):
    """从MinIO URL下载文件到指定目录
    
    Args:
        url: MinIO对象的URL
        temp_dir: 下载目录路径，默认为'./data/minio'
        clean_dir: 是否清空下载目录
        keep_extension: 是否保留文件扩展名
        
    Returns:
        tuple: (本地文件路径, 文件名)
    """
    # 确保下载目录存在
    os.makedirs(temp_dir, exist_ok=True)
    
    # 如果需要清空下载目录
    if clean_dir:
        for file in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, file)
            if os.path.isfile(file_path):
                try:
                    os.unlink(file_path)
                except Exception as e:
                    log_.warning(f"无法删除文件 {file_path}: {str(e)}")
    
    try:
        # 生成唯一的临时文件名
        timestamp = int(time.time())
        temp_filename = f"file_{timestamp}"
        temp_path = os.path.join(temp_dir, temp_filename)
        
        # 获取响应
        response = requests.get(url, stream=True)
        response.raise_for_status()  # 检查响应状态
        
        # 确定文件扩展名和最终文件名
        file_ext, final_filename = _get_file_info_from_response(url, response)
        
        # 如果需要保留扩展名
        if keep_extension and file_ext:
            final_path = temp_path + file_ext
        else:
            final_path = temp_path
        
        # 下载文件到本地
        with open(final_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        return final_path, final_filename
    
    except Exception as e:
        log_.error(f"从URL下载文件失败: {str(e)}")
        raise

def _get_file_info_from_response(url, response):
    """从响应和URL中提取文件信息
    
    Args:
        url: 下载URL
        response: 请求响应对象
        
    Returns:
        tuple: (文件扩展名, 文件名)
    """
    # 1. 尝试从Content-Disposition获取文件名和扩展名
    content_disposition = response.headers.get('Content-Disposition', '')
    filename_match = re.search(r'filename="?([^"]+)"?', content_disposition)
    
    if filename_match:
        original_filename = filename_match.group(1)
        original_filename = urllib.parse.unquote(original_filename)
        file_ext = os.path.splitext(original_filename)[1].lower()
        return file_ext, original_filename
    
    # 2. 尝试从URL解析文件名
    try:
        # 检查是否是Base64编码的URL
        if '/download-shared-object/' in url:
            encoded_part = url.split('/download-shared-object/')[1].split('?')[0] 
            try:
                # 尝试Base64解码
                decoded_url = base64.b64decode(encoded_part).decode('utf-8')
                test_match = re.search(r'test/([^?]+)', decoded_url)
                if test_match:
                    original_filename = test_match.group(1)
                    original_filename = urllib.parse.unquote(original_filename)
                    file_ext = os.path.splitext(original_filename)[1].lower()
                    return file_ext, original_filename
            except Exception as e:
                log_.warning(f"Base64解码URL失败: {str(e)}")
                
        # 直接从URL中提取
        parsed_url = urllib.parse.unquote(url)
        test_match = re.search(r'test/([^?]+)', parsed_url)
        if test_match:
            original_filename = test_match.group(1)
            file_ext = os.path.splitext(original_filename)[1].lower()
            return file_ext, original_filename
    except Exception as e:
        log_.warning(f"从URL解析文件名失败: {str(e)}")
    
    # 3. 从Content-Type判断文件类型
    content_type = response.headers.get('Content-Type', '')
    content_type_map = {
        'application/pdf': '.pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
        'application/msword': '.doc',
        'text/plain': '.txt',
        'image/jpeg': '.jpg',
        'image/png': '.png'
    }
    
    file_ext = content_type_map.get(content_type, '.bin')  # 默认二进制文件
    timestamp = int(time.time())
    default_filename = f"file_{timestamp}{file_ext}"
    
    return file_ext, default_filename

def download_and_process_minio_file(url, processor_func, **kwargs):
    """下载MinIO文件并使用提供的函数处理它
    
    Args:
        url: MinIO文件URL
        processor_func: 处理文件的函数，接收文件对象作为第一个参数
        **kwargs: 传递给处理函数的其他参数
        
    Returns:
        处理函数的返回值
    """
    local_path = None
    try:
        # 下载文件
        local_path, _ = download_from_minio_url(url, keep_extension=True)
        
        # 检查文件大小
        file_size = os.path.getsize(local_path)
        if file_size == 0:
            raise Exception("下载的文件为空")
        
        # 处理文件
        with open(local_path, 'rb') as file_object:
            result = processor_func(file_object, **kwargs)
            
        return result
    
    finally:
        # 清理临时文件
        if local_path and os.path.exists(local_path):
            try:
                os.remove(local_path)
            except Exception as e:
                log_.error(f"删除临时文件失败: {str(e)}")