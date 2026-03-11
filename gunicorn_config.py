# 导入服务器配置
from config.base import SERVER_WORKERS, SERVER_BIND, SERVER_TIMEOUT

# 设置Gunicorn配置变量
workers = SERVER_WORKERS
bind = SERVER_BIND
timeout = SERVER_TIMEOUT

# gunicorn -c gunicorn_config.py app:app