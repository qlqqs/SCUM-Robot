"""
SCUM Robot API 路由 - 将 robot 模块功能封装为 FastAPI 端点

作者: GitHub Copilot
日期: 2025年9月18日
版本: 1.0
"""

from typing import Optional, List, Union, Tuple, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from enum import Enum
import sys
import os

# 导入JWT认证依赖
from ...modules.auth.jwt_handler import jwt_bearer, require_admin, require_super_admin
from ...modules.sql.models.user_models import User

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# 导入 robot 模块
from bakend.modules.robot import (
    InstructionSet, 
    CommandSender, 
    CurrencyType as RobotCurrencyType, 
    ModifierType as RobotModifierType,
    create_robot,
    create_command_sender
)

# 创建路由器
router = APIRouter()

# ===== Pydantic 枚举模型 =====

class CurrencyType(str, Enum):
    """货币类型"""
    NORMAL = "Normal"
    GOLD = "Gold"

class ModifierType(str, Enum):
    """载具修改器类型"""
    FULL = "Full"
    WHEELS_ONLY = "WheelsOnly"
    MINIMAL_FUNCTIONAL = "MinimalFunctional"

# ===== 请求模型 =====

class CurrencyChangeRequest(BaseModel):
    """货币变更请求"""
    amount: int = Field(..., description="货币数量（正数增加，负数扣除）")
    player_identifier: str = Field(..., min_length=1, description="玩家名字或SteamID")
    currency_type: CurrencyType = Field(CurrencyType.NORMAL, description="货币类型")
    execute: bool = Field(False, description="是否直接执行命令")

class CurrencySetRequest(BaseModel):
    """货币设置请求"""
    amount: int = Field(..., ge=0, description="货币数量")
    player_identifier: str = Field(..., min_length=1, description="玩家名字或SteamID")
    currency_type: CurrencyType = Field(CurrencyType.NORMAL, description="货币类型")
    execute: bool = Field(False, description="是否直接执行命令")

class CurrencyChangeAllRequest(BaseModel):
    """所有玩家货币变更请求"""
    amount: int = Field(..., description="货币数量（正数增加，负数扣除）")
    currency_type: CurrencyType = Field(CurrencyType.NORMAL, description="货币类型")
    execute: bool = Field(False, description="是否直接执行命令")

class FameChangeRequest(BaseModel):
    """声望变更请求"""
    amount: int = Field(..., description="声望数量（正数增加，负数扣除）")
    player_identifier: str = Field(..., min_length=1, description="玩家名字或SteamID")
    execute: bool = Field(False, description="是否直接执行命令")

class AnnounceRequest(BaseModel):
    """公告请求"""
    message: str = Field(..., min_length=1, description="公告内容")
    execute: bool = Field(False, description="是否直接执行命令")

class TeleportCoordinatesRequest(BaseModel):
    """坐标传送请求"""
    x: float = Field(..., description="X坐标")
    y: float = Field(..., description="Y坐标")
    z: float = Field(..., description="Z坐标")
    player_identifier: Optional[str] = Field(None, description="玩家名字或SteamID（为空则传送自己）")
    execute: bool = Field(False, description="是否直接执行命令")

class TeleportPlayerRequest(BaseModel):
    """玩家传送请求"""
    target_player: str = Field(..., min_length=1, description="目标玩家名字或SteamID")
    source_player: Optional[str] = Field(None, description="源玩家名字或SteamID（为空则传送自己）")
    execute: bool = Field(False, description="是否直接执行命令")

class SpawnItemRequest(BaseModel):
    """物品生成请求"""
    item_name: str = Field(..., min_length=1, description="物品名称")
    quantity: int = Field(1, ge=1, description="数量")
    location: Optional[str] = Field(None, description="生成位置（玩家名或坐标）")
    ammo_count: Optional[int] = Field(None, ge=0, description="弹药数量（适用于武器）")
    execute: bool = Field(False, description="是否直接执行命令")

class SpawnAnimalRequest(BaseModel):
    """动物生成请求"""
    animal_type: str = Field(..., min_length=1, description="动物类型")
    quantity: int = Field(1, ge=1, description="数量")
    location: Optional[str] = Field(None, description="生成位置（玩家名或坐标）")
    execute: bool = Field(False, description="是否直接执行命令")

class SpawnZombieRequest(BaseModel):
    """僵尸生成请求"""
    zombie_type: str = Field(..., min_length=1, description="僵尸类型")
    quantity: int = Field(1, ge=1, description="数量")
    location: Optional[str] = Field(None, description="生成位置（玩家名或坐标）")
    execute: bool = Field(False, description="是否直接执行命令")

