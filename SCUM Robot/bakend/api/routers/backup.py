"""
备份和恢复功能API路由
"""

import os
import shutil
import zipfile
import tempfile
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from ...modules.auth import require_admin
from ...modules.sql.database.config import DatabaseConfig

router = APIRouter(prefix="/api/v1/backup", tags=["Backup Management"])


class BackupInfo(BaseModel):
    """备份信息模型"""
    filename: str
    size: int
    created_at: str
    includes_database: bool
    includes_images: bool


class BackupResponse(BaseModel):
    """备份响应模型"""
    success: bool
    message: str
    backup_info: BackupInfo = None


class RestoreResponse(BaseModel):
    """恢复响应模型"""
    success: bool
    message: str
    restored_items: Dict[str, bool] = None


def resolve_backup_path(filename: str) -> Path:
    """解析并校验备份文件路径，避免路径穿越。"""
    normalized_name = Path(filename).name
    if normalized_name != filename or not normalized_name.lower().endswith(".zip"):
        raise HTTPException(
            status_code=400,
            detail="非法备份文件名"
        )

    backups_dir = Path("backups").resolve()
    backup_path = (backups_dir / normalized_name).resolve()
    if backup_path.parent != backups_dir:
        raise HTTPException(
            status_code=400,
            detail="非法备份文件路径"
        )

    return backup_path


def get_database_path() -> str:
    """获取数据库文件路径"""
    db_config = DatabaseConfig()
    db_url = db_config._get_default_db_url()
    
    # 从 sqlite:///path 中提取路径
    if db_url.startswith('sqlite:///'):
        return db_url[10:]  # 移除 'sqlite:///'
    else:
        raise HTTPException(
            status_code=500,
            detail="不支持的数据库类型，仅支持SQLite"
        )


def get_images_path() -> str:
    """获取images文件夹路径，支持exe环境"""
    import sys
    if getattr(sys, 'frozen', False):
        # exe环境：使用exe目录下的public/images文件夹
        exe_dir = Path(sys.executable).parent
        images_path = exe_dir / "public" / "images"
        # 确保目录存在
        images_path.mkdir(parents=True, exist_ok=True)
        return str(images_path)
    else:
        # 开发环境：使用相对路径
        current_dir = Path(__file__).parent.parent.parent.parent
        images_path = current_dir / "public" / "images"
        return str(images_path)


