from functools import wraps
from common.error_codes import APIException, ErrorCode
from common import log_
from flask import request, g

def api_exception_handler(func):
    """API异常统一处理装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # 调用原始函数
            return func(*args, **kwargs)
            
        except APIException as e:
            # 处理自定义API异常
            log_.error(f"API异常: {e.message}")
            return e.to_dict(), 200
            
        except Exception as e:
            # 处理其他异常
            log_.exception(f"未预期的异常: {str(e)}")
            system_error = APIException(ErrorCode.SYSTEM_ERROR, msg=str(e))
            return system_error.to_dict(), 200
    
    return wrapper

def login_required(func):
    """用户登录验证装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 直接使用g中的用户信息，不再重复验证
        user_dict = g.get('user_dict')
        user_id = g.get('user_id')
        
        if not user_dict or not user_id:
            return {
                "code": ErrorCode.UNAUTHORIZED.code,
                "message": "请先登录",
                "data": None
            }, 200
        
        # 调用原始函数
        return func(*args, **kwargs)
    
    return wrapper

def login_optional(func):
    """可选登录装饰器 - 用户登录后可获得额外功能，未登录也可访问"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 无需额外验证，直接调用原始函数
        # 用户信息已经在中间件中设置到g对象
        return func(*args, **kwargs)
    
    return wrapper
