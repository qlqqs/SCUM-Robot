"""
数据库初始化数据脚本
"""

import json
import os
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models import (
    User, UserAssets, GiftPackage, AdminPermission, UserGiftRecord, VIPConfig,
    UserType, GiftType
)
from ..services.user_service import UserService


BOOTSTRAP_PASSWORD_PLACEHOLDERS = {
    "change-me",
    "please-change-me",
    "replace-me",
    "replace-with-a-strong-password",
    "set-a-strong-password",
    "your-strong-admin-password",
    "bootstrap-admin-password",
}


def is_placeholder_bootstrap_password(password: Optional[str]) -> bool:
    """判断管理员初始密码是否缺失或仍为占位值。"""
    normalized = (password or "").strip().lower()
    return not normalized or normalized in BOOTSTRAP_PASSWORD_PLACEHOLDERS


def get_bootstrap_admin_settings() -> dict:
    """从环境变量读取首次初始化管理员配置。"""
    username = (os.getenv("BOOTSTRAP_ADMIN_USERNAME") or "superadmin").strip() or "superadmin"
    password = (os.getenv("BOOTSTRAP_ADMIN_PASSWORD") or "").strip()

    if is_placeholder_bootstrap_password(password):
        raise RuntimeError(
            "数据库首次初始化已阻止：请先在 SCUM Robot/.env 中设置有效的 "
            "BOOTSTRAP_ADMIN_PASSWORD，不能留空或保留占位值。"
        )

    return {
        "username": username,
        "password": password,
    }


def create_default_admin(db: Session, steam_id: int = 76561198000000000,
                        username: str = "superadmin", password: Optional[str] = None) -> bool:
    """
    创建默认超级管理员账户
    
    Args:
        db: 数据库会话
        steam_id: Steam ID
        username: 用户名
        password: 密码
        
    Returns:
        bool: 创建是否成功
    """
    try:
        if is_placeholder_bootstrap_password(password):
            print("创建超级管理员失败: BOOTSTRAP_ADMIN_PASSWORD 未配置或仍为占位值")
            return False

        # 检查是否已存在超级管理员
        existing_admin = db.query(User).filter(User.user_type == UserType.SUPER_ADMIN).first()
        if existing_admin:
            print(f"超级管理员已存在: {existing_admin.username}")
            return True
        
        user_service = UserService(db)
        result = user_service.create_user(
            steam_id=steam_id,
            username=username,
            password=password,
            user_type=UserType.SUPER_ADMIN
        )
        
        if result.success:
            print(f"默认超级管理员创建成功: {username} (Steam ID: {steam_id})")
            return True
        else:
            print(f"创建超级管理员失败: {result.error.message}")
            return False
            
    except Exception as e:
        print(f"创建超级管理员时出错: {str(e)}")
        return False


