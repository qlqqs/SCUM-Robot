# -*- mode: python ; coding: utf-8 -*-

"""
SCUM Robot PyInstaller 配置文件

用于将SCUM Robot项目打包成exe文件
包含所有必要的依赖和资源文件

作者: AI Assistant
日期: 2025年10月3日
"""

import os
import sys
from pathlib import Path

# 获取项目根目录
import os
project_root = Path(os.getcwd())

# 定义数据文件和隐藏导入
datas = [
    # 前端构建文件
    (str(project_root / 'public'), 'public'),
    
    # 配置文件
    (str(project_root / '.env.example'), '.'),
]

# 隐藏导入 - 确保所有必要的模块都被包含
hiddenimports = [
    # FastAPI 相关
    'fastapi',
    'fastapi.applications',
    'fastapi.routing',
    'fastapi.middleware',
    'fastapi.middleware.cors',
    'fastapi.staticfiles',
    'fastapi.responses',
    'fastapi.exceptions',
    'fastapi.security',
    'fastapi.dependencies',
    
    # Uvicorn 相关
    'uvicorn',
    'uvicorn.main',
    'uvicorn.server',
    'uvicorn.config',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.websockets',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    
    # SQLAlchemy 相关
    'sqlalchemy',
    'sqlalchemy.orm',
    'sqlalchemy.engine',
    'sqlalchemy.dialects',
    'sqlalchemy.dialects.sqlite',
    'sqlalchemy.dialects.sqlite.pysqlite',
    'sqlalchemy.pool',
    'sqlalchemy.sql',
    'sqlalchemy.sql.sqltypes',
    'sqlalchemy.sql.schema',
    
    # Pydantic 相关
    'pydantic',
    'pydantic.fields',
    'pydantic.validators',
    'pydantic.types',
    'pydantic.json',
    
    # 其他依赖
    'requests',
    'python_dotenv',
    'pathlib',
    'zipfile',
    'json',
    'datetime',
    'typing',
    'logging',
    'contextlib',

    # 图像处理
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'PIL.ImageFont',
    
    # 项目模块
    'bakend',
    'bakend.api',
    'bakend.api.main',
    'bakend.api.routers',
    'bakend.api.routers.admin',
    'bakend.api.routers.backup',
    'bakend.modules',
    'bakend.modules.sql',
    'bakend.modules.sql.database',
    'bakend.modules.sql.models',
    'bakend.modules.sql.services',
    'bakend.modules.auth',
    'bakend.modules.auth.jwt_handler',
]

# 排除的模块 - 减少exe文件大小
excludes = [
    'tkinter',
    'matplotlib',
    'numpy',
    'pandas',
    'scipy',
    'cv2',
    'torch',
    'tensorflow',
    'jupyter',
    'notebook',
    'IPython',
]

# 主要分析配置
a = Analysis(
    ['start_api_production.py'],  # 使用生产环境启动脚本
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# 处理PYZ
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# 创建exe文件
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SCUM_Robot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # 使用UPX压缩
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 显示控制台窗口，便于查看日志
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以添加图标文件路径
    version_file=None,  # 可以添加版本信息文件
)