class SpawnVehicleRequest(BaseModel):
    """载具生成请求"""
    vehicle_type: str = Field(..., min_length=1, description="载具类型")
    quantity: int = Field(1, ge=1, description="数量")
    location: Optional[str] = Field(None, description="生成位置（玩家名或坐标）")
    modifier: Optional[ModifierType] = Field(None, description="载具修改器")
    execute: bool = Field(False, description="是否直接执行命令")

class CommandRequest(BaseModel):
    """命令请求"""
    command: str = Field(..., min_length=1, description="要发送的命令")
    window_title: str = Field("SCUM", description="目标窗口标题")
    press_enter: bool = Field(True, description="是否按回车键")

class StarterPackageRequest(BaseModel):
    """新手大礼包请求"""
    player_identifier: str = Field(..., min_length=1, description="玩家名字或SteamID")
    execute: bool = Field(False, description="是否直接执行命令")

# ===== 响应模型 =====

class CommandResponse(BaseModel):
    """命令响应"""
    success: bool = Field(..., description="操作是否成功")
    command: Optional[str] = Field(None, description="生成的命令字符串")
    executed: bool = Field(False, description="是否已执行")
    message: str = Field(..., description="响应消息")

class WindowListResponse(BaseModel):
    """窗口列表响应"""
    windows: List[str] = Field(..., description="可用窗口标题列表")

# ===== 辅助函数 =====

def convert_currency_type(currency_type: CurrencyType) -> RobotCurrencyType:
    """转换货币类型"""
    return RobotCurrencyType.NORMAL if currency_type == CurrencyType.NORMAL else RobotCurrencyType.GOLD

def convert_modifier_type(modifier_type: Optional[ModifierType]) -> Optional[RobotModifierType]:
    """转换修改器类型"""
    if modifier_type is None:
        return None
    mapping = {
        ModifierType.FULL: RobotModifierType.FULL,
        ModifierType.WHEELS_ONLY: RobotModifierType.WHEELS_ONLY,
        ModifierType.MINIMAL_FUNCTIONAL: RobotModifierType.MINIMAL_FUNCTIONAL
    }
    return mapping[modifier_type]

def handle_robot_result(result: Union[str, bool], executed: bool) -> CommandResponse:
    """处理robot模块的返回结果"""
    if executed:
        return CommandResponse(
            success=bool(result),
            command=None,
            executed=True,
            message="命令执行成功" if result else "命令执行失败"
        )
    else:
        return CommandResponse(
            success=True,
            command=str(result),
            executed=False,
            message="命令生成成功"
        )

# ===== API 端点 =====

@router.get("/", summary="Robot API 状态")
async def robot_status(current_user: Dict[str, Any] = Depends(jwt_bearer)):
    """获取 Robot API 状态信息"""
    return {
        "message": "SCUM Robot API 正常运行",
        "version": "1.0.0",
        "features": [
            "玩家管理", "服主功能", "传送功能",
            "生成功能", "预设功能", "命令发送"
        ],
        "user": current_user["username"]
    }

# ===== 玩家管理 =====

@router.post("/player/currency/change", response_model=CommandResponse, summary="改变玩家货币")
async def change_player_currency(request: CurrencyChangeRequest, current_user: Dict[str, Any] = Depends(require_admin)):
    """改变指定玩家的货币余额"""
    try:
        robot = create_robot(enable_sender=request.execute)
        currency_type = convert_currency_type(request.currency_type)
        
        result = robot.change_currency_balance(
            amount=request.amount,
            player_identifier=request.player_identifier,
            currency_type=currency_type,
            execute=request.execute
        )
        
        return handle_robot_result(result, request.execute)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"改变玩家货币失败: {str(e)}"
        )

@router.post("/player/currency/set", response_model=CommandResponse, summary="设置玩家货币")
async def set_player_currency(request: CurrencySetRequest, current_user: Dict[str, Any] = Depends(require_admin)):
    """设置指定玩家的货币余额"""
    try:
        robot = create_robot(enable_sender=request.execute)
        currency_type = convert_currency_type(request.currency_type)
        
        result = robot.set_currency_balance(
            amount=request.amount,
            player_identifier=request.player_identifier,
            currency_type=currency_type,
            execute=request.execute
        )
        
        return handle_robot_result(result, request.execute)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"设置玩家货币失败: {str(e)}"
        )

