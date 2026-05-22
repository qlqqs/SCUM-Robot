#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCUM Robot Web 自动构建和部署脚本
支持构建前端项目并自动集成到后端public文件夹
"""

import os
import sys
import subprocess
import shutil
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any


class BuildDeployManager:
    """构建部署管理器"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent.absolute()
        self.frontend_dir = self.root_dir / "SCUM Robot Web"
        self.backend_dir = self.root_dir / "SCUM Robot"
        self.backend_public = self.backend_dir / "public"
        
    def check_environment(self) -> bool:
        """检查环境依赖"""
        print("[INFO] 检查环境依赖...")
        
        # 检查Node.js
        try:
            result = subprocess.run(['node', '--version'], 
                                  capture_output=True, text=True, check=True)
            print(f"[OK] Node.js: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("[ERROR] 未找到Node.js，请先安装Node.js")
            return False
            
        # 检查npm
        try:
            result = subprocess.run(['npm', '--version'], 
                                  capture_output=True, text=True, check=True)
            print(f"[OK] npm: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("[ERROR] 未找到npm，请检查Node.js安装")
            return False
            
        # 检查前端项目目录
        if not self.frontend_dir.exists():
            print(f"[ERROR] 前端项目目录不存在: {self.frontend_dir}")
            return False
        print(f"[OK] 前端项目目录: {self.frontend_dir}")
        
        # 检查package.json
        package_json = self.frontend_dir / "package.json"
        if not package_json.exists():
            print(f"[ERROR] package.json不存在: {package_json}")
            return False
        print(f"[OK] package.json: {package_json}")
        
        return True
    
    def install_dependencies(self) -> bool:
        """安装依赖"""
        node_modules = self.frontend_dir / "node_modules"
        if node_modules.exists():
            print("[OK] 依赖已安装")
            return True
            
        print("[INFO] 安装依赖...")
        try:
            subprocess.run(['npm', 'install'], 
                         cwd=self.frontend_dir, check=True)
            print("[OK] 依赖安装完成")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] 依赖安装失败: {e}")
            return False
    
    def clean_backend_public(self) -> bool:
        """清理后端public文件夹，但保护重要的业务数据文件夹"""
        print("[INFO] 清理后端public文件夹...")
        try:
            if not self.backend_public.exists():
                print("[INFO] 后端public文件夹不存在，跳过清理")
                return True

            # 保护的文件夹列表（包含重要的业务数据）
            protected_dirs = ['images']
            protected_files = []

            # 读取public目录中的所有项目
            items = list(self.backend_public.iterdir())

            for item in items:
                # 跳过受保护的文件夹和文件
                if item.name in protected_dirs or item.name in protected_files:
                    print(f"[KEEP] 保护文件夹/文件: {item.name}")
                    continue

                # 删除其他文件和文件夹
                if item.is_dir():
                    shutil.rmtree(item)
                    print(f"[DEL] 删除文件夹: {item.name}")
                else:
                    item.unlink()
                    print(f"[DEL] 删除文件: {item.name}")

            print("[OK] 清理完成（已保护重要数据文件夹）")
            return True
        except Exception as e:
            print(f"[ERROR] 清理失败: {e}")
            return False
    
    def build_frontend(self, mode: str = "production") -> bool:
        """构建前端项目"""
        print(f"[INFO] 构建前端项目 ({mode} 模式)...")
        
        try:
            if mode == "production":
                cmd = ['npm', 'run', 'build:prod']
            else:
                cmd = ['npm', 'run', 'build:dev']
                
            result = subprocess.run(cmd, cwd=self.frontend_dir, 
                                  capture_output=True, text=True, check=True)
            print("[OK] 前端构建完成")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] 前端构建失败: {e}")
            if e.stdout:
                print(f"标准输出: {e.stdout}")
            if e.stderr:
                print(f"错误输出: {e.stderr}")
            return False
    
    def verify_build(self) -> Dict[str, Any]:
        """验证构建结果"""
        print("[INFO] 验证构建结果...")

        result = {
            "success": True,
            "errors": [],
            "stats": {}
        }

        # 检查关键文件
        required_files = [
            self.backend_public / "index.html",
        ]

        # 更新目录检查 - 使用新的自动化构建目录结构
        required_dirs = [
            self.backend_public / "assets",
            self.backend_public / "assets" / "fonts",
        ]

        for file_path in required_files:
            if not file_path.exists():
                result["success"] = False
                result["errors"].append(f"缺少文件: {file_path}")

        for dir_path in required_dirs:
            if not dir_path.exists():
                result["success"] = False
                result["errors"].append(f"缺少目录: {dir_path}")

        # 统计文件数量
        if self.backend_public.exists():
            assets_dir = self.backend_public / "assets"
            fonts_dir = self.backend_public / "assets" / "fonts"  # 更新为新的字体目录

            if assets_dir.exists():
                js_files = list(assets_dir.glob("*.js"))
                css_files = list(assets_dir.glob("*.css"))
                result["stats"]["js_files"] = len(js_files)
                result["stats"]["css_files"] = len(css_files)

            if fonts_dir.exists():
                font_files = list(fonts_dir.glob("*.woff2"))
                result["stats"]["font_files"] = len(font_files)

        if result["success"]:
            print("[OK] 构建验证通过")
            print("[INFO] 统计信息:")
            for key, value in result["stats"].items():
                print(f"   - {key}: {value}")
        else:
            print("[ERROR] 构建验证失败")
            for error in result["errors"]:
                print(f"   - {error}")

        return result
    
    def deploy(self, mode: str = "production", clean: bool = True) -> bool:
        """完整的部署流程"""
        print(f"[INFO] 开始部署流程 ({mode} 模式)")
        print("=" * 50)
        
        # 检查环境
        if not self.check_environment():
            return False
        
        # 安装依赖
        if not self.install_dependencies():
            return False
        
        # 清理（可选）
        if clean and not self.clean_backend_public():
            return False
        
        # 构建
        if not self.build_frontend(mode):
            return False
        
        # 验证
        result = self.verify_build()
        if not result["success"]:
            return False
        
        print("=" * 50)
        print("[OK] 部署完成")
        print(f"[INFO] 输出目录: {self.backend_public}")
        
        return True


