"""
SCUM Robot EXE 构建脚本

用于自动化构建exe文件的脚本
包含前端构建、依赖检查、PyInstaller打包等步骤

作者: AI Assistant
日期: 2025年10月3日
"""

import subprocess
import sys
import os
import shutil
from pathlib import Path


def check_pyinstaller():
    """检查PyInstaller是否已安装"""
    try:
        import PyInstaller
        print("[OK] PyInstaller 已安装")
        return True
    except ImportError:
        print("[ERROR] PyInstaller 未安装")
        print("请运行: pip install pyinstaller")
        return False


def build_frontend():
    """构建前端项目"""
    print("[INFO] 开始构建前端项目...")

    # 获取前端目录 - 相对于当前SCUM Robot目录
    current_dir = Path(__file__).parent
    frontend_dir = current_dir.parent / "SCUM Robot Web"

    if not frontend_dir.exists():
        print(f"[ERROR] 前端目录不存在: {frontend_dir}")
        return False

    # 检查package.json是否存在
    if not (frontend_dir / "package.json").exists():
        print("[ERROR] package.json 不存在")
        return False

    try:
        # 保存当前目录
        original_dir = os.getcwd()

        # 切换到前端目录
        os.chdir(frontend_dir)
        print(f"切换到目录: {frontend_dir}")

        # 运行npm build
        print("执行: npm run build")
        result = subprocess.run(["npm", "run", "build"],
                              capture_output=True, text=True, check=True, shell=True,
                              encoding='utf-8', errors='ignore')

        print("[OK] 前端构建成功")

        # 恢复原目录
        os.chdir(original_dir)
        return True

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] 前端构建失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False
    except Exception as e:
        print(f"[ERROR] 前端构建异常: {e}")
        return False
    finally:
        # 确保恢复原目录
        try:
            os.chdir(original_dir)
        except:
            pass


def install_dependencies():
    """安装Python依赖"""
    print("[INFO] 检查Python依赖...")

    project_root = Path(__file__).parent

    # 在uv环境中，依赖应该已经安装
    try:
        print("执行: uv sync")
        subprocess.run(["uv", "sync"], check=True, cwd=project_root.parent)
        print("[OK] Python依赖同步成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[WARN] uv sync失败: {e}")
        print("[INFO] 尝试使用已安装的依赖...")
        return True  # 继续构建，因为依赖可能已经安装
    except FileNotFoundError:
        print("[WARN] uv未找到，跳过依赖安装")
        return True


def clean_build_directory():
    """清理构建目录"""
    print("🧹 清理构建目录...")
    
    project_root = Path(__file__).parent
    
    # 清理目录列表
    clean_dirs = [
        project_root / "build",
        project_root / "dist",
        project_root / "__pycache__",
    ]
    
    for clean_dir in clean_dirs:
        if clean_dir.exists():
            shutil.rmtree(clean_dir)
            print(f"[INFO] 已删除: {clean_dir}")

    print("[OK] 构建目录清理完成")


def build_exe():
    """使用PyInstaller构建exe"""
    print("[INFO] 开始构建exe文件...")
    
    project_root = Path(__file__).parent
    spec_file = project_root / "scum_robot.spec"

    if not spec_file.exists():
        print(f"[ERROR] spec文件不存在: {spec_file}")
        return False
    
    try:
        # 切换到项目根目录
        os.chdir(project_root)
        
        # 运行PyInstaller
        cmd = [sys.executable, "-m", "PyInstaller", str(spec_file), "--clean"]
        print(f"执行: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, check=True)
        
        print("[OK] exe文件构建成功")
        
        # 检查输出文件
        exe_file = project_root / "dist" / "SCUM_Robot.exe"
        if exe_file.exists():
            print(f"[INFO] exe文件位置: {exe_file}")
            print(f"[INFO] 文件大小: {exe_file.stat().st_size / 1024 / 1024:.1f} MB")
        else:
            print("[WARN] exe文件未找到")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] exe构建失败: {e}")
        return False


