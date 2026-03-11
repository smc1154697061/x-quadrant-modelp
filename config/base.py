"""
统一配置文件 - 包含所有应用配置
"""

# Flask应用配置
DEBUG = True
SECRET_KEY = "x-quadrant-secure-key-2025-05-22-abcdef123456"  # 用于Flask应用和JWT认证的通用密钥

# 数据库配置
DB_USER = 'root'
DB_PASSWORD = '12345678'
DB_HOST = '115.190.130.68'
DB_PORT = '5432'
DB_NAME = 'test2'

# 数据库连接池配置（类似 Java HikariCP / Druid 配置）
DB_POOL_MIN_CONN = 5              # 最小连接数（类似 minimumIdle）
DB_POOL_MAX_CONN = 20             # 最大连接数（类似 maximumPoolSize）
DB_CONNECT_TIMEOUT = 10           # 连接超时秒数（类似 connectionTimeout）
DB_KEEPALIVE_IDLE = 30            # 空闲多久后开始探测（秒）
DB_KEEPALIVE_INTERVAL = 10        # 探测间隔（秒）
DB_KEEPALIVE_COUNT = 5            # 探测失败次数
DB_APPLICATION_NAME = 'x-quadrant-modelp'  # 应用名称（方便监控）

# Redis配置
REDIS_HOST = '115.190.130.68'
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = "MagicImage_2015"

# Redis键前缀
REDIS_KEY_PREFIX_VERIFICATION_CODE = 'auth:verify:'  # 验证码键前缀
REDIS_KEY_PREFIX_RATE_LIMIT = 'auth:rate:'          # 频率限制键前缀

# Email配置
EMAIL_HOST = "smtp.163.com"  # 163邮箱SMTP服务器
EMAIL_PORT = 465             # SMTP SSL端口
EMAIL_SENDER = "smc_97@163.com"  # 发件人邮箱
EMAIL_PASSWORD = "RDjFNJBsqcvndRQh"  # 邮箱授权码（非登录密码）
EMAIL_USE_SSL = True
EMAIL_NAME = "渡渡鸟科技"    # 发件人显示名称

# 文档处理配置
TESSERACT_PATH = r"C:\Users\Bryant\AppData\Local\Tesseract-OCR\tesseract.exe"
OCR_LANGUAGES = ["chi_sim", "eng"]  # 确保chi_sim在前面
MAX_PDF_PAGES = 30  # 最大处理PDF页数，防止过大文件
IMAGE_PREPROCESS = True  # 是否进行图像预处理
INVERT_COLORS = False  # 禁用颜色反转，因为您的图像是黑字白底
SUPPORTED_TYPES = {
    "text": [".txt", ".text", ".log", ".csv"],
    "word": [".docx", ".doc"],
    "markdown": [".md", ".markdown"],
    "pdf": [".pdf"],
    "image": [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".gif"]
}

# MinIO配置
MINIO_ENDPOINT = "http://115.190.130.68:9000"
MINIO_UPLOAD_ENDPOINT = "http://115.190.130.68:9000/upload"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
MINIO_DEFAULT_BUCKET = "documents"
MINIO_SECURE = False

# PostgreSQL pgvector配置
PGVECTOR_DEFAULT_TABLE = "knowledge_embeddings"
PGVECTOR_INDEX_TYPE = "ivfflat"  # 索引类型: ivfflat, hnsw
PGVECTOR_DIMENSION = 768  # 修改为768维，匹配chinese-base模型的输出维度

# 模型配置
# LLM 提供者：'ollama'（默认）、'openai_compatible'（兼容 DeepSeek 等）
LLM_PROVIDER = "openai_compatible"  # 可选: "ollama" 或 "openai_compatible"

# Ollama 配置（当 LLM_PROVIDER = "ollama" 时使用）
#OLLAMA_BASE_URL = "http://ai-chat.vip.cpolar.cn"  # Ollama外网映射地址
OLLAMA_BASE_URL = "http://localhost:11434/"  # Ollama地址
OLLAMA_MODEL = "qwen2:7b"  # 默认模型
OLLAMA_TEMPERATURE = 0.7

# OpenAI-Compatible 提供者配置（当 LLM_PROVIDER = "openai_compatible" 时使用）
# 适配 DeepSeek / Moonshot / OpenAI 等兼容接口
# DeepSeek 配置示例：
OPENAI_BASE_URL = "https://api.deepseek.com"  # DeepSeek API 地址（不要包含 /v1）
OPENAI_API_KEY = "sk-e395a4b4e7fe4c7282849e1ba735a65a"  # DeepSeek API Key
OPENAI_MODEL = "deepseek-chat"  # DeepSeek 模型名称
OPENAI_TIMEOUT = 30

# 嵌入模型配置
EMBEDDINGS_MODEL_ID = "iic/nlp_corom_sentence-embedding_chinese-base"

# 信息提取服务配置
# 0: 使用本地Ollama模型, 1: 使用Coze工作流
EXTRACTION_MODE = 0

# Coze配置
COZE_API_TOKEN = "pat_lDRZGkLAJPZhFzykojNac6KHSGR943diur5jzdnHspdexz2nFQDMhWGvGxkWyTEo"
COZE_WORKFLOW_ID = "7529481489819090971"
COZE_BOT_ID = ""  # 豆包智能体ID（可选）

# 服务器部署配置
SERVER_WORKERS = 4
SERVER_BIND = "0.0.0.0:8000"
SERVER_TIMEOUT = 30

# 日志配置
LOG_LEVEL = "DEBUG"  # 可选: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_CONSOLE_OUTPUT = True
LOG_FILE_OUTPUT = True