@router.post("/player/currency/change-all", response_model=CommandResponse, summary="改变所有玩家货币")
async def change_all_players_currency(request: CurrencyChangeAllRequest, current_user: Dict[str, Any] = Depends(require_super_admin)):
    """改变所有玩家的货币余额"""
    try:
        robot = create_robot(enable_sender=request.execute)
        currency_type = convert_currency_type(request.currency_type)
        
        result = robot.change_currency_balance_to_all(
            amount=request.amount,
            currency_type=currency_type,
            execute=request.execute
        )
        
        return handle_robot_result(result, request.execute)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"改变所有玩家货币失败: {str(e)}"
        )

@router.post("/player/fame/change", response_model=CommandResponse, summary="改变玩家声望")
async def change_player_fame(request: FameChangeRequest, current_user: Dict[str, Any] = Depends(require_admin)):
    """改变指定玩家的声望点数"""
    try:
        robot = create_robot(enable_sender=request.execute)

        result = robot.change_fame_points(
            points=request.amount,
            player_identifier=request.player_identifier,
            execute=request.execute
        )

        return handle_robot_result(result, request.execute)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"改变玩家声望失败: {str(e)}"
        )

# 注意：以下玩家管理功能需要在InstructionSet类中实现相应方法
# 目前这些方法在robot模块中不存在，可以作为未来扩展功能

# @router.post("/player/ban", response_model=CommandResponse, summary="封禁玩家")
# @router.post("/player/unban", response_model=CommandResponse, summary="解封玩家")
# @router.post("/player/mute", response_model=CommandResponse, summary="禁言玩家")
# @router.post("/player/unmute", response_model=CommandResponse, summary="解除禁言")

# ===== 服主功能 =====

@router.post("/admin/announce", response_model=CommandResponse, summary="发送公告")
async def send_announcement(request: AnnounceRequest, current_user: Dict[str, Any] = Depends(require_super_admin)):
    """向所有玩家发送公告"""
    try:
        robot = create_robot(enable_sender=request.execute)

        result = robot.announce(
            message=request.message,
            execute=request.execute
        )

        return handle_robot_result(result, request.execute)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发送公告失败: {str(e)}"
        )

# ===== 传送功能 =====

@router.post("/teleport/coordinates", response_model=CommandResponse, summary="传送到坐标")
async def teleport_to_coordinates(request: TeleportCoordinatesRequest, current_user: Dict[str, Any] = Depends(require_admin)):
    """传送到指定坐标"""
    try:
        robot = create_robot(enable_sender=request.execute)

        result = robot.teleport_to_coordinates(
            x=request.x,
            y=request.y,
            z=request.z,
            player_identifier=request.player_identifier,
            execute=request.execute
        )

        return handle_robot_result(result, request.execute)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"传送到坐标失败: {str(e)}"
        )

@router.post("/teleport/player", response_model=CommandResponse, summary="传送到玩家")
async def teleport_to_player(request: TeleportPlayerRequest, current_user: Dict[str, Any] = Depends(require_admin)):
    """传送到指定玩家位置"""
    try:
        robot = create_robot(enable_sender=request.execute)

        result = robot.teleport_to_player(
            target_player=request.target_player,
            source_player=request.source_player,
            execute=request.execute
        )

        return handle_robot_result(result, request.execute)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"传送到玩家失败: {str(e)}"
        )

@router.post("/teleport/to-me", response_model=CommandResponse, summary="传送玩家到我")
async def teleport_player_to_me(request: TeleportPlayerRequest, current_user: Dict[str, Any] = Depends(require_admin)):
    """传送指定玩家到我的位置"""
    try:
        robot = create_robot(enable_sender=request.execute)

        result = robot.teleport_to_me(
            player_identifier=request.target_player,
            execute=request.execute
        )

        return handle_robot_result(result, request.execute)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"传送玩家到我失败: {str(e)}"
        )

@router.post("/teleport/random", response_model=CommandResponse, summary="随机传送")
async def teleport_random(request: TeleportPlayerRequest, current_user: Dict[str, Any] = Depends(require_admin)):
    """随机传送玩家"""
    try:
        robot = create_robot(enable_sender=request.execute)

        result = robot.teleport_random(
            player_identifier=request.target_player,
            execute=request.execute
        )

        return handle_robot_result(result, request.execute)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"随机传送失败: {str(e)}"
        )

# ===== 生成功能 =====

@router.post("/spawn/item", response_model=CommandResponse, summary="生成物品")
async def spawn_item(request: SpawnItemRequest, current_user: Dict[str, Any] = Depends(require_admin)):
    """生成指定物品"""
    try:
        robot = create_robot(enable_sender=request.execute)

        result = robot.spawn_item(
            item_name=request.item_name,
            quantity=request.quantity,
            location=request.location,
            ammo_count=request.ammo_count,
            execute=request.execute
        )

        return handle_robot_result(result, request.execute)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成物品失败: {str(e)}"
        )