def copy_additional_files():
    """复制额外的文件到dist目录"""
    print("📋 复制额外文件...")

    project_root = Path(__file__).parent
    dist_dir = project_root / "dist"
    public_src = project_root / "public"
    public_dst = dist_dir / "public"

    if not dist_dir.exists():
        print("[ERROR] dist目录不存在")
        return False

    # 确保public目录存在
    public_dst.mkdir(exist_ok=True)

    # 复制前端文件
    if public_src.exists():
        print("[INFO] 复制前端文件...")

        # 复制关键文件
        key_files = ["index.html", "favicon.ico"]
        for file_name in key_files:
            src_file = public_src / file_name
            dst_file = public_dst / file_name
            if src_file.exists():
                shutil.copy2(src_file, dst_file)
                print(f"[INFO] 已复制: {file_name}")

        # 复制目录 - 更新为新的自动化构建目录结构
        key_dirs = ["assets", "images"]  # 移除fonts，因为字体现在在assets/fonts中
        for dir_name in key_dirs:
            src_dir = public_src / dir_name
            dst_dir = public_dst / dir_name
            if src_dir.exists():
                if dst_dir.exists():
                    shutil.rmtree(dst_dir)
                shutil.copytree(src_dir, dst_dir)
                print(f"[INFO] 已复制目录: {dir_name}")

        # 检查自动化构建的字体文件是否已存在
        assets_fonts_dir = public_dst / "assets" / "fonts"
        if assets_fonts_dir.exists() and list(assets_fonts_dir.glob("*.woff2")):
            print("[OK] 字体文件已通过自动化构建处理: assets/fonts")
        else:
            # 如果自动化构建的字体文件不存在，则从原始位置复制（向后兼容）
            fonts_source = public_src / "fonts" / "inter"
            if fonts_source.exists():
                assets_fonts_dir.mkdir(parents=True, exist_ok=True)
                for font_file in fonts_source.glob("*.woff2"):
                    shutil.copy2(font_file, assets_fonts_dir / font_file.name)
                print("[OK] 备用字体文件复制完成: fonts/inter -> assets/fonts")
            else:
                print("[WARN] 字体文件未找到，请检查构建配置")

        # 复制原始fonts目录（如果需要向后兼容）
        fonts_dir = public_src / "fonts"
        if fonts_dir.exists():
            dst_fonts_dir = public_dst / "fonts"
            if dst_fonts_dir.exists():
                shutil.rmtree(dst_fonts_dir)
            shutil.copytree(fonts_dir, dst_fonts_dir)
            print("[INFO] 已复制目录: fonts (向后兼容)")

    # 复制配置文件
    config_files = [
        (".env.example", "配置文件示例"),
        ("README.md", "说明文档") if (project_root / "README.md").exists() else None,
    ]

    for file_info in config_files:
        if file_info is None:
            continue

        src_file, description = file_info
        src_path = project_root / src_file
        dst_path = dist_dir / src_file

        if src_path.exists():
            shutil.copy2(src_path, dst_path)
            print(f"[INFO] 已复制: {description}")

    print("[OK] 所有文件复制完成")
    return True


def main():
    """主函数"""
    print("=" * 60)
    print("SCUM Robot EXE 构建器")
    print("=" * 60)
    
    # 检查PyInstaller
    if not check_pyinstaller():
        return 1
    
    # 清理构建目录
    clean_build_directory()
    
    # 构建前端
    if not build_frontend():
        print("[ERROR] 前端构建失败，停止构建")
        return 1
    
    # 安装依赖
    if not install_dependencies():
        print("[ERROR] 依赖安装失败，停止构建")
        return 1
    
    # 构建exe
    if not build_exe():
        print("[ERROR] exe构建失败")
        return 1
    
    # 复制额外文件
    copy_additional_files()
    
    print("\n" + "=" * 60)
    print("[OK] SCUM Robot exe构建完成！")
    print("[INFO] 输出目录: dist/")
    print("[INFO] 可执行文件: dist/SCUM_Robot.exe")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
