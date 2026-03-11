import os
import io
import tempfile
import time
from minio import Minio
from minio.error import S3Error
from urllib.parse import urlparse
from config.base import MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY
from config.base import MINIO_DEFAULT_BUCKET, MINIO_SECURE
from common import log_

class MinioClient:
    """MinIO客户端类，处理对象存储操作"""
    _instance = None

    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        """初始化MinIO客户端"""
        try:
            # 直接使用与测试文件相同的连接方式
            self.client = Minio(
                MINIO_ENDPOINT.replace("http://", "").replace("https://", ""),  # 移除协议前缀
                access_key=MINIO_ACCESS_KEY,
                secret_key=MINIO_SECRET_KEY,
                secure=MINIO_SECURE
            )

            self.default_bucket = MINIO_DEFAULT_BUCKET
            # 尝试确保存储桶存在，但不要让错误导致应用崩溃
            try:
                self._ensure_bucket_exists(self.default_bucket)
            except Exception as e:
                log_.error(f"MinIO存储桶检查失败，但应用将继续运行: {str(e)}")
        except Exception as e:
            log_.error(f"MinIO客户端初始化失败，但应用将继续运行: {str(e)}")
            self.client = None

    def _ensure_bucket_exists(self, bucket_name):
        """确保桶存在，不存在则创建"""
        max_retries = 3
        retry_delay = 1  # 初始延迟1秒
        
        for attempt in range(max_retries):
            try:
                # 检查客户端是否初始化成功
                if not self.client:
                    log_.error("MinIO客户端未初始化，无法检查桶")
                    raise RuntimeError("MinIO客户端未初始化")
                
                # 检查桶是否存在
                bucket_exists = self.client.bucket_exists(bucket_name)
                
                if not bucket_exists:
                    self.client.make_bucket(bucket_name)
                
                return True
            except S3Error as e:
                log_.error(f"MinIO操作失败 (尝试 {attempt+1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避
                else:
                    log_.error(f"确保桶存在失败，已达到最大重试次数: {str(e)}")
                    raise
            except Exception as e:
                log_.error(f"确保桶存在时发生未预期的错误: {str(e)}")
                raise

    def upload_file(self, file_path, object_name=None, bucket_name=None):
        """上传文件到MinIO
        
        Args:
            file_path: 本地文件路径
            object_name: 对象名称，默认使用文件名
            bucket_name: 桶名称，默认使用配置中的桶
            
        Returns:
            str: 对象URL
        """
        try:
            if not os.path.exists(file_path):
                log_.error(f"文件不存在: {file_path}")
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            bucket_name = bucket_name or self.default_bucket
            object_name = object_name or os.path.basename(file_path)
            
            # 确保桶存在
            self._ensure_bucket_exists(bucket_name)
            
            # 检查文件大小
            file_size = os.path.getsize(file_path)

            # 获取文件MIME类型
            import mimetypes
            content_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
            
            # 上传文件
            self.client.fput_object(
                bucket_name=bucket_name,
                object_name=object_name,
                file_path=file_path,
                content_type=content_type
            )
            
            # 验证文件是否成功上传
            try:
                stat = self.client.stat_object(bucket_name, object_name)
            except Exception as e:
                log_.error(f"文件上传后验证失败: {str(e)}")
                raise Exception(f"文件上传后无法验证: {str(e)}")
            
            # 生成URL
            url = f"{MINIO_ENDPOINT}/{bucket_name}/{object_name}"

            return url
        except FileNotFoundError:
            # 直接重新抛出文件不存在错误
            raise
        except S3Error as e:
            log_.error(f"MinIO上传文件失败: {str(e)}")
            raise
        except Exception as e:
            log_.error(f"上传文件过程中发生异常: {str(e)}")
            raise

    def upload_bytes(self, data, object_name, bucket_name=None, content_type=None):
        """上传字节数据到MinIO
        
        Args:
            data: 字节数据
            object_name: 对象名称
            bucket_name: 桶名称，默认使用配置中的桶
            content_type: 内容类型
            
        Returns:
            str: 对象URL
        """
        try:
            bucket_name = bucket_name or self.default_bucket
            
            # 确保桶存在
            self._ensure_bucket_exists(bucket_name)
            
            # 上传数据
            self.client.put_object(
                bucket_name=bucket_name,
                object_name=object_name,
                data=io.BytesIO(data),
                length=len(data),
                content_type=content_type
            )
            
            # 生成URL
            url = f"{MINIO_ENDPOINT}/{bucket_name}/{object_name}"

            return url
        except S3Error as e:
            log_.error(f"上传数据失败: {str(e)}")
            raise

    def download_file(self, object_name, file_path=None, bucket_name=None):
        """从MinIO下载文件
        
        Args:
            object_name: 对象名称
            file_path: 保存路径，为None时返回对象数据
            bucket_name: 桶名称，默认使用配置中的桶
            
        Returns:
            str|bytes: 文件路径或对象数据
        """
        try:
            bucket_name = bucket_name or self.default_bucket
            
            if file_path:
                # 下载到文件
                self.client.fget_object(
                    bucket_name=bucket_name,
                    object_name=object_name,
                    file_path=file_path
                )
                return file_path
            else:
                # 下载到内存
                response = self.client.get_object(
                    bucket_name=bucket_name,
                    object_name=object_name
                )
                data = response.read()
                response.close()
                return data
        except S3Error as e:
            log_.error(f"下载文件失败: {str(e)}")
            raise

    def download_from_url(self, url, file_path=None):
        """从MinIO URL下载文件
        
        Args:
            url: MinIO对象URL
            file_path: 保存路径，为None时返回对象数据
            
        Returns:
            str|bytes: 文件路径或对象数据
        """
        try:
            parsed_url = urlparse(url)
            path_parts = parsed_url.path.strip('/').split('/')
            bucket_name = path_parts[0]
            object_name = '/'.join(path_parts[1:])
            
            return self.download_file(
                object_name=object_name,
                file_path=file_path,
                bucket_name=bucket_name
            )
        except Exception as e:
            log_.error(f"从URL下载文件失败: {str(e)}")
            raise

    def list_objects(self, prefix="", bucket_name=None):
        """列出对象
        
        Args:
            prefix: 前缀过滤
            bucket_name: 桶名称，默认使用配置中的桶
            
        Returns:
            list: 对象列表
        """
        try:
            bucket_name = bucket_name or self.default_bucket
            
            objects = self.client.list_objects(
                bucket_name=bucket_name,
                prefix=prefix,
                recursive=True
            )
            
            result = []
            for obj in objects:
                result.append({
                    "object_name": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified,
                    "url": f"{MINIO_ENDPOINT}/{bucket_name}/{obj.object_name}"
                })
                
            return result
        except S3Error as e:
            log_.error(f"列出对象失败: {str(e)}")
            raise

    def delete_file(self, object_name):
        """从MinIO中删除对象
        
        Args:
            object_name (str): 对象名称或路径
            
        Returns:
            bool: 删除是否成功
        """
        try:
            self.client.remove_object(
                bucket_name=self.default_bucket,
                object_name=object_name
            )
            return True
        except Exception as e:
            log_.error(f"从MinIO删除文件失败: {str(e)}")
            return False

    def delete_from_url(self, url):
        """从URL中提取并删除MinIO对象
        
        Args:
            url (str): MinIO对象的URL
            
        Returns:
            bool: 删除是否成功
        """
        try:
            # 从URL中提取对象名称
            object_name = self._extract_object_name_from_url(url)
            if not object_name:
                log_.error(f"无法从URL提取对象名称: {url}")
                return False
            
            return self.delete_file(object_name)
        except Exception as e:
            log_.error(f"从URL删除文件失败: {str(e)}")
            return False

    def _extract_object_name_from_url(self, url):
        """从URL中提取对象名称
        
        Args:
            url (str): MinIO对象的URL
            
        Returns:
            str: 对象名称，如果提取失败则返回None
        """
        try:
            # URL格式: http(s)://endpoint/bucket/object
            parsed_url = urlparse(url)
            path = parsed_url.path
            
            # 去除开头的斜杠和bucket名称
            parts = path.split('/')
            if len(parts) >= 3:  # At least ["", "bucket", "object"]
                return '/'.join(parts[2:])
            
            return None
        except Exception as e:
            log_.error(f"解析URL失败: {str(e)}")
            return None 

    def get_presigned_url(self, object_name, bucket_name=None, expires=3600):
        """获取对象的预签名URL
        
        Args:
            object_name (str): 对象名称
            bucket_name (str, optional): 桶名称，默认使用配置中的桶
            expires (int, optional): 链接有效期（秒），默认1小时
            
        Returns:
            str: 预签名URL
        """
        try:
            from datetime import timedelta
            
            bucket_name = bucket_name or self.default_bucket

            # 检查对象是否存在
            try:
                self.client.stat_object(bucket_name, object_name)
            except Exception as e:
                log_.error(f"对象不存在: {object_name}, 错误: {str(e)}")
                # 返回一个静态URL，即使对象不存在
                return f"{MINIO_ENDPOINT}/{bucket_name}/{object_name}"
            
            # 处理expires参数
            try:
                if isinstance(expires, int):
                    # 如果是整数，转换为timedelta
                    expires_delta = timedelta(seconds=expires)
                elif isinstance(expires, timedelta):
                    # 如果已经是timedelta，直接使用
                    expires_delta = expires
                else:
                    # 其他情况，使用默认值
                    log_.warning(f"无效的expires类型: {type(expires)}，使用默认值3600秒")
                    expires_delta = timedelta(seconds=3600)
                
                # 生成预签名URL
                url = self.client.presigned_get_object(
                    bucket_name=bucket_name,
                    object_name=object_name,
                    expires=expires_delta
                )

                return url
            except Exception as expires_error:
                log_.error(f"处理expires参数或生成预签名URL失败: {str(expires_error)}", exc_info=True)
                # 出错时返回一个静态URL
                return f"{MINIO_ENDPOINT}/{bucket_name}/{object_name}"
        except Exception as e:
            log_.error(f"生成预签名URL失败: {str(e)}", exc_info=True)
            # 出错时返回一个静态URL
            return f"{MINIO_ENDPOINT}/{bucket_name}/{object_name}" 