def create_default_gift_packages(db: Session) -> bool:
    """
    创建默认礼包
    
    Args:
        db: 数据库会话
        
    Returns:
        bool: 创建是否成功
    """
    try:

        # 一次性礼包示例
        one_time_gift = db.query(GiftPackage).filter(
            GiftPackage.name == "新手装备礼包"
        ).first()

        if not one_time_gift:
            one_time_items = {
                "BP_Weapon_Pistol_1911": 1,
                "BP_Ammo_45ACP": 50,
                "BP_Equipment_Backpack_Small": 1,
                "BP_Consumable_Bandage": 10
            }

            one_time_gift = GiftPackage(
                name="新手装备礼包",
                description="新手专属一次性装备礼包",
                gift_type=GiftType.ONE_TIME,
                items_config=json.dumps(one_time_items, ensure_ascii=False),
                is_active=True,
                max_claims=1,
                cooldown_hours=0,
                required_level=0,
                total_quantity=None,
                claimed_quantity=0
            )
            db.add(one_time_gift)
            print("一次性礼包创建成功")

        # 每日礼包示例
        daily_gift_new = db.query(GiftPackage).filter(
            GiftPackage.name == "每日补给礼包"
        ).first()

        if not daily_gift_new:
            daily_items_new = {
                "BP_Consumable_MRE": 3,
                "BP_Consumable_Water": 3,
                "BP_Consumable_Bandage": 5
            }

            daily_gift_new = GiftPackage(
                name="每日补给礼包",
                description="每日可领取的基础补给",
                gift_type=GiftType.DAILY,
                items_config=json.dumps(daily_items_new, ensure_ascii=False),
                is_active=True,
                max_claims=-1,
                cooldown_hours=24,
                required_level=0,
                total_quantity=None,
                claimed_quantity=0
            )
            db.add(daily_gift_new)
            print("每日礼包创建成功")

        # 限量礼包示例
        limited_gift = db.query(GiftPackage).filter(
            GiftPackage.name == "限量武器礼包"
        ).first()

        if not limited_gift:
            limited_items = {
                "BP_Weapon_M4A1": 1,
                "BP_Ammo_556x45": 300,
                "BP_Equipment_Scope_ACOG": 1
            }

            limited_gift = GiftPackage(
                name="限量武器礼包",
                description="全服限量100份的高级武器礼包",
                gift_type=GiftType.LIMITED_QUANTITY,
                items_config=json.dumps(limited_items, ensure_ascii=False),
                is_active=True,
                max_claims=1,
                cooldown_hours=0,
                required_level=10,
                total_quantity=100,
                claimed_quantity=0
            )
            db.add(limited_gift)
            print("限量礼包创建成功")

        # 限时礼包示例
        limited_time_gift = db.query(GiftPackage).filter(
            GiftPackage.name == "周末特惠礼包"
        ).first()

        if not limited_time_gift:
            limited_time_items = {
                "BP_Weapon_AK74": 1,
                "BP_Ammo_762x39": 240,
                "BP_Equipment_Vest_Police": 1
            }

            # 设置为本周末
            start_time = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = start_time + timedelta(days=2)  # 2天限时

            limited_time_gift = GiftPackage(
                name="周末特惠礼包",
                description="周末限时礼包，限时48小时",
                gift_type=GiftType.LIMITED_TIME,
                items_config=json.dumps(limited_time_items, ensure_ascii=False),
                is_active=True,
                start_time=start_time,
                end_time=end_time,
                max_claims=3,  # 限时期间可领3次
                cooldown_hours=8,  # 8小时冷却
                required_level=5,
                total_quantity=None,
                claimed_quantity=0
            )
            db.add(limited_time_gift)
            print("限时礼包创建成功")

        # 限时限量礼包示例
        limited_time_quantity_gift = db.query(GiftPackage).filter(
            GiftPackage.name == "稀有装备礼包"
        ).first()

        if not limited_time_quantity_gift:
            rare_items = {
                "BP_Weapon_AWM": 1,
                "BP_Ammo_338Lapua": 20,
                "BP_Equipment_Scope_8x": 1,
                "BP_Equipment_Ghillie_Suit": 1
            }

            # 设置为3天限时
            start_time = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = start_time + timedelta(days=3)

            limited_time_quantity_gift = GiftPackage(
                name="稀有装备礼包",
                description="限时3天，全服限量50份的稀有装备礼包",
                gift_type=GiftType.LIMITED_TIME_QUANTITY,
                items_config=json.dumps(rare_items, ensure_ascii=False),
                is_active=True,
                start_time=start_time,
                end_time=end_time,
                max_claims=1,
                cooldown_hours=0,
                required_level=20,
                total_quantity=50,
                claimed_quantity=0
            )
            db.add(limited_time_quantity_gift)
            print("限时限量礼包创建成功")

        db.commit()
        return True
        
    except Exception as e:
        db.rollback()
        print(f"创建默认礼包时出错: {str(e)}")
        return False


def create_default_vip_configs(db: Session) -> bool:
    """
    创建默认VIP配置

    Args:
        db: 数据库会话

    Returns:
        bool: 创建是否成功
    """
    try:
        # VIP配置列表 (daily_gift_id将在礼包创建后设置)
        vip_configs = [
            {
                'level': 0,
                'name': '普通用户',
                'daily_gift_id': None,  # 将在礼包创建后关联
                'upgrade_required_points': 0,
                'enable_login_announcement': False
            },
            {
                'level': 1,
                'name': 'VIP青铜',
                'daily_gift_id': None,  # 将在礼包创建后关联
                'upgrade_required_points': 1000,
                'enable_login_announcement': False
            },
            {
                'level': 2,
                'name': 'VIP白银',
                'daily_gift_id': None,  # 将在礼包创建后关联
                'upgrade_required_points': 3000,
                'enable_login_announcement': False
            },
            {
                'level': 3,
                'name': 'VIP黄金',
                'daily_gift_id': None,  # 将在礼包创建后关联
                'upgrade_required_points': 6000,
                'enable_login_announcement': True
            },
            {
                'level': 4,
                'name': 'VIP铂金',
                'daily_gift_id': None,  # 将在礼包创建后关联
                'upgrade_required_points': 10000,
                'enable_login_announcement': True
            },
            {
                'level': 5,
                'name': 'VIP钻石',
                'daily_gift_id': None,  # 将在礼包创建后关联
                'upgrade_required_points': 20000,
                'enable_login_announcement': True
            }
        ]

        for config_data in vip_configs:
            # 检查是否已存在
            existing_config = db.query(VIPConfig).filter(
                VIPConfig.level == config_data['level']
            ).first()

            if not existing_config:
                vip_config = VIPConfig(
                    level=config_data['level'],
                    name=config_data['name'],
                    daily_gift_id=config_data['daily_gift_id'],
                    upgrade_required_points=config_data['upgrade_required_points'],
                    enable_login_announcement=config_data['enable_login_announcement']
                )
                db.add(vip_config)
                print(f"VIP{config_data['level']}配置创建成功: {config_data['name']}")

        db.commit()
        return True

    except Exception as e:
        db.rollback()
        print(f"创建默认VIP配置时出错: {str(e)}")
        return False


