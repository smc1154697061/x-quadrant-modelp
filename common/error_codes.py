from enum import Enum

class ErrorCode(Enum):
    """错误码枚举类"""
    SUCCESS = ("0000", "操作成功")
    
    # 通用错误 (1xxx)
    UNKNOWN_ERROR = ("1000", "未知错误")
    PARAMETER_ERROR = ("1001", "参数错误") 
    VALIDATION_ERROR = ("1002", "数据验证错误")
    NOT_FOUND = ("1003", "资源不存在")
    PERMISSION_DENIED = ("1004", "权限不足")
    UNAUTHORIZED = ("1005", "未授权访问")
    
    # 文件相关错误 (2xxx)
    FILE_NOT_FOUND = ("2000", "文件不存在")
    FILE_UPLOAD_ERROR = ("2001", "文件上传失败")
    FILE_TYPE_ERROR = ("2002", "不支持的文件类型")
    FILE_SIZE_ERROR = ("2003", "文件大小超过限制")
    FILE_READ_ERROR = ("2004", "文件读取失败")
    FILE_PROCESS_ERROR = ("2005", "文件处理失败")
    
    # OCR相关错误 (3xxx)
    OCR_INIT_ERROR = ("3000", "OCR初始化失败")
    OCR_PROCESS_ERROR = ("3001", "OCR处理失败")
    TESSERACT_ERROR = ("3002", "Tesseract错误")
    IMAGE_PROCESS_ERROR = ("3003", "图像处理错误")
    
    # 模型相关错误 (4xxx)
    MODEL_INIT_ERROR = ("4000", "模型初始化失败")
    MODEL_INVOKE_ERROR = ("4001", "模型调用失败")
    MODEL_RESPONSE_ERROR = ("4002", "模型响应异常")
    
    # 知识库相关错误 (5xxx)
    KB_NOT_FOUND = ("5000", "知识库不存在")
    KB_CREATE_ERROR = ("5001", "创建知识库失败")
    KB_UPDATE_ERROR = ("5002", "更新知识库失败")
    KB_DELETE_ERROR = ("5003", "删除知识库失败")
    KB_QUERY_ERROR = ("5004", "知识库查询失败")
    
    # 内容提取相关错误 (6xxx)
    EXTRACT_ERROR = ("6000", "内容提取失败")
    SCHEMA_ERROR = ("6001", "Schema格式错误")
    JSON_PARSE_ERROR = ("6002", "JSON解析错误")
    
    # 系统相关错误 (9xxx)
    SYSTEM_ERROR = ("9000", "系统错误")
    DATABASE_ERROR = ("9001", "数据库错误")
    NETWORK_ERROR = ("9002", "网络错误")
    TIMEOUT_ERROR = ("9003", "请求超时")

    def __init__(self, code, message):
        self.code = code
        self.message = message


class APIException(Exception):
    """API异常基类"""
    def __init__(self, error_code=ErrorCode.UNKNOWN_ERROR, data=None, msg=None):
        if isinstance(error_code, ErrorCode):
            self.code = error_code.code
            self.message = msg or error_code.message
        else:
            self.code = ErrorCode.UNKNOWN_ERROR.code
            self.message = msg or ErrorCode.UNKNOWN_ERROR.message
        
        self.data = data
        super().__init__(self.message)

    def to_dict(self):
        """转换为字典格式，用于API响应"""
        return {
            "code": self.code,
            "message": self.message,
            "data": self.data
        }


# 定义具体异常类
class ParameterError(APIException):
    """参数错误"""
    def __init__(self, data=None, msg=None):
        super().__init__(ErrorCode.PARAMETER_ERROR, data, msg)


class ResourceNotFound(APIException):
    """资源不存在"""
    def __init__(self, data=None, msg=None):
        super().__init__(ErrorCode.NOT_FOUND, data, msg)


class UnauthorizedError(APIException):
    """未授权访问错误"""
    def __init__(self, data=None, msg=None):
        super().__init__(ErrorCode.UNAUTHORIZED, data, msg)


class FileError(APIException):
    """文件相关错误"""
    def __init__(self, error_code=ErrorCode.FILE_PROCESS_ERROR, data=None, msg=None):
        super().__init__(error_code, data, msg)


class OCRError(APIException):
    """OCR相关错误"""
    def __init__(self, error_code=ErrorCode.OCR_PROCESS_ERROR, data=None, msg=None):
        super().__init__(error_code, data, msg)


class ModelError(APIException):
    """模型相关错误"""
    def __init__(self, error_code=ErrorCode.MODEL_INVOKE_ERROR, data=None, msg=None):
        super().__init__(error_code, data, msg)


class ModelCallError(ModelError):
    """模型调用错误"""
    def __init__(self, msg=None, data=None):
        super().__init__(ErrorCode.MODEL_INVOKE_ERROR, data, msg)


class KnowledgeBaseError(APIException):
    """知识库相关错误"""
    def __init__(self, error_code=ErrorCode.KB_QUERY_ERROR, data=None, msg=None):
        super().__init__(error_code, data, msg)


class ExtractionError(APIException):
    """内容提取相关错误"""
    def __init__(self, error_code=ErrorCode.EXTRACT_ERROR, data=None, msg=None):
        super().__init__(error_code, data, msg)


class SystemError(APIException):
    """系统相关错误"""
    def __init__(self, error_code=ErrorCode.SYSTEM_ERROR, data=None, msg=None):
        super().__init__(error_code, data, msg)


class JSONParseError(APIException):
    """JSON解析错误"""
    def __init__(self, data=None, msg=None):
        super().__init__(ErrorCode.JSON_PARSE_ERROR, data, msg)
