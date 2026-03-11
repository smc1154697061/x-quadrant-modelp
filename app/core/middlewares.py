from functools import wraps
from flask import request, g, jsonify
from common import log_
from common.error_codes import APIException, ErrorCode

# 定义需要登录的API路径前缀列表
AUTH_REQUIRED_PATHS = [
    '/api/llm/knowledge-bases',  # 知识库相关API
    '/api/llm/conversations',    # 对话相关API
    '/api/llm/bots'              # 机器人相关API
]

# 定义可选登录的API路径前缀列表（未登录也可访问，但登录后功能更丰富）
AUTH_OPTIONAL_PATHS = [
    '/api/llm/documents'         # 文档相关API
]

def auth_required(f):
    """需要登录的接口装饰器
    
    用于装饰需要用户登录才能访问的API接口
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # 检查当前用户是否已登录
        user_dict = g.get('user_dict')
        user_id = g.get('user_id')
        
        if not user_dict or not user_id:
            log_.warning("用户未登录，拒绝访问需要认证的API")
            return {
                "code": ErrorCode.UNAUTHORIZED.code,
                "message": "请先登录再继续操作",
                "data": None
            }, 401
        
        # 调用原始函数
        return f(*args, **kwargs)
    
    return decorated

def auth_optional(f):
    """可选登录的接口装饰器
    
    用于装饰可选登录的API接口，未登录也可访问，但登录后功能更丰富
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # 无需检查登录状态，直接调用原始函数
        return f(*args, **kwargs)
    
    return decorated

def init_auth_middleware(app):
    """初始化认证中间件
    
    在每个请求前检查用户登录状态，并将用户信息存储到g对象中
    """
    @app.before_request
    def check_auth():
        # 跳过OPTIONS请求
        if request.method == 'OPTIONS':
            return None
            
        # 跳过不需要认证的路径
        exempt_paths = [
            '/api/auth/send-code',
            '/api/auth/login-register',
            '/api/auth/verify-token'
        ]
        if request.path in exempt_paths:
            return None
            
        # 获取Authorization头
        auth_header = request.headers.get('Authorization')
        
        # 初始化用户信息为空
        g.user_dict = None
        g.user_id = None
        
        if not auth_header or not auth_header.startswith('Bearer '):
            # 未提供有效的Authorization头
            
            # 检查是否是需要登录的API
            for path_prefix in AUTH_REQUIRED_PATHS:
                if request.path.startswith(path_prefix):
                    log_.warning(f"未授权访问需要登录的API: {request.path}")
                    return {
                        "code": ErrorCode.UNAUTHORIZED.code,
                        "message": "请先登录再继续操作",
                        "data": None
                    }, 401
            
            # 不是需要登录的API，继续处理请求
            return None
            
        # 提取token
        token = auth_header.split(' ')[1]
        
        # 尝试验证token并获取用户信息
        try:
            from app.services.auth_service import AuthService
            
            # 先尝试从Redis缓存中获取用户信息
            try:
                from app import redis_client
                redis_key = f"user_token:{token}"
                redis_data = redis_client.get(redis_key)
                
                if redis_data:
                    import json
                    user_dict = json.loads(redis_data.decode())
                    
                    # 验证缓存的用户信息是否有效
                    if user_dict and 'id' in user_dict and 'email' in user_dict:
                        # 将用户信息存储到g对象中
                        g.user_dict = user_dict
                        g.user_id = user_dict['id']
                        return None  # 验证成功，继续处理请求
                    else:
                        log_.warning("Redis缓存的用户信息无效")
            except Exception as redis_error:
                log_.error(f"从Redis获取用户信息时出错: {str(redis_error)}", exc_info=True)
            
            # 如果Redis缓存无效或不存在，则验证token
            user_dict = AuthService.verify_token(token)
            
            if user_dict:
                # 将用户信息存储到g对象中
                g.user_dict = user_dict
                g.user_id = user_dict['id']
                
                # 更新Redis缓存
                try:
                    from app import redis_client
                    from app.controllers.base import json_serialize
                    
                    redis_key = f"user_token:{token}"
                    serialized_data = json_serialize(user_dict)
                    
                    redis_client.setex(
                        redis_key,
                        60 * 60 * 24 * 30,  # 30天过期
                        serialized_data
                    )
                except Exception as redis_error:
                    log_.error(f"更新Redis缓存失败: {str(redis_error)}", exc_info=True)
            else:
                log_.warning("无效的token，未能获取用户信息")
                
                # 检查是否是需要登录的API
                for path_prefix in AUTH_REQUIRED_PATHS:
                    if request.path.startswith(path_prefix):
                        log_.warning(f"无效token访问需要登录的API: {request.path}")
                        return {
                            "code": ErrorCode.UNAUTHORIZED.code,
                            "message": "登录已过期，请重新登录",
                            "data": None
                        }, 401
        except Exception as e:
            log_.error(f"验证token时出错: {str(e)}", exc_info=True)
            
            # 检查是否是需要登录的API
            for path_prefix in AUTH_REQUIRED_PATHS:
                if request.path.startswith(path_prefix):
                    log_.warning(f"验证失败访问需要登录的API: {request.path}")
                    return {
                        "code": ErrorCode.UNAUTHORIZED.code,
                        "message": "登录验证失败，请重新登录",
                        "data": None
                    }, 401
        
        # 无论验证结果如何，继续处理请求
        return None 