"""
礼包管理相关API路由
"""

from typing import Optional, List, Dict, Any, Union
from fastapi import APIRouter, HTTPException, status, Depends, Query, File, UploadFile
from pydantic import BaseModel, Field, validator
from datetime import datetime
from pathlib import Path
import hashlib
import time
import re
import json
from PIL import Image

from ...modules.sql.services.gift_service import GiftService
from ...modules.sql.services.service_result import ServiceErrorType
from ...modules.auth import jwt_bearer, require_admin
from ...modules.sql.database.manager import DatabaseManager
from ...modules.sql.models import GiftType


router = APIRouter(prefix="/api/v1/gifts", tags=["Gift Management"])


# Pydantic 模型
class GiftItem(BaseModel):
    """礼包物品模型"""
    command: str = Field(..., description="游戏命令")
    item: str = Field(..., description="物品代码")
    amount: int = Field(..., ge=1, description="数量")


# 辅助函数
def normalize_items_config(items_config: Any) -> List[Dict[str, Any]]:
    """
    将items_config标准化为统一的数组格式

    Args:
        items_config: 物品配置，可以是字典格式或数组格式

    Returns:
        List[Dict]: 标准化后的数组格式
    """
    if isinstance(items_config, dict):
        # 字典格式转换为数组格式
        return [
            {
                "command": "#spawnitem",
                "item": item_code,
                "amount": amount
            }
            for item_code, amount in items_config.items()
        ]
    elif isinstance(items_config, list):
        # 数组格式，转换为字典格式以便存储
        return [
            {
                "command": item.command,
                "item": item.item,
                "amount": item.amount
            }
            for item in items_config
        ]
    else:
        raise ValueError("items_config must be either dict or list")


# 图片处理函数
def validate_filename(filename: str) -> bool:
    """验证文件名是否安全"""
    if not filename or len(filename) > 255:
        return False

    # 检查是否包含非法字符
    illegal_chars = r'[<>:"/\\|?*\x00-\x1f]'
    if re.search(illegal_chars, filename):
        return False

    return True

def is_valid_image_file(filename: str) -> bool:
    """验证文件是否为有效的图片格式"""
    valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
    return Path(filename).suffix.lower() in valid_extensions

async def validate_file_content(file: UploadFile) -> bool:
    """验证文件内容是否为真实的图片文件"""
    try:
        # 读取文件头部字节来验证文件类型
        content = await file.read(32)  # 读取前32字节
        await file.seek(0)  # 重置文件指针

        # 检查常见图片格式的文件头
        if content.startswith(b'\xff\xd8\xff'):  # JPEG
            return True
        elif content.startswith(b'\x89PNG\r\n\x1a\n'):  # PNG
            return True
        elif content.startswith(b'GIF87a') or content.startswith(b'GIF89a'):  # GIF
            return True
        elif content.startswith(b'RIFF') and b'WEBP' in content[:12]:  # WebP
            return True
        elif content.startswith(b'BM'):  # BMP
            return True

        return False
    except Exception:
        return False

def get_upload_directory() -> tuple[Path, Path]:
    """获取上传目录路径，返回(原图目录, 缩略图目录)"""
    # 获取项目根目录
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent.parent
    imgs_dir = project_root / "public" / "images" / "gifts" / "imgs"
    thumbs_dir = project_root / "public" / "images" / "gifts" / "thumbs"

    # 确保目录存在
    imgs_dir.mkdir(parents=True, exist_ok=True)
    thumbs_dir.mkdir(parents=True, exist_ok=True)
    return imgs_dir, thumbs_dir

def generate_gift_filename(gift_id: int, original_filename: str) -> str:
    """为礼包生成唯一文件名"""
    file_extension = Path(original_filename).suffix.lower()
    timestamp = str(int(time.time() * 1000))
    return f"gift_{gift_id}_{timestamp}{file_extension}"

def generate_thumbnail_filename(gift_id: int, original_filename: str) -> str:
    """为礼包生成缩略图文件名"""
    file_extension = Path(original_filename).suffix.lower()
    timestamp = str(int(time.time() * 1000))
    return f"gift_{gift_id}_{timestamp}_thumb{file_extension}"

