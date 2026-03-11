"""
日志管理模块 - 参考 Log4j 设计
支持：
  - 层级Logger（按模块名）
  - 多Appender（控制台、滚动文件）
  - 灵活配置（级别、格式、过滤器）
  - 日志文件滚动（按大小和日期）
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

# ==================== 配置区域（类似 log4j.properties）====================

def _get_config():
    """延迟加载配置，避免循环导入"""
    try:
        from config import base as config
        return {
            'level': getattr(config, 'LOG_LEVEL', 'INFO'),
            'console': getattr(config, 'LOG_CONSOLE_OUTPUT', True),
            'file': getattr(config, 'LOG_FILE_OUTPUT', True),
            'log_dir': getattr(config, 'LOG_DIR', 'logs'),
            'max_bytes': getattr(config, 'LOG_MAX_BYTES', 10 * 1024 * 1024),  # 10MB
            'backup_count': getattr(config, 'LOG_BACKUP_COUNT', 5),
        }
    except ImportError:
        return {
            'level': os.getenv('LOG_LEVEL', 'INFO'),
            'console': os.getenv('LOG_CONSOLE_OUTPUT', 'true').lower() in ('1', 'true', 'yes'),
            'file': os.getenv('LOG_FILE_OUTPUT', 'true').lower() in ('1', 'true', 'yes'),
            'log_dir': 'logs',
            'max_bytes': 10 * 1024 * 1024,
            'backup_count': 5,
        }

# 日志级别映射
LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

# ==================== Formatter（格式化器）====================

# 日志格式 - 类似 Log4j PatternLayout
LOG_PATTERN = '%(asctime)s [%(levelname)-5s] %(name)s - %(message)s'
DATE_PATTERN = '%Y-%m-%d %H:%M:%S'

class ColoredFormatter(logging.Formatter):
    """控制台彩色输出格式化器"""
    COLORS = {
        'DEBUG': '\033[36m',     # 青色
        'INFO': '\033[32m',      # 绿色
        'WARNING': '\033[33m',   # 黄色
        'ERROR': '\033[31m',     # 红色
        'CRITICAL': '\033[1;31m', # 粗体红色
    }
    RESET = '\033[0m'
    
    def format(self, record):
        msg = super().format(record)
        color = self.COLORS.get(record.levelname, '')
        return f"{color}{msg}{self.RESET}" if color else msg


# ==================== LoggerFactory（日志工厂）====================

class LoggerFactory:
    """
    日志工厂 - 类似 Log4j 的 LoggerFactory
    用法：
        logger = LoggerFactory.get_logger(__name__)
        logger.info("message")
    """
    _loggers = {}
    _root_configured = False
    _config = None
    
    @classmethod
    def _get_config(cls):
        if cls._config is None:
            cls._config = _get_config()
        return cls._config
    
    @classmethod
    def _configure_root(cls):
        """配置根Logger（只执行一次）"""
        if cls._root_configured:
            return
        
        cfg = cls._get_config()
        level = LEVELS.get(cfg['level'].upper(), logging.INFO)
        
        # 根Logger
        root = logging.getLogger('app')
        root.setLevel(logging.DEBUG)  # 根Logger接收所有级别
        root.propagate = False
        
        # 清除已有handler
        root.handlers.clear()
        
        # 控制台 Appender
        if cfg['console']:
            console = logging.StreamHandler(sys.stdout)
            console.setLevel(level)
            console.setFormatter(ColoredFormatter(LOG_PATTERN, DATE_PATTERN))
            root.addHandler(console)
        
        # 文件 Appender（滚动文件）
        if cfg['file']:
            log_dir = cfg['log_dir']
            os.makedirs(log_dir, exist_ok=True)
            
            # 主日志文件 - 按大小滚动
            main_file = os.path.join(log_dir, 'app.log')
            file_handler = RotatingFileHandler(
                main_file,
                maxBytes=cfg['max_bytes'],
                backupCount=cfg['backup_count'],
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(logging.Formatter(LOG_PATTERN, DATE_PATTERN))
            root.addHandler(file_handler)
            
            # 错误日志单独文件
            error_file = os.path.join(log_dir, 'error.log')
            error_handler = RotatingFileHandler(
                error_file,
                maxBytes=cfg['max_bytes'],
                backupCount=cfg['backup_count'],
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(logging.Formatter(LOG_PATTERN, DATE_PATTERN))
            root.addHandler(error_handler)
        
        cls._root_configured = True
    
    @classmethod
    def get_logger(cls, name: str = None) -> logging.Logger:
        """
        获取Logger实例
        
        Args:
            name: Logger名称，通常使用 __name__
        
        Returns:
            Logger实例
        """
        cls._configure_root()
        
        logger_name = f"app.{name}" if name else "app"
        
        if logger_name not in cls._loggers:
            logger = logging.getLogger(logger_name)
            cls._loggers[logger_name] = logger
        
        return cls._loggers[logger_name]
    
    @classmethod
    def set_level(cls, level: str, logger_name: str = None):
        """
        动态设置日志级别
        
        Args:
            level: 级别名称 (DEBUG/INFO/WARNING/ERROR/CRITICAL)
            logger_name: 指定Logger名称，None则设置根Logger
        """
        lvl = LEVELS.get(level.upper(), logging.INFO)
        if logger_name:
            logging.getLogger(f"app.{logger_name}").setLevel(lvl)
        else:
            for handler in logging.getLogger('app').handlers:
                if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                    handler.setLevel(lvl)


# ==================== 便捷函数（兼容旧API）====================

# 默认Logger
_default_logger = None

def _get_default_logger():
    global _default_logger
    if _default_logger is None:
        _default_logger = LoggerFactory.get_logger('main')
    return _default_logger

def debug(msg, *args, **kwargs):
    _get_default_logger().debug(msg, *args, **kwargs)

def info(msg, *args, **kwargs):
    _get_default_logger().info(msg, *args, **kwargs)

def warning(msg, *args, **kwargs):
    _get_default_logger().warning(msg, *args, **kwargs)

def error(msg, *args, **kwargs):
    _get_default_logger().error(msg, *args, **kwargs)

def critical(msg, *args, **kwargs):
    _get_default_logger().critical(msg, *args, **kwargs)

def exception(msg, *args, **kwargs):
    _get_default_logger().exception(msg, *args, **kwargs)

def set_log_level(level):
    """设置日志级别（兼容旧API）"""
    LoggerFactory.set_level(level)

def log_startup():
    """记录应用启动"""
    from datetime import datetime
    info(f"{'='*20} 应用启动于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {'='*20}")


# ==================== 导出 ====================

# 类似 Java: private static final Logger logger = LoggerFactory.getLogger(Xxx.class);
get_logger = LoggerFactory.get_logger