@router.post("/create", response_model=BackupResponse)
async def create_backup(
    include_database: bool = True,
    include_images: bool = True,
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """
    创建系统备份
    
    Args:
        include_database: 是否包含数据库
        include_images: 是否包含图片文件
        current_user: 当前用户（需要管理员权限）
    
    Returns:
        BackupResponse: 备份结果
    """
    try:
        if not include_database and not include_images:
            raise HTTPException(
                status_code=400,
                detail="至少需要选择备份数据库或图片文件"
            )
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_dir = Path(temp_dir) / "backup"
            backup_dir.mkdir()
            
            # 备份数据库
            if include_database:
                try:
                    db_path = get_database_path()
                    if os.path.exists(db_path):
                        shutil.copy2(db_path, backup_dir / "scum_robot.db")
                    else:
                        raise HTTPException(
                            status_code=404,
                            detail=f"数据库文件不存在: {db_path}"
                        )
                except Exception as e:
                    raise HTTPException(
                        status_code=500,
                        detail=f"备份数据库失败: {str(e)}"
                    )
            
            # 备份图片文件夹
            if include_images:
                try:
                    images_path = get_images_path()
                    if os.path.exists(images_path):
                        shutil.copytree(images_path, backup_dir / "images")
                    else:
                        # 如果images文件夹不存在，创建一个空的
                        (backup_dir / "images").mkdir()
                except Exception as e:
                    raise HTTPException(
                        status_code=500,
                        detail=f"备份图片文件失败: {str(e)}"
                    )
            
            # 创建备份信息文件
            backup_info = {
                "created_at": datetime.now().isoformat(),
                "created_by": current_user.get("username", "unknown"),
                "includes_database": include_database,
                "includes_images": include_images,
                "version": "1.0"
            }
            
            with open(backup_dir / "backup_info.json", "w", encoding="utf-8") as f:
                import json
                json.dump(backup_info, f, ensure_ascii=False, indent=2)
            
            # 创建ZIP文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"scum_robot_backup_{timestamp}.zip"
            backup_path = Path(temp_dir) / backup_filename
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(backup_dir):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(backup_dir)
                        zipf.write(file_path, arcname)
            
            # 移动到下载目录
            downloads_dir = Path("backups")
            downloads_dir.mkdir(exist_ok=True)
            final_backup_path = downloads_dir / backup_filename
            shutil.move(backup_path, final_backup_path)
            
            # 获取文件大小
            file_size = final_backup_path.stat().st_size
            
            backup_info_response = BackupInfo(
                filename=backup_filename,
                size=file_size,
                created_at=backup_info["created_at"],
                includes_database=include_database,
                includes_images=include_images
            )
            
            return BackupResponse(
                success=True,
                message="备份创建成功",
                backup_info=backup_info_response
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"创建备份失败: {str(e)}"
        )


@router.get("/download/{filename}")
async def download_backup(
    filename: str,
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """
    下载备份文件
    
    Args:
        filename: 备份文件名
        current_user: 当前用户（需要管理员权限）
    
    Returns:
        FileResponse: 备份文件
    """
    try:
        backup_path = resolve_backup_path(filename)
        
        if not backup_path.exists():
            raise HTTPException(
                status_code=404,
                detail="备份文件不存在"
            )
        
        return FileResponse(
            path=str(backup_path),
            filename=filename,
            media_type="application/zip"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"下载备份文件失败: {str(e)}"
        )


@router.get("/list")
async def list_backups(
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """
    列出所有备份文件
    
    Args:
        current_user: 当前用户（需要管理员权限）
    
    Returns:
        List[BackupInfo]: 备份文件列表
    """
    try:
        backups_dir = Path("backups")
        if not backups_dir.exists():
            return []
        
        backups = []
        for backup_file in backups_dir.glob("*.zip"):
            try:
                stat = backup_file.stat()
                backups.append(BackupInfo(
                    filename=backup_file.name,
                    size=stat.st_size,
                    created_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    includes_database=True,  # 假设都包含，实际可以从zip中读取
                    includes_images=True
                ))
            except Exception:
                continue
        
        # 按创建时间倒序排列
        backups.sort(key=lambda x: x.created_at, reverse=True)
        return backups
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取备份列表失败: {str(e)}"
        )


@router.post("/restore", response_model=RestoreResponse)
async def restore_backup(
    backup_file: UploadFile = File(...),
    restore_database: bool = True,
    restore_images: bool = True,
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """
    从备份文件恢复系统

    Args:
        backup_file: 上传的备份文件
        restore_database: 是否恢复数据库
        restore_images: 是否恢复图片文件
        current_user: 当前用户（需要管理员权限）

    Returns:
        RestoreResponse: 恢复结果
    """
    try:
        if not restore_database and not restore_images:
            raise HTTPException(
                status_code=400,
                detail="至少需要选择恢复数据库或图片文件"
            )

        # 检查文件类型
        if not backup_file.filename.endswith('.zip'):
            raise HTTPException(
                status_code=400,
                detail="只支持ZIP格式的备份文件"
            )

        restored_items = {
            "database": False,
            "images": False
        }

        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            # 保存上传的文件
            upload_path = Path(temp_dir) / backup_file.filename
            with open(upload_path, "wb") as buffer:
                content = await backup_file.read()
                buffer.write(content)

            # 解压备份文件
            extract_dir = Path(temp_dir) / "extracted"
            extract_dir.mkdir()

            try:
                with zipfile.ZipFile(upload_path, 'r') as zipf:
                    zipf.extractall(extract_dir)
            except zipfile.BadZipFile:
                raise HTTPException(
                    status_code=400,
                    detail="无效的ZIP文件"
                )

            # 检查备份信息
            backup_info_path = extract_dir / "backup_info.json"
            if backup_info_path.exists():
                try:
                    import json
                    with open(backup_info_path, "r", encoding="utf-8") as f:
                        backup_info = json.load(f)
                    print(f"恢复备份信息: {backup_info}")
                except Exception as e:
                    print(f"读取备份信息失败: {e}")

            # 恢复数据库
            if restore_database:
                db_backup_path = extract_dir / "scum_robot.db"
                if db_backup_path.exists():
                    try:
                        db_path = get_database_path()

                        # 备份当前数据库
                        if os.path.exists(db_path):
                            backup_current_db = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                            shutil.copy2(db_path, backup_current_db)

                        # 恢复数据库
                        os.makedirs(os.path.dirname(db_path), exist_ok=True)
                        shutil.copy2(db_backup_path, db_path)
                        restored_items["database"] = True

                    except Exception as e:
                        raise HTTPException(
                            status_code=500,
                            detail=f"恢复数据库失败: {str(e)}"
                        )
                else:
                    if restore_database:
                        raise HTTPException(
                            status_code=400,
                            detail="备份文件中不包含数据库"
                        )

            # 恢复图片文件夹
            if restore_images:
                images_backup_path = extract_dir / "images"
                if images_backup_path.exists():
                    try:
                        images_path = get_images_path()

                        # 备份当前images文件夹
                        if os.path.exists(images_path):
                            backup_current_images = f"{images_path}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                            shutil.copytree(images_path, backup_current_images)
                            shutil.rmtree(images_path)

                        # 恢复images文件夹
                        shutil.copytree(images_backup_path, images_path)
                        restored_items["images"] = True

                    except Exception as e:
                        raise HTTPException(
                            status_code=500,
                            detail=f"恢复图片文件失败: {str(e)}"
                        )
                else:
                    if restore_images:
                        print("警告: 备份文件中不包含图片文件夹")

        success_items = [k for k, v in restored_items.items() if v]
        message = f"恢复完成，已恢复: {', '.join(success_items)}"

        return RestoreResponse(
            success=True,
            message=message,
            restored_items=restored_items
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"恢复备份失败: {str(e)}"
        )


@router.delete("/delete/{filename}")
async def delete_backup(
    filename: str,
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """
    删除备份文件

    Args:
        filename: 备份文件名
        current_user: 当前用户（需要管理员权限）

    Returns:
        JSONResponse: 删除结果
    """
    try:
        backup_path = resolve_backup_path(filename)

        if not backup_path.exists():
            raise HTTPException(
                status_code=404,
                detail="备份文件不存在"
            )

        backup_path.unlink()

        return JSONResponse(
            content={
                "success": True,
                "message": f"备份文件 {filename} 已删除"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"删除备份文件失败: {str(e)}"
        )
