import os
# 设置环境变量以解决 OpenMP 运行时冲突
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from flask import Flask
from flask_cors import CORS
from app import create_app
from config.base import LOG_LEVEL, LOG_CONSOLE_OUTPUT, LOG_FILE_OUTPUT

# 将日志开关透传为环境变量，供 common.log_ 在导入时读取
os.environ['LOG_CONSOLE_OUTPUT'] = '1' if LOG_CONSOLE_OUTPUT else '0'
os.environ['LOG_FILE_OUTPUT'] = '1' if LOG_FILE_OUTPUT else '0'
os.environ['LOG_LEVEL'] = str(LOG_LEVEL)

from common import log_
import logging

# 设置日志级别
log_.set_log_level(LOG_LEVEL)

# 记录启动信息
log_.log_startup()

app = create_app()

# 关闭 werkzeug 访问日志
logging.getLogger('werkzeug').disabled = True
logging.getLogger('werkzeug').propagate = False

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, use_reloader=False)  # 监听所有网络接口