def create_thumbnail(original_path: Path, thumbnail_path: Path, size: tuple = (200, 200)) -> bool:
    """创建缩略图"""
    try:
        with Image.open(original_path) as img:
            # 转换为RGB模式（处理RGBA等格式）
            if img.mode in ('RGBA', 'LA', 'P'):
                # 创建白色背景
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # 创建缩略图（保持宽高比）
            img.thumbnail(size, Image.Resampling.LANCZOS)

            # 保存缩略图
            img.save(thumbnail_path, optimize=True, quality=85)

            return True
    except Exception as e:
        print(f"创建缩略图失败: {e}")
        return False

async def save_gift_image_with_thumbnail(file: UploadFile, filename: str, thumbnail_filename: str) -> tuple[str, Optional[str]]:
    """保存礼包图片和缩略图，返回原图和缩略图的相对路径"""
    try:
        imgs_dir, thumbs_dir = get_upload_directory()
        file_path = imgs_dir / filename
        thumbnail_path = thumbs_dir / thumbnail_filename

        # 保存原图
        with open(file_path, "wb") as buffer:
            content = await file.read()
            if not content:
                raise ValueError("文件内容为空")
            buffer.write(content)

        # 验证原图是否成功保存
        if not file_path.exists() or file_path.stat().st_size == 0:
            raise ValueError("原图保存失败")

        # 生成缩略图
        if not create_thumbnail(file_path, thumbnail_path):
            # 缩略图生成失败，但不影响原图上传
            print(f"警告: 缩略图生成失败，但原图上传成功")
            thumbnail_url = None
        else:
            thumbnail_url = f"/static/images/gifts/thumbs/{thumbnail_filename}"

        # 返回用于HTTP访问的相对路径
        image_url = f"/static/images/gifts/imgs/{filename}"
        return image_url, thumbnail_url

    except Exception as e:
        # 如果保存失败，尝试清理可能创建的文件
        try:
            imgs_dir, thumbs_dir = get_upload_directory()
            file_path = imgs_dir / filename
            thumbnail_path = thumbs_dir / thumbnail_filename
            if file_path.exists():
                file_path.unlink()
            if thumbnail_path.exists():
                thumbnail_path.unlink()
        except:
            pass
        raise ValueError(f"保存文件失败: {str(e)}")


def delete_gift_image_files(image_url: Optional[str]) -> bool:
    """
    删除礼包的图片文件和缩略图文件

    Args:
        image_url: 图片URL

    Returns:
        是否成功删除
    """
    if not image_url:
        return True

    try:
        imgs_dir, thumbs_dir = get_upload_directory()

        # 从URL提取文件名
        url_path = image_url.replace('/static/images/gifts/imgs/', '').replace('/static/images/gifts/', '').replace('/static/images/', '')
        filename = Path(url_path).name
        if not filename:
            return True

        # 构建文件路径
        file_path = imgs_dir / filename

        # 生成缩略图文件名
        file_stem = Path(filename).stem
        file_suffix = Path(filename).suffix
        thumbnail_filename = f"{file_stem}_thumb{file_suffix}"
        thumbnail_path = thumbs_dir / thumbnail_filename

        deleted_files = []

        # 删除原图文件
        if file_path.exists():
            file_path.unlink()
            deleted_files.append(filename)
            print(f"删除礼包图片文件: {filename}")

        # 删除缩略图文件
        if thumbnail_path.exists():
            thumbnail_path.unlink()
            deleted_files.append(thumbnail_filename)
            print(f"删除礼包缩略图文件: {thumbnail_filename}")

        if deleted_files:
            print(f"成功删除礼包图片文件: {deleted_files}")

        return True

    except Exception as e:
        print(f"删除礼包图片文件失败: {e}")
        return False


