"""
SCUM Robot API 生产环境启动脚本

专为exe打包环境设计，移除了开发选项
适用于PyInstaller打包后的exe文件

作者: AI Assistant
日期: 2025年10月3日
"""

import subprocess
import sys
import os
from pathlib import Path


def get_exe_directory():
    """获取exe文件所在目录"""
    if getattr(sys, 'frozen', False):
        # 如果是打包后的exe
        return Path(sys.executable).parent
    else:
        # 如果是开发环境
        return Path(__file__).parent


def setup_database_path():
    """设置数据库路径，确保在exe环境下正确"""
    exe_dir = get_exe_directory()
    
    # 在exe目录下创建data文件夹存放数据库
    data_dir = exe_dir / "data"
    data_dir.mkdir(exist_ok=True)
    
    # 设置数据库路径环境变量
    db_path = data_dir / "scum_robot.db"
    os.environ['DATABASE_URL'] = f"sqlite:///{db_path}"
    
    print(f"[INFO] 数据库路径: {db_path}")
    return str(db_path)


def setup_static_files_path():
    """设置静态文件路径"""
    exe_dir = get_exe_directory()
    
    # 在exe目录下创建public文件夹
    public_dir = exe_dir / "public"
    public_dir.mkdir(exist_ok=True)
    
    # 创建必要的子目录
    (public_dir / "images").mkdir(exist_ok=True)
    (public_dir / "assets").mkdir(exist_ok=True)
    (public_dir / "fonts").mkdir(exist_ok=True)
    
    print(f"[INFO] 静态文件路径: {public_dir}")
    return str(public_dir)


def check_dependencies():
    """检查必要的依赖是否已安装"""
    # 在exe环境中，依赖已经打包，跳过检查
    if getattr(sys, 'frozen', False):
        print("[OK] exe环境，依赖已打包")
        return True

    required_packages = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "requests",
        "sqlalchemy"
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print("[ERROR] 缺少以下依赖包:")
        for pkg in missing_packages:
            print(f"   - {pkg}")
        return False

    print("[OK] 所有依赖已安装")
    return True


def start_api_server():
    """启动 API 服务器 (生产环境配置)"""
    print("[INFO] 启动 SCUM Robot API 服务 (生产环境)...")
    
    # 获取exe目录
    exe_dir = get_exe_directory()
    
    # 切换到exe目录
    os.chdir(exe_dir)
    
    # 设置路径
    db_path = setup_database_path()
    public_path = setup_static_files_path()
    
    # 启动 uvicorn 服务器 (生产环境配置)
    try:
        if getattr(sys, 'frozen', False):
            # exe环境：直接导入并启动
            print("[INFO] exe环境：直接启动FastAPI应用...")
            import uvicorn
            uvicorn.run(
                "bakend.api.main:app",
                host="0.0.0.0",
                port=8000,
                log_level="info"
            )
        else:
            # 开发环境：使用subprocess
            cmd = [
                sys.executable, "-m", "uvicorn",
                "bakend.api.main:app",
                "--host", "0.0.0.0",
                "--port", "8000",
            ]

            print("执行命令:", " ".join(cmd))
            print("API 文档地址: http://localhost:8000/docs")
            print("健康检查: http://localhost:8000/health")
            print("按 Ctrl+C 停止服务\n")

            # 启动服务器
            subprocess.run(cmd, check=True)

    except KeyboardInterrupt:
        print("\n[INFO] 服务已停止")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] 启动失败: {e}")
    except Exception as e:
        print(f"[ERROR] 未知错误: {e}")


def main():
    """主函数"""
    print("=" * 50)
    print("SCUM Robot API 启动器 (生产环境)")
    print("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        print("[WARN] 在exe环境中，依赖应该已经打包，继续启动...")
    
    # 启动服务器
    start_api_server()
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