def main():
    """主函数"""
    manager = BuildDeployManager()

    # 检查是否在虚拟环境中运行
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("[INFO] 运行在虚拟环境中")
    else:
        print("[WARN] 建议在虚拟环境中运行，可以使用: uv run python build_deploy.py")

    if len(sys.argv) > 1:
        # 命令行模式
        command = sys.argv[1].lower()
        
        if command == "prod":
            success = manager.deploy("production")
        elif command == "dev":
            success = manager.deploy("development")
        elif command == "clean":
            success = manager.clean_backend_public()
        elif command == "verify":
            result = manager.verify_build()
            success = result["success"]
        else:
            print(f"未知命令: {command}")
            print("可用命令: prod, dev, clean, verify")
            success = False
    else:
        # 交互模式
        print("SCUM Robot Web 自动构建和部署工具")
        print("=" * 50)
        
        while True:
            print("\n请选择操作:")
            print("1. 生产环境构建并部署")
            print("2. 开发环境构建并部署")
            print("3. 清理后端public文件夹")
            print("4. 验证构建结果")
            print("5. 退出")
            
            choice = input("\n请输入选择 (1-5): ").strip()
            
            if choice == "1":
                success = manager.deploy("production")
            elif choice == "2":
                success = manager.deploy("development")
            elif choice == "3":
                success = manager.clean_backend_public()
            elif choice == "4":
                result = manager.verify_build()
                success = result["success"]
            elif choice == "5":
                print("再见")
                break
            else:
                print("[ERROR] 无效选择，请重新输入")
                continue
            
            if success:
                print("[OK] 操作完成")
            else:
                print("[ERROR] 操作失败")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
