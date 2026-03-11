import random
import smtplib
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import jsonify, request, g
import psycopg2
from datetime import datetime
from email.utils import formataddr
import json

from .base import BaseResource
from common import log_
from common.error_codes import APIException, ErrorCode, ParameterError, ResourceNotFound, UnauthorizedError
from config.base import EMAIL_HOST, EMAIL_PORT, EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_NAME
from app.services.user_service import UserService
from app.services.auth_service import AuthService
from common.redis_utils import RedisUtil
from common.db_utils import get_db_connection

# 邮件服务类
class EmailService:
    @staticmethod
    def send_code_email(email, code):
        """
        发送验证码邮件
        """
        try:
            # 创建邮件消息
            msg = MIMEMultipart()
            # 设置发件人，使用QQ邮箱兼容的格式
            msg['From'] = formataddr((EMAIL_NAME, EMAIL_SENDER))
            msg['To'] = email
            msg['Subject'] = "【智能对话平台】验证码"
            
            # 邮件正文
            body = f"""
            <html>
            <body>
                <div style="background-color:#f7f7f7;padding:20px">
                    <div style="max-width:600px;margin:0 auto;background-color:white;padding:20px;border-radius:10px;box-shadow:0 0 10px rgba(0,0,0,0.1)">
                        <h2 style="color:#333;text-align:center">智能对话平台 - 验证码</h2>
                        <p>您好，</p>
                        <p>您的验证码是：</p>
                        <div style="text-align:center;padding:15px;background-color:#f5f5f5;margin:20px 0;border-radius:5px">
                            <h1 style="color:#007bff;letter-spacing:5px">{code}</h1>
                        </div>
                        <p>该验证码将在5分钟内有效，请勿泄露给他人。</p>
                        <p>如果这不是您的操作，请忽略此邮件。</p>
                        <p style="color:#999;font-size:12px;margin-top:30px">此邮件由系统自动发送，请勿回复。</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html', 'utf-8'))
            
            # 连接SMTP服务器并发送
            server = smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT)
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            return True
        except Exception as e:
            log_.error(f"邮件发送失败: {str(e)}")
            return False


# 验证码控制器
class AuthCodeResource(BaseResource):
    def post(self):
        """发送验证码接口"""
        try:
            params = self.get_params()
            email = params.get('email')
            
            if not email:
                return {"code": ErrorCode.PARAMETER_ERROR.code, "message": "邮箱不能为空"}
            
            # 使用AuthService发送验证码
            AuthService.send_verification_code(email)
            
            return {"code": ErrorCode.SUCCESS.code, "message": "验证码发送成功"}
        
        except APIException as e:
            return e.to_dict()
        
        except Exception as e:
            log_.exception(f"发送验证码异常: {str(e)}")
            error = APIException(ErrorCode.SYSTEM_ERROR, msg="系统错误")
            return error.to_dict()


# 登录/注册控制器
class AuthLoginRegisterResource(BaseResource):
    def post(self):
        """登录/注册接口"""
        try:
            params = self.get_params()
            email = params.get('email')
            code = params.get('code')
            
            # 测试账号特殊处理
            if email == 'test@123.com':
                user_data = AuthService.login_register_test_account(email)
                return {
                    "code": ErrorCode.SUCCESS.code, 
                    "message": "测试账号登录成功", 
                    "data": user_data
                }
            
            # 登录或注册
            user_data = AuthService.login_register(email, code)
            
            # 返回成功信息
            return {
                "code": ErrorCode.SUCCESS.code, 
                "message": "登录成功", 
                "data": user_data
            }
        
        except psycopg2.Error as e:
            log_.exception(f"数据库错误: {str(e)}")
            error = APIException(ErrorCode.DATABASE_ERROR, msg="数据库操作失败")
            return error.to_dict()
        
        except APIException as e:
            return e.to_dict()
        
        except Exception as e:
            log_.exception(f"登录/注册异常: {str(e)}")
            error = APIException(ErrorCode.SYSTEM_ERROR, msg="系统错误")
            return error.to_dict()


# 令牌验证控制器（自动登录）
class AuthVerifyTokenResource(BaseResource):
    """
    验证令牌资源
    
    用于验证用户令牌的有效性，并返回用户信息
    """
    def post(self):
        """验证令牌的有效性，并返回用户信息"""
        # 获取请求参数
        params = request.get_json(silent=True) or {}
        
        # 获取Authorization头
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            log_.warning(f"验证令牌失败：未提供token")
            return {
                "code": ErrorCode.UNAUTHORIZED.code,
                "message": "未提供有效的令牌",
                "data": None
            }
        
        # 提取token
        token = auth_header.split(' ')[1]
        
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
                    # 将用户信息转换为响应格式
                    user_data = {
                        'id': user_dict['id'],
                        'email': user_dict['email'],
                        'name': user_dict.get('name', user_dict['email'].split('@')[0]),
                        'avatar': user_dict.get('avatar', '/static/images/avatar_default.png'),
                        'phone': user_dict.get('phone')
                    }
                    
                    # 返回成功响应
                    return {
                        "code": "SUCCESS",
                        "message": "令牌验证成功",
                        "data": user_data
                    }
                else:
                    log_.warning(f"Redis中的用户数据无效")
            else:
                log_.warning(f"Redis中不存在用户信息，键: {redis_key}")
        except Exception as redis_error:
            log_.error(f"从Redis获取用户信息时出错: {str(redis_error)}", exc_info=True)
        
        # 如果Redis缓存无效或不存在，则验证token
        try:
            from app.services.auth_service import AuthService
            user_data = AuthService.verify_token(token)
            
            if user_data:
                # 格式化用户数据
                response_data = {
                    'id': user_data['id'],
                    'email': user_data['email'],
                    'name': user_data.get('name', user_data['email'].split('@')[0]),
                    'avatar': user_data.get('avatar', '/static/images/avatar_default.png'),
                    'phone': user_data.get('phone')
                }
                
                # 更新Redis缓存
                try:
                    from app import redis_client
                    
                    # 序列化用户数据
                    serialized_data = json.dumps(user_data).encode()
                    
                    # 存储到Redis，设置30天过期
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
                
                # 返回成功响应
                return {
                    "code": "SUCCESS",
                    "message": "令牌验证成功",
                    "data": response_data
                }
            else:
                log_.warning(f"令牌验证失败: {token[:20]}...")
                return {
                    "code": ErrorCode.UNAUTHORIZED.code,
                    "message": "令牌无效或已过期",
                    "data": None
                }
        except Exception as e:
            log_.error(f"验证令牌时出错: {str(e)}", exc_info=True)
            return {
                "code": ErrorCode.SYSTEM_ERROR.code,
                "message": "系统错误，请稍后重试",
                "data": None
            }
    
    def get(self):
        """GET方法处理验证令牌请求"""
        # 直接调用post方法处理，保持逻辑一致
        return self.post() 