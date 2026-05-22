"""
SCUM Robot API 启动脚本

用于启动 FastAPI 服务

作者: GitHub Copilot
日期: 2025年9月17日
"""

import subprocess
import sys
import os
from pathlib import Path


def check_dependencies():
    """检查必要的依赖是否已安装"""
    required_packages = [
        "fastapi",
        "uvicorn", 
        "pydantic",
        "requests"
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
        print("\n请运行以下命令安装依赖:")
        print("pip install -r requirements.txt")
        return False
    
    print("[OK] 所有依赖已安装")
    return True


def start_api_server():
    """启动 API 服务器"""
    print("[INFO] 启动 SCUM Robot API 服务...")
    
    # 获取当前脚本目录
    current_dir = Path(__file__).parent
    
    # 切换到项目根目录
    os.chdir(current_dir)
    
    # 启动 uvicorn 服务器
    try:
        cmd = [
            sys.executable, "-m", "uvicorn",
            "bakend.api.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload",
            "--reload-dir", "./bakend"
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
    print("SCUM Robot API 启动器")
    print("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        return 1
    
    # 启动服务器
    start_api_server()
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