def generate_gift_code_hash(gift_id: int, add_timestamp: bool = False) -> str:
    """为礼包生成唯一哈希编码（与物品API命名方式一致）"""
    import hashlib
    import time

    # 构建哈希输入，基于礼包ID
    hash_input = f"gift_{gift_id}"

    # 如果需要，添加时间戳以增加唯一性
    if add_timestamp:
        timestamp = str(int(time.time() * 1000))  # 毫秒级时间戳
        hash_input = f"{hash_input}_{timestamp}"

    # 使用SHA256生成哈希
    hash_object = hashlib.sha256(hash_input.encode('utf-8'))
    hash_hex = hash_object.hexdigest()

    # 取前16位作为短哈希，并添加前缀（与物品API保持一致的格式）
    short_hash = hash_hex[:16]
    return f"gift_{short_hash}"


def is_valid_image_file(filename: str) -> bool:
    """验证文件是否为有效的图片格式"""
    valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
    return Path(filename).suffix.lower() in valid_extensions


def validate_filename(filename: str) -> bool:
    """验证文件名是否安全（防止路径遍历攻击）"""
    if not filename:
        return False

    # 检查是否包含危险字符
    dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in dangerous_chars:
        if char in filename:
            return False

    # 检查文件名长度
    if len(filename) > 255:
        return False

    return True


async def validate_file_content(file: UploadFile) -> bool:
    """验证上传的文件内容是否为有效图片"""
    try:
        # 读取文件头部分来验证
        content = await file.read(1024)  # 读取前1KB
        await file.seek(0)  # 重置文件指针

        # 检查常见图片格式的文件头
        if content.startswith(b'\xff\xd8\xff'):  # JPEG
            return True
        elif content.startswith(b'\x89PNG\r\n\x1a\n'):  # PNG
            return True
        elif content.startswith(b'GIF87a') or content.startswith(b'GIF89a'):  # GIF
            return True
        elif content.startswith(b'RIFF') and b'WEBP' in content[:12]:  # WebP
            return True
        elif content.startswith(b'BM'):  # BMP
            return True

        return False
    except Exception:
        return False


def generate_unique_gift_filename(gift_id: int, original_filename: str, check_conflicts: bool = True) -> str:
    """根据礼包ID生成文件名，确保唯一性（与物品API命名方式一致）"""
    # 获取文件扩展名
    file_extension = Path(original_filename).suffix.lower()

    # 生成唯一哈希编码
    safe_code = generate_gift_code_hash(gift_id)

    # 生成基础文件名
    base_filename = f"{safe_code}{file_extension}"

    # 如果不需要检查冲突，直接返回
    if not check_conflicts:
        return base_filename

    # 检查文件是否已存在，如果存在则添加时间戳
    imgs_dir, thumbs_dir = get_upload_directory()
    file_path = imgs_dir / base_filename

    if file_path.exists():
        # 添加时间戳以避免冲突
        safe_code = generate_gift_code_hash(gift_id, add_timestamp=True)
        base_filename = f"{safe_code}{file_extension}"

    return base_filename


def generate_gift_thumbnail_filename(gift_id: int, original_filename: str, check_conflicts: bool = True) -> str:
    """根据礼包ID生成缩略图文件名，确保唯一性（与物品API命名方式一致）"""
    # 获取文件扩展名
    file_extension = Path(original_filename).suffix.lower()

    # 生成唯一哈希编码
    safe_code = generate_gift_code_hash(gift_id)

    # 生成基础文件名（缩略图添加-thumb后缀）
    base_filename = f"{safe_code}-thumb{file_extension}"

    # 如果不需要检查冲突，直接返回
    if not check_conflicts:
        return base_filename

    # 检查文件是否已存在，如果存在则添加时间戳
    imgs_dir, thumbs_dir = get_upload_directory()
    file_path = thumbs_dir / base_filename

    if file_path.exists():
        # 添加时间戳以避免冲突
        safe_code = generate_gift_code_hash(gift_id, add_timestamp=True)
        base_filename = f"{safe_code}-thumb{file_extension}"

    return base_filename


