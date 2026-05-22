"""
SCUM Robot API 服务

使用 FastAPI 封装 SCUM Robot 模块功能，提供 RESTful API 接口

作者: GitHub Copilot
日期: 2025年9月17日
版本: 1.0
"""

from fastapi import FastAPI, HTTPException, status, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from contextlib import asynccontextmanager
import sys
import os
import json

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# 导入路由
from bakend.api.routers import robot, items, auth, users, gifts, admin, signin, vip, character, payment_config, recharge_package, config, backup


# 全局数据库管理器
global_db_manager = None

def get_global_db_manager():
    """获取全局数据库管理器实例"""
    global global_db_manager
    if global_db_manager is None:
        # 如果全局管理器未初始化，创建一个临时的
        from bakend.modules.sql.database import DatabaseManager
        temp_manager = DatabaseManager()  # 使用默认配置（支持exe环境）
        temp_manager.init_database()
        return temp_manager
    return global_db_manager


def get_db_manager():
    """FastAPI依赖函数：获取数据库管理器"""
    return get_global_db_manager()


def get_db_session():
    """FastAPI依赖函数：获取数据库会话"""
    db_manager = get_global_db_manager()
    return db_manager.get_db_session()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global global_db_manager

    # 启动时执行
    print("[INFO] SCUM Robot API 服务启动中...")

    # 初始化全局数据库管理器
    try:
        from bakend.modules.sql.database import DatabaseManager
        # 使用DatabaseConfig的默认路径配置（支持exe环境）
        global_db_manager = DatabaseManager()

        # 初始化数据库表结构
        if global_db_manager.init_database():
            print("[OK] 数据库表结构初始化成功")

            # 检查数据是否已初始化
            if not global_db_manager.is_data_initialized():
                print("[INFO] 检测到数据库未初始化，开始创建默认数据...")

                # 获取初始化状态详情
                status = global_db_manager.get_initialization_status()
                missing_data = status.get('missing_data', [])

                if missing_data:
                    print(f"[INFO] 缺失的数据项: {', '.join(missing_data)}")

                # 自动初始化数据
                if global_db_manager.auto_initialize_data():
                    print("[OK] 默认数据创建成功")
                    bootstrap_username = (os.getenv("BOOTSTRAP_ADMIN_USERNAME") or "superadmin").strip() or "superadmin"
                    print(f"[OK] 首次超级管理员账户已创建: {bootstrap_username}")
                    print("[OK] VIP0配置已创建并受保护")
                else:
                    raise RuntimeError(
                        "数据库首次初始化失败，请检查 BOOTSTRAP_ADMIN_PASSWORD 等配置后重试。"
                    )
            else:
                print("[OK] 数据库数据已初始化")

                # 显示初始化状态摘要
                status = global_db_manager.get_initialization_status()
                required_data = status.get('required_data', {})
                print(f"[INFO] 数据完整性检查: {sum(required_data.values())}/{len(required_data)} 项完整")

            # 初始化配置管理器
            from bakend.modules.config import config_manager
            config_manager.init(global_db_manager)
        else:
            raise RuntimeError("数据库表结构初始化失败")
    except Exception as e:
        print(f"[ERROR] 数据库初始化错误: {e}")
        import traceback
        traceback.print_exc()
        if global_db_manager:
            global_db_manager.close()
            global_db_manager = None
        raise

    # 检查 Windows 环境
    import platform
    if platform.system() != 'Windows':
        print("[WARN] 此应用仅在 Windows 环境下完整支持")

    yield

    # 关闭时执行
    print("[INFO] SCUM Robot API 服务关闭")
    if global_db_manager:
        global_db_manager.close()
        print("[OK] 数据库连接已关闭")


