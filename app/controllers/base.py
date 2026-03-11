import flask_restful
from flask import request, g, make_response
import json
from datetime import datetime
import traceback
from common import log_
from common.error_codes import APIException, ErrorCode, ParameterError

# 自定义JSON编码器，处理datetime等特殊类型
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        # 如果是具有to_dict方法的对象，调用该方法并返回其结果
        elif hasattr(obj, 'to_dict') and callable(getattr(obj, 'to_dict')):
            return obj.to_dict()
        # 对于SQLAlchemy对象，尝试将其转换为字典
        elif hasattr(obj, '__dict__'):
            # 处理SQLAlchemy对象
            result = {}
            for key, value in obj.__dict__.items():
                if not key.startswith('_'):  # 排除私有属性
                    if isinstance(value, datetime):
                        result[key] = value.isoformat()
                    else:
                        result[key] = value
            return result
        # 对于其他不可序列化对象，返回其字符串表示
        try:
            return super().default(obj)
        except TypeError:
            return str(obj)

# 封装用于Redis存储的JSON序列化
def json_serialize(obj):
    """序列化对象为JSON字符串，处理特殊类型如datetime"""
    return json.dumps(obj, cls=CustomJSONEncoder)

class BaseResource(flask_restful.Resource):
    """REST API基础资源类"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    # 添加对OPTIONS请求的支持
    def options(self, *args, **kwargs):
        """处理OPTIONS请求，用于CORS预检请求"""
        response = make_response()
        response.status_code = 200
        return response
    
    def get_params(self):
        """获取请求参数，支持form表单和JSON格式"""
        try:
            params = request.form
            if not params:
                if request.data:
                    params = json.loads(request.data.decode())
                else:
                    params = {}
            return params
        except Exception as e:
            log_.error(f"解析请求参数失败: {str(e)}")
            raise ParameterError(msg="请求体格式有误")
    
    def get_current_user(self):
        """
        获取当前登录用户信息
        
        先尝试从g.user_dict获取，如果不存在则尝试从g.user_id获取
        如果g.user_id存在但g.user_dict不存在，则从数据库中查询并缓存到g.user_dict
        
        Returns:
            dict: 用户信息字典，未登录时返回None
        """
        # 先尝试从g.user_dict获取
        user_dict = getattr(g, 'user_dict', None)
        if user_dict:
            return user_dict
        
        # 再尝试从g.user_id获取
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return None
        
        # 从数据库中查询用户信息
        try:
            from app.dao.user_dao import UserDao
            user = UserDao.get_user_by_id(user_id)
            
            if not user:
                log_.warning(f"使用user_id {user_id}未找到用户信息")
                return None
            
            # 转换为字典并缓存到g.user_dict
            user_dict = user.to_dict()
            g.user_dict = user_dict
            
            return user_dict
        except Exception as e:
            log_.error(f"获取用户信息时出错: {str(e)}", exc_info=True)
            return None

    def get_user_from_token(self):
        """
        从请求头的Authorization中提取token并获取用户信息
        
        Returns:
            dict: 用户信息字典，未登录或token无效时返回None
        """
        # 获取Authorization头
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            log_.warning(f"请求头中没有有效的Authorization: {auth_header}")
            return None
        
        # 提取token
        token = auth_header.split(' ')[1]
        
        # 先尝试从Redis缓存中获取用户信息
        try:
            from app import redis_client
            redis_key = f"user_token:{token}"
            user_data = redis_client.get(redis_key)
            
            if user_data:
                # 解析用户数据
                import json
                user_dict = json.loads(user_data.decode())
                
                # 验证用户数据是否有效
                if not user_dict or 'id' not in user_dict:
                    log_.warning("Redis中的用户数据缺少id字段，将重新验证token")
                else:
                    # 缓存到g对象
                    g.user_dict = user_dict
                    g.user_id = user_dict['id']
                    
                    return user_dict
            else:
                log_.warning(f"Redis中未找到键 {redis_key} 对应的用户信息")
        except Exception as redis_error:
            log_.error(f"从Redis获取用户信息时出错: {str(redis_error)}", exc_info=True)
        
        # 如果Redis缓存无效或不存在，则验证token
        try:
            from app.services.auth_service import AuthService
            
            # 验证token
            user_dict = AuthService.verify_token(token)
            
            if user_dict:
                # 缓存到g对象
                g.user_dict = user_dict
                g.user_id = user_dict['id']
                
                # 更新Redis缓存
                try:
                    from app import redis_client
                    
                    # 序列化用户数据
                    serialized_data = json.dumps(user_dict).encode()
                    
                    # 存储到Redis，设置30天过期
                    redis_key = f"user_token:{token}"
                    redis_client.setex(
                        redis_key,
                        60 * 60 * 24 * 30,  # 30天过期
                        serialized_data
                    )
                    
                    # 验证缓存是否成功
                    verification = redis_client.get(redis_key)
                    if not verification:
                        log_.warning("Redis缓存验证失败，未能读取刚刚写入的数据")
                except Exception as redis_error:
                    log_.error(f"更新Redis缓存失败: {str(redis_error)}", exc_info=True)
                
                return user_dict
            else:
                log_.warning(f"AuthService验证token失败: {token[:10]}...")
        except Exception as e:
            log_.error(f"验证token时出错: {str(e)}", exc_info=True)
        
        # 如果所有方法都失败，返回None
        log_.warning("未能获取当前用户，返回None")
        return None
    
    def dispatch_request(self, *args, **kwargs):
        """重写dispatch_request方法，添加统一异常处理"""
        try:
            return super().dispatch_request(*args, **kwargs)
        except Exception as e:
            # 记录异常
            log_.exception(f"API调用异常: {str(e)}")
            
            # 使用统一的错误处理
            if isinstance(e, APIException):
                return e.to_dict(), 200
            
            # 未知异常，封装为APIException
            system_error = APIException(ErrorCode.SYSTEM_ERROR, msg=str(e))
            return system_error.to_dict(), 200