def rename_gift_image_files(gift_id: int, current_image_url: Optional[str]) -> Optional[str]:
    """
    当礼包信息更改时，重命名相关的图片文件（与物品API命名方式一致）

    Args:
        gift_id: 礼包ID
        current_image_url: 当前的图片URL

    Returns:
        新的图片URL，如果没有图片则返回None
    """
    if not current_image_url:
        return None

    try:
        imgs_dir, thumbs_dir = get_upload_directory()

        # 从当前URL提取文件名
        url_path = current_image_url.replace('/static/images/gifts/imgs/', '').replace('/static/images/gifts/', '').replace('/static/images/', '')
        current_filename = Path(url_path).name
        if not current_filename:
            return current_image_url

        # 获取文件扩展名
        file_extension = Path(current_filename).suffix.lower()
        if not file_extension:
            print(f"警告: 无法确定文件扩展名: {current_filename}")
            return current_image_url

        # 使用与上传时相同的逻辑生成新文件名
        temp_original_filename = f"image{file_extension}"
        new_filename = generate_unique_gift_filename(gift_id, temp_original_filename, check_conflicts=False)
        new_thumbnail_filename = generate_gift_thumbnail_filename(gift_id, temp_original_filename, check_conflicts=False)

        # 构建文件路径
        old_file_path = imgs_dir / current_filename
        new_file_path = imgs_dir / new_filename

        # 生成缩略图文件名
        old_file_stem = Path(current_filename).stem
        old_file_suffix = Path(current_filename).suffix
        old_thumbnail_filename = f"{old_file_stem}-thumb{old_file_suffix}"
        old_thumbnail_path = thumbs_dir / old_thumbnail_filename
        new_thumbnail_path = thumbs_dir / new_thumbnail_filename

        # 检查新文件名是否与当前文件名相同
        if current_filename == new_filename:
            print(f"文件名未改变，无需重命名: {current_filename}")
            return current_image_url

        # 重命名原图文件
        renamed_original = False
        if old_file_path.exists():
            if new_file_path.exists():
                # 如果新文件名已存在，添加时间戳避免冲突
                import time
                timestamp = str(int(time.time() * 1000))
                new_filename = generate_unique_gift_filename(gift_id, f"image_{timestamp}{file_extension}", check_conflicts=False)
                new_file_path = imgs_dir / new_filename
                new_thumbnail_filename = generate_gift_thumbnail_filename(gift_id, f"image_{timestamp}{file_extension}", check_conflicts=False)
                new_thumbnail_path = thumbs_dir / new_thumbnail_filename

            # 执行重命名
            old_file_path.rename(new_file_path)
            renamed_original = True
            print(f"重命名礼包图片文件: {current_filename} -> {new_filename}")
        else:
            print(f"警告: 原图文件不存在: {old_file_path}")

        # 重命名缩略图文件
        if old_thumbnail_path.exists():
            if new_thumbnail_path.exists():
                # 如果新缩略图已存在，删除旧缩略图
                old_thumbnail_path.unlink()
                print(f"删除旧缩略图文件: {old_thumbnail_filename}")
            else:
                # 重命名缩略图
                old_thumbnail_path.rename(new_thumbnail_path)
                print(f"重命名礼包缩略图文件: {old_thumbnail_filename} -> {new_thumbnail_filename}")
        else:
            print(f"警告: 缩略图文件不存在: {old_thumbnail_path}")

        # 只有在原图成功重命名时才返回新URL
        if renamed_original:
            return f"/static/images/gifts/imgs/{new_filename}"
        else:
            print(f"警告: 原图文件不存在: {current_filename}")
            return current_image_url

    except Exception as e:
        print(f"重命名礼包图片文件失败: {e}")
        # 如果重命名失败，返回原URL
        return current_image_url


# Pydantic 模型
class GiftItem(BaseModel):
    """礼包物品模型"""
    command: str = Field(..., description="游戏命令")
    item: str = Field(..., description="物品代码")
    amount: int = Field(..., ge=1, description="数量")


class GiftPackageCreate(BaseModel):
    """礼包创建模型"""
    name: str = Field(..., min_length=1, max_length=100, description="礼包名称")
    description: Optional[str] = Field(None, max_length=500, description="礼包描述")
    gift_type: str = Field(..., description="礼包类型 (one_time/daily/limited_quantity/limited_time/limited_time_quantity)")
    items_config: Union[Dict[str, int], List[GiftItem]] = Field(..., description="物品配置 - 支持字典格式{物品代码: 数量}或数组格式[{command, item, amount}]")
    image_url: Optional[str] = Field(None, max_length=500, description="礼包图片URL")
    is_active: bool = Field(True, description="是否启用")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    max_claims: int = Field(1, description="最大领取次数 (-1为无限制)")
    cooldown_hours: int = Field(24, description="冷却时间(小时)")
    required_level: int = Field(0, description="所需等级")
    total_quantity: Optional[int] = Field(None, description="全服总数量 (null表示无限制，用于限量礼包)")
    claimed_quantity: int = Field(0, description="已领取数量 (系统自动维护)")