@router.post("/spawn/animal", response_model=CommandResponse, summary="生成动物")
async def spawn_animal(request: SpawnAnimalRequest, current_user: Dict[str, Any] = Depends(require_admin)):
    """生成指定动物"""
    try:
        robot = create_robot(enable_sender=request.execute)

        result = robot.spawn_animal(
            animal_type=request.animal_type,
            quantity=request.quantity,
            location=request.location,
            execute=request.execute
        )

        return handle_robot_result(result, request.execute)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成动物失败: {str(e)}"
        )

@router.post("/spawn/zombie", response_model=CommandResponse, summary="生成僵尸")
async def spawn_zombie(request: SpawnZombieRequest, current_user: Dict[str, Any] = Depends(require_admin)):
    """生成指定僵尸"""
    try:
        robot = create_robot(enable_sender=request.execute)

        result = robot.spawn_zombie(
            zombie_type=request.zombie_type,
            quantity=request.quantity,
            location=request.location,
            execute=request.execute
        )

        return handle_robot_result(result, request.execute)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成僵尸失败: {str(e)}"
        )

@router.post("/spawn/vehicle", response_model=CommandResponse, summary="生成载具")
async def spawn_vehicle(request: SpawnVehicleRequest, current_user: Dict[str, Any] = Depends(require_admin)):
    """生成指定载具"""
    try:
        robot = create_robot(enable_sender=request.execute)
        modifier = convert_modifier_type(request.modifier)

        result = robot.spawn_vehicle(
            vehicle_type=request.vehicle_type,
            quantity=request.quantity,
            location=request.location,
            modifier=modifier,
            execute=request.execute
        )

        return handle_robot_result(result, request.execute)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成载具失败: {str(e)}"
        )

# ===== 预设功能 =====

@router.post("/preset/starter-package", response_model=CommandResponse, summary="新手大礼包")
async def give_starter_package(request: StarterPackageRequest, current_user: Dict[str, Any] = Depends(require_admin)):
    """给玩家发放新手大礼包"""
    try:
        robot = create_robot(enable_sender=request.execute)

        result = robot.give_starter_package(
            player_identifier=request.player_identifier,
            execute=request.execute
        )

        if request.execute:
            return CommandResponse(
                success=bool(result),
                command=None,
                executed=True,
                message="新手大礼包发放成功" if result else "新手大礼包发放失败"
            )
        else:
            # 返回命令列表
            commands = result if isinstance(result, list) else [str(result)]
            return CommandResponse(
                success=True,
                command="; ".join(commands),
                executed=False,
                message=f"生成了 {len(commands)} 个命令"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发放新手大礼包失败: {str(e)}"
        )

# ===== 命令发送功能 =====

@router.post("/command/send", response_model=CommandResponse, summary="发送自定义命令")
async def send_custom_command(request: CommandRequest, current_user: Dict[str, Any] = Depends(require_super_admin)):
    """发送自定义命令到指定窗口"""
    try:
        sender = create_command_sender()

        result = sender.send_command(
            window_title=request.window_title,
            command=request.command,
            press_enter=request.press_enter
        )

        return CommandResponse(
            success=result,
            command=request.command,
            executed=True,
            message="命令发送成功" if result else "命令发送失败"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发送命令失败: {str(e)}"
        )

class ScumCommandRequest(BaseModel):
    """SCUM命令请求"""
    command: str = Field(..., min_length=1, description="要发送的SCUM命令")

@router.post("/command/scum", response_model=CommandResponse, summary="发送SCUM游戏命令")
async def send_scum_command(request: ScumCommandRequest, current_user: Dict[str, Any] = Depends(require_super_admin)):
    """发送命令到SCUM游戏窗口"""
    try:
        sender = create_command_sender()

        result = sender.send_scum_command(request.command)

        return CommandResponse(
            success=result,
            command=request.command,
            executed=True,
            message="SCUM命令发送成功" if result else "SCUM命令发送失败"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发送SCUM命令失败: {str(e)}"
        )

@router.get("/command/windows", response_model=WindowListResponse, summary="获取可用窗口列表")
async def get_available_windows(current_user: Dict[str, Any] = Depends(require_super_admin)):
    """获取当前系统中所有可用的窗口标题列表"""
    try:
        sender = create_command_sender()
        windows = sender.get_all_window_titles()

        return WindowListResponse(windows=windows)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取窗口列表失败: {str(e)}"
        )

# ===== 工具功能 =====


