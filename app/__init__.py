'''
初始化 Flask 应用，加载配置，注册 Blueprint。
'''
from flask import Flask, jsonify, request, g
from flask_cors import CORS
import redis
import json
from datetime import datetime, date
from flask_restful import Api
from flask_caching import Cache

# 导入统一配置
from config.base import DEBUG, SECRET_KEY, REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD
from config.base import REDIS_KEY_PREFIX_VERIFICATION_CODE, REDIS_KEY_PREFIX_RATE_LIMIT
from common.error_codes import APIException, ErrorCode
from common import log_
from common.db_utils import get_db_pool
from app.core.middlewares import init_auth_middleware
from app.models.embeddings.modelfactory import EmbeddingModelFactory
from app.models.llm.model_factory import get_llm_model
from app.models.vector_store.povector_store import PVectorStore
from app.services.chat_service import ChatService

# 全局变量
redis_client = None
embedding_model = None
llm_model = None
vector_store = None
chat_service = None
db_pool = None

cache = Cache(config={'CACHE_TYPE': 'simple'})

# 自定义JSONEncoder处理datetime类型
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        return super().default(obj)

def create_app():
    app = Flask(__name__)
    # 直接设置配置，不使用CONFIG变量
    app.config['DEBUG'] = DEBUG
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['TESTING'] = False
    app.config['JSON_AS_ASCII'] = False
    
    # 设置自定义JSON编码器
    app.json_encoder = CustomJSONEncoder
    
    # 添加请求日志中间件
    @app.before_request
    def log_request_info():
        # 只在调试模式下记录请求路径，不记录详细参数
        if app.debug:
            log_.debug(f"请求: {request.method} {request.path}")
            return
    
    # 允许跨域请求
    CORS(app, resources={
        r"/*": {
            "origins": ["http://localhost:8080", "http://192.168.100.154:8080", "*"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"]
        }
    }, supports_credentials=True)
    
    # 添加OPTIONS请求处理，防止每次OPTIONS请求报错
    @app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
    @app.route('/<path:path>', methods=['OPTIONS'])
    def options_handler(path):
        return '', 200

    # 初始化Redis客户端
    global redis_client
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
        decode_responses=False  # 不要自动解码，由RedisUtil负责解码
    )

    # 初始化数据库连接池（使用原生 SQL，不使用 ORM 自动建表）
    global db_pool
    db_pool = get_db_pool()
    
    # 预加载模型和服务
    try:
        # 预加载embedding模型
        global embedding_model
        try:
            embedding_model = EmbeddingModelFactory.get_embeddings()
            app.embedding_model = embedding_model  # 存储在应用上下文中
        except Exception as e:
            log_.error(f"Embedding模型加载失败，但应用将继续运行: {str(e)}")
            embedding_model = None
        
        # 预加载LLM模型
        global llm_model
        try:
            llm_model = get_llm_model()
            app.llm_model = llm_model  # 存储在应用上下文中
        except Exception as e:
            log_.error(f"LLM模型加载失败，但应用将继续运行: {str(e)}")
            llm_model = None
        
        # 预加载向量存储
        global vector_store
        try:
            vector_store = PVectorStore()
            app.vector_store = vector_store  # 存储在应用上下文中
        except Exception as e:
            log_.error(f"向量存储加载失败，但应用将继续运行: {str(e)}")
            vector_store = None
        
        # 预加载聊天服务
        global chat_service
        try:
            chat_service = ChatService()
            app.chat_service = chat_service  # 存储在应用上下文中
        except Exception as e:
            log_.error(f"聊天服务加载失败，但应用将继续运行: {str(e)}")
            chat_service = None
        
    except Exception as e:
        log_.error(f"预加载模型和服务失败，但应用将继续运行: {str(e)}")

    # 在请求上下文中添加全局变量访问器
    @app.before_request
    def set_global_resources():
        g.embedding_model = embedding_model
        g.llm_model = llm_model
        g.vector_store = vector_store
        g.chat_service = chat_service
        g.db_pool = db_pool

    # 注册API蓝图
    from apis.extraction_api import extraction_api_bp
    app.register_blueprint(extraction_api_bp)
    
    # 注册前端API蓝图
    from app.routes.web_routes import frontend_bp
    app.register_blueprint(frontend_bp)
    
    # 注册认证API路由
    from app.controllers.auth_controller import AuthCodeResource, AuthLoginRegisterResource, AuthVerifyTokenResource
    from app.controllers.user_controller import UserResource
    
    # 配置Flask-RESTful，使用自定义JSONEncoder
    def output_json_with_dates(data, code, headers=None):
        resp = app.response_class(
            response=json.dumps(data, cls=CustomJSONEncoder),
            status=code,
            headers=headers,
            mimetype='application/json'
        )
        return resp
    
    # 创建Api实例并配置JSON编码器
    auth_api = Api(app)
    auth_api.representations = {'application/json': output_json_with_dates}
    auth_api.add_resource(AuthCodeResource, '/api/auth/send-code')
    auth_api.add_resource(AuthLoginRegisterResource, '/api/auth/login-register')
    auth_api.add_resource(AuthVerifyTokenResource, '/api/auth/verify-token')
    
    # 注册用户API路由
    user_api = Api(app, prefix='/api')
    user_api.representations = {'application/json': output_json_with_dates}
    user_api.add_resource(UserResource, '/users/<int:user_id>', '/users')
    
    # 初始化认证中间件
    init_auth_middleware(app)

    # 全局异常处理
    @app.errorhandler(Exception)
    def handle_exception(e):
        if isinstance(e, APIException):
            return jsonify(e.to_dict()), 200
        
        # 记录未处理的异常
        log_.exception(f"未处理的异常: {str(e)}")
        
        # 返回通用错误
        error = APIException(ErrorCode.SYSTEM_ERROR, msg=str(e))
        return jsonify(error.to_dict()), 200

    cache.init_app(app)

    return app