# 创建 FastAPI 实例
app = FastAPI(
    title="SCUM Robot API",
    description="SCUM 游戏自动化工具的 RESTful API 接口",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 添加UTF-8编码中间件
@app.middleware("http")
async def ensure_utf8_encoding(request: Request, call_next):
    """确保所有响应都使用UTF-8编码"""
    response = await call_next(request)

    # 如果是JSON响应，确保Content-Type包含charset=utf-8
    if response.headers.get("content-type", "").startswith("application/json"):
        response.headers["content-type"] = "application/json; charset=utf-8"

    return response

# 包含路由
app.include_router(auth.router, tags=["Authentication"])
app.include_router(users.router, tags=["User Management"])
app.include_router(gifts.router, tags=["Gift Management"])
app.include_router(signin.router, tags=["Signin System"])
app.include_router(vip.router, tags=["VIP System"])
app.include_router(character.router, tags=["Character System"])
app.include_router(admin.router, tags=["Admin Management"])
app.include_router(robot.router, prefix="/api/v1/robot", tags=["Robot"])
app.include_router(items.router, tags=["Items"])
app.include_router(payment_config.router)
app.include_router(recharge_package.router)
app.include_router(config.router)
app.include_router(backup.router, tags=["Backup Management"])

# 配置静态文件服务
def get_public_directory():
    """获取public目录路径，支持exe环境"""
    if getattr(sys, 'frozen', False):
        # exe环境：使用exe目录下的public文件夹
        exe_dir = os.path.dirname(sys.executable)
        public_dir = os.path.join(exe_dir, 'public')
    else:
        # 开发环境：使用相对路径
        project_root = os.path.join(os.path.dirname(__file__), '..', '..')
        public_dir = os.path.join(project_root, 'public')

    # 确保运行期所需目录存在，即使尚未执行前端构建也不阻塞API启动
    os.makedirs(public_dir, exist_ok=True)
    os.makedirs(os.path.join(public_dir, 'images'), exist_ok=True)
    os.makedirs(os.path.join(public_dir, 'assets'), exist_ok=True)
    os.makedirs(os.path.join(public_dir, 'fonts'), exist_ok=True)
    return public_dir

public_dir = get_public_directory()
if os.path.exists(public_dir):
    # 主要的静态文件服务：/static 路径
    app.mount("/static", StaticFiles(directory=public_dir), name="static")
    print(f"[OK] 静态文件服务已配置: {public_dir} -> /static")

    # 兼容性支持：/assets 路径（用于前端资源）
    app.mount("/assets", StaticFiles(directory=os.path.join(public_dir, "assets")), name="assets")
    print(f"[OK] 前端资源兼容性已配置: {public_dir}/assets -> /assets")

    print(f"[INFO] 静态资源可通过 /static/ 和 /assets/ 路径访问")
else:
    print(f"[WARN] public目录不存在: {public_dir}")

# 前端SPA支持 - 处理前端路由
@app.get("/favicon.ico")
async def favicon():
    """返回网站图标"""
    favicon_path = os.path.join(public_dir, "favicon.ico")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    else:
        raise HTTPException(status_code=404, detail="Favicon not found")

# 所有静态资源统一通过 /static/ 路径访问，由 StaticFiles 挂载处理
# 包括：/static/assets/, /static/fonts/, /static/images/ 等
# 不再需要单独的路由，避免路径冲突和重复

# API状态和健康检查路由
@app.get("/api")
async def api_root():
    """API根路径 - API 状态信息"""
    return {
        "message": "SCUM Robot API 服务运行中",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "api_prefix": "/api/v1",
        "available_modules": {
            "auth": "/api/v1/auth",
            "users": "/api/v1/users",
            "gifts": "/api/v1/gifts",
            "signin": "/api/v1/signin",
            "vip": "/api/v1/vip",
            "character": "/api/v1/character",
            "admin": "/api/v1/admin",
            "robot": "/api/v1/robot",
            "sql": "/api/v1/sql"
        }
    }

@app.get("/health")
@app.get("/api/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "message": "SCUM Robot API 服务正常运行"
    }

# SPA路由支持 - 必须放在最后，作为catch-all路由
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """
    SPA (Single Page Application) 支持
    对于所有非API路径，返回index.html让前端路由器处理
    """
    # API路径不应该被这个路由处理
    if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("redoc"):
        raise HTTPException(status_code=404, detail="API endpoint not found")

    # 检查是否是静态文件请求
    if (full_path.startswith("static/") or
        full_path.startswith("assets/") or
        full_path.startswith("fonts/") or
        full_path.startswith("icons/") or
        full_path.endswith(('.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2', '.ttf', '.eot'))):
        raise HTTPException(status_code=404, detail="Static file not found")

    # 返回index.html用于前端路由
    index_path = os.path.join(public_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    else:
        raise HTTPException(status_code=404, detail="Frontend application not found")

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    _ = request  # 忽略未使用的参数
    """全局异常处理器"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": str(exc),
            "detail": "服务器内部错误，请检查日志或联系管理员"
        }
    )


if __name__ == "__main__":
    # 开发环境运行
    uvicorn.run(
        "bakend.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["bakend"],
        log_level="info"
    )
