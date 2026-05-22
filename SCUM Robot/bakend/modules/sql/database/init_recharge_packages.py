"""
初始化充值套餐数据
"""

from sqlalchemy.orm import Session
from ..models.recharge_package_models import RechargePackage


def create_default_recharge_packages(session: Session) -> bool:
    """
    创建默认充值套餐
    
    Args:
        session: 数据库会话
        
    Returns:
        bool: 创建是否成功
    """
    try:
        # 检查是否已存在套餐
        existing_count = session.query(RechargePackage).count()
        if existing_count > 0:
            print(f"充值套餐已存在 ({existing_count}个)，跳过创建")
            return True
        
        # 定义默认套餐
        packages = [
            {
                'name': '体验套餐',
                'description': '新手体验，小额充值',
                'tag': '新手推荐',
                'price': 6.0,
                'coins': 60,
                'bonus_coins': 0,
                'badge': 'NEW',
                'sort_order': 1,
                'is_active': True,
                'is_hot': False,
                'is_recommended': True,
            },
            {
                'name': '基础套餐',
                'description': '日常充值，性价比高',
                'tag': None,
                'price': 30.0,
                'coins': 300,
                'bonus_coins': 50,
                'badge': None,
                'sort_order': 2,
                'is_active': True,
                'is_hot': False,
                'is_recommended': False,
            },
            {
                'name': '性价比之选',
                'description': '最受欢迎，超值优惠',
                'tag': '性价比之选',
                'price': 68.0,
                'coins': 680,
                'bonus_coins': 150,
                'badge': 'HOT',
                'sort_order': 3,
                'is_active': True,
                'is_hot': True,
                'is_recommended': True,
            },
            {
                'name': '进阶套餐',
                'description': '进阶玩家首选',
                'tag': None,
                'price': 128.0,
                'coins': 1280,
                'bonus_coins': 320,
                'badge': None,
                'sort_order': 4,
                'is_active': True,
                'is_hot': False,
                'is_recommended': False,
            },
            {
                'name': '豪华套餐',
                'description': '豪华享受，超多赠送',
                'tag': '热门推荐',
                'price': 298.0,
                'coins': 2980,
                'bonus_coins': 800,
                'badge': 'HOT',
                'sort_order': 5,
                'is_active': True,
                'is_hot': True,
                'is_recommended': True,
            },
            {
                'name': '至尊套餐',
                'description': '至尊体验，尊享特权',
                'tag': '土豪专属',
                'price': 648.0,
                'coins': 6480,
                'bonus_coins': 2000,
                'badge': 'VIP',
                'sort_order': 6,
                'is_active': True,
                'is_hot': False,
                'is_recommended': False,
            },
        ]
        
        # 创建套餐
        for pkg_data in packages:
            package = RechargePackage(**pkg_data)
            package.calculate_total_coins()  # 计算总商城币
            session.add(package)
        
        session.commit()
        
        print(f"充值套餐创建成功: {len(packages)}个套餐")
        
        # 显示创建的套餐
        for pkg in packages:
            print(f"  - {pkg['name']}: ¥{pkg['price']} → {pkg['coins']}+{pkg['bonus_coins']}={pkg['coins']+pkg['bonus_coins']}商城币")
        
        return True
        
    except Exception as e:
        session.rollback()
        print(f"创建充值套餐时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 独立运行时的测试代码
    from ..database.manager import DatabaseManager
    
    db_manager = DatabaseManager()
    if db_manager.init_database():
        with db_manager.get_db_session() as session:
            create_default_recharge_packages(session)
    else:
        print("数据库初始化失败")

