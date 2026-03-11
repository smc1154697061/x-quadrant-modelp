# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 配置文件
使用方法：pyinstaller build_spec.py
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 项目根目录
block_cipher = None
project_root = os.path.abspath('.')

# 收集所有数据文件
datas = []

# 添加数据目录
datas += [(os.path.join(project_root, 'data'), 'data')]

# 添加日志目录（空目录也要创建）
datas += [(os.path.join(project_root, 'logs'), 'logs')]

# 收集所有隐藏导入
hiddenimports = [
    # Flask 相关
    'flask',
    'flask_cors',
    'flask.json',
    'flask.json.tag',
    # 注意：flask-sock 已移除，不需要再导入
    
    # 应用模块
    'app',
    'app.controllers',
    'app.controllers.auth_controller',
    'app.controllers.base',
    'app.controllers.chat_controller',
    'app.controllers.extraction_controller',
    'app.controllers.knowledge_controller',
    'app.controllers.user_controller',
    'app.core',
    'app.core.decorators',
    'app.core.middlewares',
    'app.dao',
    'app.dao.base_dao',
    'app.dao.bot_dao',
    'app.dao.conversation_dao',
    'app.dao.knowledge_dao',
    'app.dao.message_dao',
    'app.dao.user_dao',
    'app.entity',
    'app.entity.bot',
    'app.entity.conversation',
    'app.entity.knowledge_base',
    'app.entity.message',
    'app.entity.user',
    'app.models.embeddings',
    'app.models.embeddings.base',
    'app.models.embeddings.modelfactory',
    'app.models.embeddings.modelscope_adapter',
    'app.models.llm',
    'app.models.llm.ollama_model',
    'app.models.vector_store',
    'app.models.vector_store.base',
    'app.models.vector_store.pg_vector_store',
    'app.models.vector_store.povector_store',
    'app.routes',
    'app.routes.web_routes',
    'app.services',
    'app.services.auth_service',
    'app.services.chat_service',
    'app.services.extraction_service',
    'app.services.knowledge_service',
    'app.services.user_service',
    'app.utils',
    'app.utils.document_loader',
    
    # API 模块
    'apis',
    'apis.extraction_api',
    
    # 公共模块
    'common',
    'common.db_utils',
    'common.document_extractor',
    'common.error_codes',
    'common.json_utils',
    'common.log_',
    'common.mail_client',
    'common.minio_client',
    'common.minio_utils',
    'common.redis_client',
    'common.redis_utils',
    
    # 配置模块
    'config',
    'config.base',
    
    # 数据库相关
    'psycopg2',
    'pymysql',
    
    # Redis
    'redis',
    
    # MinIO
    'minio',
    
    # 文档处理
    'docx',
    'python-docx',
    'pypdf',
    'PyPDF2',
    'markdown',
    'PIL',
    'Pillow',
    
    # AI 相关
    'langchain',
    'langchain_community',
    'langchain_core',
    'langchain_ollama',
    
    # 其他依赖
    'jwt',
    'bcrypt',
    'email_validator',
    'werkzeug',
    'werkzeug.security',
    'jinja2',
    'click',
    'itsdangerous',
    'requests',
    'urllib3',
    'certifi',
    'charset_normalizer',
    'idna',
]

# 分析选项
a = Analysis(
    ['run.py'],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'chat-vue',  # 排除前端目录
        'test',      # 排除测试目录
        'scripts',   # 排除脚本目录
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# PYZ 归档
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# EXE 可执行文件
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='x-quadrant-modelp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # 使用 UPX 压缩
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 显示控制台（方便查看日志）
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以添加图标: icon='app_icon.ico'
)

# 如果需要打包成目录形式（推荐用于调试）
# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     name='x-quadrant-modelp',
# )