def create_admin_permissions(db: Session) -> bool:
    """
    创建管理员权限定义
    
    Args:
        db: 数据库会话
        
    Returns:
        bool: 创建是否成功
    """
    try:
        # 获取超级管理员
        super_admin = db.query(User).filter(User.user_type == UserType.SUPER_ADMIN).first()
        if not super_admin:
            print("未找到超级管理员，跳过权限创建")
            return True
        
        # 定义权限列表
        permissions = [
            ("user_management", "用户管理"),
            ("user_create", "创建用户"),
            ("user_edit", "编辑用户"),
            ("user_delete", "删除用户"),
            ("user_ban", "封禁用户"),
            ("asset_management", "资产管理"),
            ("asset_transfer", "资产转账"),
            ("gift_management", "礼包管理"),
            ("gift_create", "创建礼包"),
            ("gift_edit", "编辑礼包"),
            ("gift_delete", "删除礼包"),
            ("system_config", "系统配置"),
            ("view_logs", "查看日志"),
            ("admin_management", "管理员管理")
        ]
        
        for permission_key, permission_name in permissions:
            existing_permission = db.query(AdminPermission).filter(
                and_(
                    AdminPermission.user_id == super_admin.id,
                    AdminPermission.permission_key == permission_key
                )
            ).first()
            
            if not existing_permission:
                admin_permission = AdminPermission(
                    user_id=super_admin.id,
                    permission_key=permission_key,
                    permission_name=permission_name,
                    granted_by=super_admin.id
                )
                db.add(admin_permission)
        
        db.commit()
        print("管理员权限创建成功")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"创建管理员权限时出错: {str(e)}")
        return False


def initialize_database(db: Session, admin_steam_id: int = None,
                       admin_username: str = None, admin_password: str = None) -> bool:
    """
    初始化数据库数据

    Args:
        db: 数据库会话
        admin_steam_id: 管理员Steam ID
        admin_username: 管理员用户名
        admin_password: 管理员密码

    Returns:
        bool: 初始化是否成功
    """
    print("开始初始化数据库数据...")

    success = True

    # 创建默认超级管理员
    if is_placeholder_bootstrap_password(admin_password):
        print("数据库初始化失败: 缺少有效的 BOOTSTRAP_ADMIN_PASSWORD")
        return False

    admin_params = {}
    if admin_steam_id:
        admin_params['steam_id'] = admin_steam_id
    if admin_username:
        admin_params['username'] = admin_username
    if admin_password:
        admin_params['password'] = admin_password

    if not create_default_admin(db, **admin_params):
        success = False

    # 只创建VIP0配置
    try:
        existing_vip0 = db.query(VIPConfig).filter(VIPConfig.level == 0).first()
        if not existing_vip0:
            vip0 = VIPConfig(
                level=0,
                name='普通用户',
                daily_gift_id=None,
                upgrade_required_points=0,
                enable_login_announcement=False
            )
            db.add(vip0)
            db.commit()
            print("VIP0配置创建成功: 普通用户")
        else:
            print("VIP0配置已存在")
    except Exception as e:
        db.rollback()
        print(f"创建VIP0配置时出错: {str(e)}")
        success = False

    if success:
        print("数据库初始化完成！")
    else:
        print("数据库初始化过程中出现错误")

    return success


def reset_and_initialize(db: Session) -> bool:
    """
    重置并初始化数据库
    
    Args:
        db: 数据库会话
        
    Returns:
        bool: 操作是否成功
    """
    try:
        print("警告：这将删除所有用户数据！")
        
        # 删除所有用户相关数据
        db.query(AdminPermission).delete()
        db.query(UserGiftRecord).delete()
        db.query(UserAssets).delete()
        db.query(User).delete()
        db.query(GiftPackage).delete()
        db.query(VIPConfig).delete()
        
        db.commit()
        print("数据库清理完成")
        
        # 重新初始化
        return initialize_database(db)
        
    except Exception as e:
        db.rollback()
        print(f"重置数据库时出错: {str(e)}")
        return False


if __name__ == "__main__":
    # 独立运行时的测试代码
    from ..database.manager import DatabaseManager
    
    db_manager = DatabaseManager()
    if db_manager.init_database():
        with db_manager.get_db_session() as db:
            initialize_database(db)
    else:
        print("数据库初始化失败")
