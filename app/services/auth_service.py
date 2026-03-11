"""
认证服务类 - 处理验证码发送、登录注册等认证逻辑
"""
import random
import smtplib
import string
import jwt
import time
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

from common import log_
from common.error_codes import APIException, ErrorCode, ParameterError
from config.base import EMAIL_HOST, EMAIL_PORT, EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_NAME, SECRET_KEY
from app.services.user_service import UserService
from common.redis_utils import RedisUtil

class AuthService:
    """认证服务类，处理认证相关的业务逻辑"""
    
    @classmethod
    def send_verification_code(cls, email):
        """发送验证码"""
        # 验证邮箱格式
        if not UserService._validate_email(email):
            raise ParameterError(msg="邮箱格式不正确")
        
        # 生成6位数字验证码
        code = ''.join(random.choices(string.digits, k=6))
        
        # 保存验证码到Redis
        if not RedisUtil.set_code(email, code, 300):
            raise APIException(ErrorCode.SYSTEM_ERROR, msg="验证码保存失败")
        
        # 发送验证码邮件
        if not cls._send_code_email(email, code):
            RedisUtil.delete_code(email)
            raise APIException(ErrorCode.SYSTEM_ERROR, msg="验证码发送失败")
        
        return True
    

    @classmethod
    def login_register_test_account(cls, email):
        """测试账号登录，无需验证码"""
        # 验证参数
        if not email or email != 'test@123.com':
            raise ParameterError(msg="仅支持test@123.com测试账号")
        
        try:
            # 查询用户是否存在
            user_data = UserService.get_user_by_email(email)
            
            # 如果用户不存在，则创建新用户
            if not user_data:
                user_data = UserService.create_user(email)
            
            # 生成JWT令牌
            token = cls.generate_token(user_data["id"], user_data["email"])

            # 将用户信息缓存到Redis，有效期30天
            try:
                from app import redis_client
                from app.controllers.base import json_serialize, CustomJSONEncoder
                
                # 移除所有非基本类型的字段，创建一个只包含简单值的新字典
                redis_data = {
                    'id': user_data['id'],
                    'email': user_data['email'],
                    'name': user_data.get('name', '测试账号'),
                    'created_at': user_data.get('created_at'),
                    'phone': user_data.get('phone', '')
                }
                
                # 确保所有值都能被序列化
                for key, value in redis_data.items():
                    if isinstance(value, datetime):
                        redis_data[key] = value.isoformat()
                
                redis_key = f"user_token:{token}"
                
                # 使用json_serialize确保正确序列化
                serialized_data = json_serialize(redis_data)
                
                # 设置Redis缓存
                redis_client.setex(
                    redis_key,
                    60 * 60 * 24 * 30,  # 30天过期
                    serialized_data
                )
            except Exception as redis_error:
                log_.error(f"缓存测试账号信息到Redis失败: {str(redis_error)}", exc_info=True)
            
            # 返回用户信息和令牌
            return {
                "id": user_data["id"],
                "email": user_data["email"],
                "name": user_data.get("name", "测试账号"),
                "avatar": "/static/images/avatar_default.png",  # 使用默认头像
                "token": token  # 添加令牌
            }
        except Exception as e:
            log_.error(f"测试账号登录过程中发生错误: {str(e)}", exc_info=True)
            raise APIException(ErrorCode.DATABASE_ERROR, msg="数据库连接异常，请稍后重试")
    
    
    @classmethod
    def login_register(cls, email, code):
        """登录或注册"""
        # 验证参数
        if not email or not code:
            raise ParameterError(msg="邮箱和验证码不能为空")
        
        # 验证验证码
        stored_code = RedisUtil.get_code(email)
        if not stored_code:
            raise APIException(ErrorCode.VALIDATION_ERROR, msg="验证码已过期，请重新获取")
        
        if stored_code != code:
            raise APIException(ErrorCode.VALIDATION_ERROR, msg="验证码错误")
        
        # 验证通过，删除验证码
        RedisUtil.delete_code(email)
        
        try:
            # 查询用户是否存在
            user_data = UserService.get_user_by_email(email)
            
            # 如果用户不存在，则创建新用户
            if not user_data:
                user_data = UserService.create_user(email)
            
            # 生成JWT令牌
            token = cls.generate_token(user_data["id"], user_data["email"])

            # 将用户信息缓存到Redis，有效期30天
            try:
                from app import redis_client
                from app.controllers.base import json_serialize, CustomJSONEncoder
                
                # 确保user_data中的所有字段都可以被序列化

                # 直接使用CustomJSONEncoder尝试序列化
                try:
                    # 尝试使用json.dumps而不是我们的包装器，便于调试
                    test_json = json.dumps(user_data, cls=CustomJSONEncoder)
                except Exception as json_error:
                    log_.error(f"测试JSON序列化失败: {str(json_error)}", exc_info=True)
                
                # 移除所有非基本类型的字段，创建一个只包含简单值的新字典
                redis_data = {
                    'id': user_data['id'],
                    'email': user_data['email'],
                    'name': user_data.get('name', ''),
                    'created_at': user_data.get('created_at'),
                    'phone': user_data.get('phone', '')
                }
                
                # 确保所有值都能被序列化
                for key, value in redis_data.items():
                    if isinstance(value, datetime):
                        redis_data[key] = value.isoformat()
                
                redis_key = f"user_token:{token}"
                
                # 使用json_serialize确保正确序列化
                serialized_data = json_serialize(redis_data)

                # 设置Redis缓存
                redis_client.setex(
                    redis_key,
                    60 * 60 * 24 * 30,  # 30天过期
                    serialized_data
                )

                # 验证缓存是否成功
                verification = redis_client.get(redis_key)
                if verification:
                    log_.debug(f"Redis缓存验证成功，数据长度: {len(verification)}")
                else:
                    log_.warning("Redis缓存验证失败，未能读取刚刚写入的数据")
            except Exception as redis_error:
                log_.error(f"缓存用户信息到Redis失败: {str(redis_error)}", exc_info=True)
            
            # 返回用户信息和令牌
            return {
                "id": user_data["id"],
                "email": user_data["email"],
                "name": user_data.get("name", ""),
                "avatar": "/static/images/avatar_default.png",  # 使用默认头像
                "token": token  # 添加令牌
            }
        except Exception as e:
            log_.error(f"登录/注册过程中发生错误: {str(e)}", exc_info=True)
            raise APIException(ErrorCode.DATABASE_ERROR, msg="数据库连接异常，请稍后重试")
    
    @classmethod
    def generate_token(cls, user_id, email):
        """生成JWT令牌"""
        try:
            # 设置令牌有效期为30天
            payload = {
                'user_id': user_id,
                'email': email,
                'exp': datetime.utcnow() + timedelta(days=30),
                'iat': datetime.utcnow()
            }
            
            # 使用SECRET_KEY签名
            token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
            
            return token
        except Exception as e:
            log_.error(f"生成令牌失败: {str(e)}")
            raise APIException(ErrorCode.SYSTEM_ERROR, msg="令牌生成失败")
    
    @staticmethod
    def verify_token(token):
        """
        验证令牌并获取用户信息
        
        Args:
            token (str): JWT令牌
            
        Returns:
            dict: 用户信息字典，验证失败时返回None
        """
        try:
            # 解码JWT令牌
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            
            # 从payload中获取用户ID和邮箱
            user_id = payload.get('user_id')
            email = payload.get('email')
            
            if not user_id:
                log_.warning(f"Token中缺少user_id: {payload}")
                return None
            
            # 从数据库中获取用户信息
            from app.dao.user_dao import UserDao
            user = UserDao.get_user_by_id(user_id)
            
            if not user:
                log_.warning(f"Token中的用户不存在: {user_id}")
                return None
            
            # 验证邮箱是否匹配
            if user.email != email:
                log_.warning(f"用户不存在或邮箱不匹配: {user_id}, {email}")
                return None
            
            # 返回用户信息
            return user.to_dict()
        except jwt.ExpiredSignatureError:
            log_.warning(f"Token已过期: {token[:10]}...")
            return None
        except Exception as e:
            log_.warning(f"Token解析失败: {token[:20]}..., 错误: {str(e)}")
            return None
    
    @staticmethod
    def _send_code_email(email, code):
        """发送验证码邮件"""
        try:
            # 创建邮件消息
            msg = MIMEMultipart()
            # 设置发件人，使用QQ邮箱兼容的格式
            from email.utils import formataddr
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