class GiftPackageUpdate(BaseModel):
    """礼包更新模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="礼包名称")
    description: Optional[str] = Field(None, max_length=500, description="礼包描述")
    items_config: Optional[Union[Dict[str, int], List[GiftItem]]] = Field(None, description="物品配置 - 支持字典格式{物品代码: 数量}或数组格式[{command, item, amount}]")
    image_url: Optional[str] = Field(None, max_length=500, description="礼包图片URL")
    is_active: Optional[bool] = Field(None, description="是否启用")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    max_claims: Optional[int] = Field(None, description="最大领取次数")
    cooldown_hours: Optional[int] = Field(None, description="冷却时间(小时)")
    required_level: Optional[int] = Field(None, description="所需等级")
    total_quantity: Optional[int] = Field(None, description="全服总数量 (null表示无限制)")
    claimed_quantity: Optional[int] = Field(None, description="已领取数量 (通常不允许手动修改)")


# API 路由
@router.get("/available", response_model=dict, summary="获取可领取礼包")
async def get_available_gifts(
    category: Optional[str] = Query(None, description="礼包分类过滤 (general/vip_daily/vip_level/paid_daily)"),
    current_user: dict = Depends(jwt_bearer)
):
    """
    获取当前用户可领取的礼包列表

    - **category**: 可选，过滤特定分类的礼包
    """
    from ..main import get_global_db_manager

    db_manager = get_global_db_manager()
    
    with db_manager.get_db_session() as db:
        gift_service = GiftService(db)
        result = gift_service.get_available_gifts(current_user["user_id"])
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error.message
            )

        # 如果指定了分类过滤，则过滤结果
        gifts = result.data["gifts"]
        if category:
            gifts = [gift for gift in gifts if gift.get("category") == category]

        return {
            "success": True,
            "message": result.message,
            "data": {"gifts": gifts}
        }


@router.post("/{gift_id}/claim", response_model=dict, summary="领取礼包")
async def claim_gift(
    gift_id: int,
    current_user: dict = Depends(jwt_bearer)
):
    """
    领取指定的礼包
    
    - **gift_id**: 礼包ID
    """
    from ..main import get_global_db_manager

    db_manager = get_global_db_manager()
    
    with db_manager.get_db_session() as db:
        gift_service = GiftService(db)
        result = gift_service.claim_gift(current_user["user_id"], gift_id)
        
        if not result.success:
            if result.error.error_type == ServiceErrorType.NOT_FOUND:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=result.error.message
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.error.message
                )
        
        return {
            "success": True,
            "message": result.message,
            "data": result.data
        }


@router.get("/history", response_model=dict, summary="获取领取历史")
async def get_gift_history(
    limit: int = Query(50, ge=1, le=100, description="限制数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: dict = Depends(jwt_bearer)
):
    """
    获取当前用户的礼包领取历史
    
    - **limit**: 限制数量 (1-100)
    - **offset**: 偏移量
    """
    from ..main import get_global_db_manager

    db_manager = get_global_db_manager()
    
    with db_manager.get_db_session() as db:
        gift_service = GiftService(db)
        result = gift_service.get_user_gift_history(
            current_user["user_id"], limit, offset
        )
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error.message
            )
        
        return {
            "success": True,
            "message": result.message,
            "data": result.data
        }


# 管理员接口
@router.post("/", response_model=dict, summary="创建礼包")
async def create_gift_package(
    gift_data: GiftPackageCreate,
    current_user: dict = Depends(require_admin)
):
    """
    创建新的礼包 (需要管理员权限)
    
    - **name**: 礼包名称
    - **description**: 礼包描述
    - **gift_type**: 礼包类型
    - **items_config**: 物品配置
    - **其他配置**: 时间限制、领取限制等
    """
    from ..main import get_global_db_manager

    db_manager = get_global_db_manager()
    
    # 验证礼包类型
    try:
        gift_type_enum = GiftType(gift_data.gift_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的礼包类型"
        )
    
    # 标准化items_config为数组格式
    try:
        normalized_items = normalize_items_config(gift_data.items_config)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"物品配置格式错误: {str(e)}"
        )

    with db_manager.get_db_session() as db:
        gift_service = GiftService(db)
        result = gift_service.create_gift_package(
            name=gift_data.name,
            description=gift_data.description or "",
            gift_type=gift_type_enum,
            items_config={"items": normalized_items},  # 包装为字典格式
            image_url=gift_data.image_url,
            is_active=gift_data.is_active,
            start_time=gift_data.start_time,
            end_time=gift_data.end_time,
            max_claims=gift_data.max_claims,
            cooldown_hours=gift_data.cooldown_hours,
            required_level=gift_data.required_level,
            total_quantity=gift_data.total_quantity,
            claimed_quantity=gift_data.claimed_quantity
        )
        
        if not result.success:
            if result.error.error_type == ServiceErrorType.DUPLICATE_ENTRY:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=result.error.message
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.error.message
                )
        
        return {
            "success": True,
            "message": result.message,
            "data": result.data
        }


@router.get("/admin/all", response_model=dict, summary="获取所有礼包")
async def get_all_gift_packages(
    current_user: dict = Depends(require_admin)
):
    """
    获取所有礼包列表 (需要管理员权限)
    """
    from ..main import get_global_db_manager

    db_manager = get_global_db_manager()
    
    with db_manager.get_db_session() as db:
        from ...modules.sql.models import GiftPackage
        
        try:
            gifts = db.query(GiftPackage).all()
            
            gift_list = []
            for gift in gifts:
                import json
                gift_data = {
                    "id": gift.id,
                    "name": gift.name,
                    "description": gift.description,
                    "gift_type": gift.gift_type.value,
                    "items_config": json.loads(gift.items_config),
                    "image_url": gift.image_url,
                    "is_active": gift.is_active,
                    "start_time": gift.start_time.isoformat() if gift.start_time else None,
                    "end_time": gift.end_time.isoformat() if gift.end_time else None,
                    "max_claims": gift.max_claims,
                    "cooldown_hours": gift.cooldown_hours,
                    "required_level": gift.required_level,
                    "total_quantity": gift.total_quantity,
                    "claimed_quantity": gift.claimed_quantity,
                    "remaining_quantity": gift.total_quantity - gift.claimed_quantity if gift.total_quantity is not None else None,
                    "created_at": gift.created_at.isoformat()
                }
                gift_list.append(gift_data)
            
            return {
                "success": True,
                "message": "获取礼包列表成功",
                "data": {"gifts": gift_list}
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取礼包列表失败: {str(e)}"
            )


@router.get("/{gift_id}", response_model=dict, summary="获取礼包配置")
async def get_gift_package(
    gift_id: int,
    current_user: dict = Depends(require_admin)
):
    """
    获取指定礼包的详细配置信息（仅管理员）

    - 管理员：可以查看所有礼包的详细配置
    """
    try:
        from ..main import get_global_db_manager
        db_manager = get_global_db_manager()

        with db_manager.get_db_session() as db:
            from ...modules.sql.models import GiftPackage

            # 管理员可以查看所有礼包
            gift = db.query(GiftPackage).filter(GiftPackage.id == gift_id).first()

            if not gift:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"礼包ID {gift_id} 不存在或无权访问"
                )

            # 构建响应数据
            gift_data = {
                "id": gift.id,
                "name": gift.name,
                "description": gift.description,
                "gift_type": gift.gift_type.value,
                "items_config": json.loads(gift.items_config),
                "image_url": gift.image_url,
                "is_active": gift.is_active,
                "start_time": gift.start_time.isoformat() if gift.start_time else None,
                "end_time": gift.end_time.isoformat() if gift.end_time else None,
                "max_claims": gift.max_claims,
                "cooldown_hours": gift.cooldown_hours,
                "required_level": gift.required_level,
                "total_quantity": gift.total_quantity,
                "claimed_quantity": gift.claimed_quantity,
                "remaining_quantity": gift.total_quantity - gift.claimed_quantity if gift.total_quantity is not None else None,
                "created_at": gift.created_at.isoformat(),
                "updated_at": gift.updated_at.isoformat()
            }

            return {
                "success": True,
                "message": "获取礼包配置成功",
                "data": gift_data
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取礼包配置失败: {str(e)}"
        )


@router.put("/{gift_id}", response_model=dict, summary="更新礼包")
async def update_gift_package(
    gift_id: int,
    gift_data: GiftPackageUpdate,
    current_user: dict = Depends(require_admin)
):
    """
    更新指定礼包 (需要管理员权限)
    """
    from ..main import get_global_db_manager

    db_manager = get_global_db_manager()
    
    with db_manager.get_db_session() as db:
        from ...modules.sql.models import GiftPackage
        import json
        
        try:
            gift = db.query(GiftPackage).filter(GiftPackage.id == gift_id).first()
            if not gift:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="礼包不存在"
                )
            
            # 记录原始名称和图片URL，用于重命名逻辑
            old_gift_name = gift.name
            current_image_url = gift.image_url
            name_changed = gift_data.name is not None and gift_data.name != old_gift_name

            # 更新字段
            if gift_data.name is not None:
                gift.name = gift_data.name
            if gift_data.description is not None:
                gift.description = gift_data.description
            if gift_data.items_config is not None:
                # 标准化items_config为数组格式
                try:
                    normalized_items = normalize_items_config(gift_data.items_config)
                    gift.items_config = json.dumps({"items": normalized_items}, ensure_ascii=False)
                except ValueError as e:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"物品配置格式错误: {str(e)}"
                    )
            if gift_data.image_url is not None:
                gift.image_url = gift_data.image_url
            if gift_data.is_active is not None:
                gift.is_active = gift_data.is_active
            if gift_data.start_time is not None:
                gift.start_time = gift_data.start_time
            if gift_data.end_time is not None:
                gift.end_time = gift_data.end_time
            if gift_data.max_claims is not None:
                gift.max_claims = gift_data.max_claims
            if gift_data.cooldown_hours is not None:
                gift.cooldown_hours = gift_data.cooldown_hours
            if gift_data.required_level is not None:
                gift.required_level = gift_data.required_level
            if gift_data.total_quantity is not None:
                gift.total_quantity = gift_data.total_quantity
            if gift_data.claimed_quantity is not None:
                gift.claimed_quantity = gift_data.claimed_quantity

            # 如果有图片，重新生成图片文件名（与物品API保持一致的命名方式）
            if current_image_url:
                try:
                    new_image_url = rename_gift_image_files(gift_id, current_image_url)
                    if new_image_url and new_image_url != current_image_url:
                        # 更新图片URL
                        gift.image_url = new_image_url
                        print(f"礼包图片URL已更新为统一格式: {current_image_url} -> {new_image_url}")
                except Exception as e:
                    print(f"重命名礼包图片文件失败: {e}")
                    # 重命名失败不影响礼包更新，继续执行

            gift.update_timestamp()
            db.commit()
            
            return {
                "success": True,
                "message": "礼包更新成功",
                "data": {"gift_id": gift_id}
            }
            
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"更新礼包失败: {str(e)}"
            )


@router.delete("/{gift_id}", response_model=dict, summary="删除礼包")
async def delete_gift_package(
    gift_id: int,
    current_user: dict = Depends(require_admin)
):
    """
    删除指定礼包 (需要管理员权限)
    """
    from ..main import get_global_db_manager

    db_manager = get_global_db_manager()
    
    with db_manager.get_db_session() as db:
        from ...modules.sql.models import GiftPackage
        
        try:
            gift = db.query(GiftPackage).filter(GiftPackage.id == gift_id).first()
            if not gift:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="礼包不存在"
                )

            # 在删除礼包之前先删除相关的图片文件
            if gift.image_url:
                delete_gift_image_files(gift.image_url)

            db.delete(gift)
            db.commit()

            return {
                "success": True,
                "message": "礼包删除成功",
                "data": {"gift_id": gift_id}
            }
            
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"删除礼包失败: {str(e)}"
            )


# 图片上传API
@router.post("/{gift_id}/upload-image", response_model=dict, summary="上传礼包图片")
async def upload_gift_image(
    gift_id: int,
    file: UploadFile = File(..., description="要上传的图片文件"),
    current_user: dict = Depends(require_admin)
):
    """为指定礼包上传图片"""
    try:
        # 验证文件名
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="未提供文件名"
            )

        if not validate_filename(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件名包含非法字符或过长"
            )

        if not is_valid_image_file(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不支持的文件格式，请上传 JPG、PNG、GIF、WebP 或 BMP 格式的图片"
            )

        # 验证文件内容
        if not await validate_file_content(file):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件内容不是有效的图片格式"
            )

        # 验证文件大小（5MB限制）
        if file.size and file.size > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件大小不能超过5MB"
            )

        # 验证礼包是否存在
        from ..main import get_global_db_manager
        db_manager = get_global_db_manager()

        with db_manager.get_db_session() as db:
            from ...modules.sql.models import GiftPackage

            gift = db.query(GiftPackage).filter(GiftPackage.id == gift_id).first()
            if not gift:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"礼包ID {gift_id} 不存在"
                )

            # 生成唯一文件名并保存文件（包括缩略图）
            filename = generate_unique_gift_filename(gift_id, file.filename, check_conflicts=True)
            thumbnail_filename = generate_gift_thumbnail_filename(gift_id, file.filename, check_conflicts=True)

            try:
                image_url, thumbnail_url = await save_gift_image_with_thumbnail(file, filename, thumbnail_filename)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

            # 更新数据库中的图片路径
            try:
                gift.image_url = image_url
                db.commit()
            except Exception as e:
                # 如果数据库更新失败，删除已上传的文件
                try:
                    imgs_dir, thumbs_dir = get_upload_directory()
                    file_path = imgs_dir / filename
                    thumbnail_path = thumbs_dir / thumbnail_filename
                    if file_path.exists():
                        file_path.unlink()
                    if thumbnail_path.exists():
                        thumbnail_path.unlink()
                except:
                    pass
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"数据库更新失败: {str(e)}"
                )

            return {
                "success": True,
                "message": "礼包图片上传成功",
                "data": {
                    "gift_id": gift_id,
                    "filename": filename,
                    "thumbnail_filename": thumbnail_filename,
                    "image_url": image_url,
                    "thumbnail_url": thumbnail_url,
                    "file_size": file.size
                }
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"上传图片失败: {str(e)}"
        )


# VIP专用端点
@router.get("/vip/daily", response_model=dict, summary="获取VIP每日礼包")
async def get_vip_daily_gifts(current_user: dict = Depends(jwt_bearer)):
    """
    获取当前用户VIP等级对应的每日礼包
    """
    from ..main import get_global_db_manager

    db_manager = get_global_db_manager()

    with db_manager.get_db_session() as db:
        gift_service = GiftService(db)
        result = gift_service.get_available_gifts(current_user["user_id"])

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error.message
            )

        # 过滤VIP每日礼包
        vip_daily_gifts = [gift for gift in result.data["gifts"] if gift.get("category") == "vip_daily"]

        return {
            "success": True,
            "message": "获取VIP每日礼包成功",
            "data": {"gifts": vip_daily_gifts}
        }


@router.get("/vip/level", response_model=dict, summary="获取VIP等级礼包")
async def get_vip_level_gifts(current_user: dict = Depends(jwt_bearer)):
    """
    获取当前用户可领取的VIP等级礼包
    """
    from ..main import get_global_db_manager

    db_manager = get_global_db_manager()

    with db_manager.get_db_session() as db:
        gift_service = GiftService(db)
        result = gift_service.get_available_gifts(current_user["user_id"])

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error.message
            )

        # 过滤VIP等级礼包
        vip_level_gifts = [gift for gift in result.data["gifts"] if gift.get("category") == "vip_level"]

        return {
            "success": True,
            "message": "获取VIP等级礼包成功",
            "data": {"gifts": vip_level_gifts}
        }
