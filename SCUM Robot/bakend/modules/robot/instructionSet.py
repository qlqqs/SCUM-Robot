"""
SCUM 游戏指令集模块 - 提供预定义的游戏命令集合

作者: GitHub Copilot
日期: 2025年9月16日
版本: 1.0

功能:
1. 玩家管理: 货币、声望等
2. 消息发送: 公屏消息、管理员公告等
3. 传送类: 各种传送功能
4. 物品生成: 物品、动物、僵尸、载具生成
"""

from typing import Union, Optional, Dict, List
from enum import Enum
from .sentCommand import CommandSender


class CurrencyType(Enum):
    """货币类型枚举"""
    NORMAL = "Normal"  # 普通货币
    GOLD = "Gold"      # 金条


class ModifierType(Enum):
    """载具修改器类型"""
    FULL = "Full"                      # 满配装甲
    WHEELS_ONLY = "WheelsOnly"        # 只有轮子
    MINIMAL_FUNCTIONAL = "MinimalFunctional"  # 最小可用


class InstructionSet:
    """SCUM 游戏指令集合类"""
    
    def __init__(self, enable_sender: bool = True):
        """
        初始化指令集
        
        Args:
            enable_sender: 是否启用命令发送器（用于直接执行命令）
        """
        self.sender = CommandSender() if enable_sender else None
        self.enable_sender = enable_sender
    
    def _execute_command(self, command: str, execute: bool = False) -> Union[str, bool]:
        """
        内部方法：执行或返回命令字符串
        
        Args:
            command: 命令字符串
            execute: 是否直接执行命令
            
        Returns:
            如果execute为True，返回执行结果（bool）；否则返回命令字符串
        """
        if execute and self.sender:
            return self.sender.send_scum_command(command)
        elif execute and not self.sender:
            print("错误: 命令发送器未启用，请在初始化时设置 enable_sender=True")
            return False
        else:
            return command
    
    # ========================= 玩家管理 =========================
    
    def change_currency_balance(self, amount: int, 
                              player_identifier: str,
                              currency_type: CurrencyType = CurrencyType.NORMAL,
                              execute: bool = False) -> Union[str, bool]:
        """
        改变玩家货币余额
        
        Args:
            amount: 货币数量（正数增加，负数扣除）
            player_identifier: 玩家名字或SteamID
            currency_type: 货币类型（Normal/Gold）
            execute: 是否直接执行命令（True执行并返回结果，False返回命令字符串）
        
        Returns:
            如果execute为True，返回执行结果（bool）；否则返回命令字符串
            
        Examples:
            >>> inst.change_currency_balance(999, "Player1")
            "#ChangeCurrencyBalance Normal 999 Player1"
            >>> inst.change_currency_balance(999, "Player1", execute=True)
            True  # 直接执行命令并返回执行结果
        """
        command = f"#ChangeCurrencyBalance {currency_type.value} {amount} {player_identifier}"
        return self._execute_command(command, execute)
    
    def change_currency_balance_to_all(self, amount: int,
                                     currency_type: CurrencyType = CurrencyType.NORMAL,
                                     execute: bool = False) -> Union[str, bool]:
        """
        改变所有玩家货币余额
        
        Args:
            amount: 货币数量（正数增加，负数扣除）
            currency_type: 货币类型（Normal/Gold）
            execute: 是否直接执行命令
        
        Returns:
            如果execute为True，返回执行结果（bool）；否则返回命令字符串
            
        Examples:
            >>> inst.change_currency_balance_to_all(999)
            "#ChangeCurrencyBalanceToAll Normal 999"
            >>> inst.change_currency_balance_to_all(-100, CurrencyType.GOLD, execute=True)
            True  # 直接执行命令并返回结果
        """
        command = f"#ChangeCurrencyBalanceToAll {currency_type.value} {amount}"
        return self._execute_command(command, execute)
    
    def change_currency_balance_to_all_online(self, amount: int,
                                            currency_type: CurrencyType = CurrencyType.NORMAL,
                                            execute: bool = False) -> Union[str, bool]:
        """
        改变所有在线玩家货币余额
        
        Args:
            amount: 货币数量（正数增加，负数扣除）
            currency_type: 货币类型（Normal/Gold）
            execute: 是否直接执行命令
        
        Returns:
            如果execute为True，返回执行结果（bool）；否则返回命令字符串
            
        Examples:
            >>> inst.change_currency_balance_to_all_online(999)
            "#ChangeCurrencyBalanceToAllOnline Normal 999"
        """
        command = f"#ChangeCurrencyBalanceToAllOnline {currency_type.value} {amount}"
        return self._execute_command(command, execute)
    
    def set_currency_balance(self, amount: int, 
                           player_identifier: str,
                           currency_type: CurrencyType = CurrencyType.NORMAL,
                           execute: bool = False) -> Union[str, bool]:
        """
        设置玩家货币余额
        
        Args:
            amount: 货币数量
            player_identifier: 玩家名字或SteamID
            currency_type: 货币类型（Normal/Gold）
            execute: 是否直接执行命令
        
        Returns:
            如果execute为True，返回执行结果（bool）；否则返回命令字符串
            
        Examples:
            >>> inst.set_currency_balance(100, "Player1")
            "#SetCurrencyBalance Normal 100 Player1"
            >>> inst.set_currency_balance(100, "Player1", execute=True)
            True  # 直接执行命令并返回结果
        """
        command = f"#SetCurrencyBalance {currency_type.value} {amount} {player_identifier}"
        return self._execute_command(command, execute)
    
    def change_fame_points(self, points: int, player_identifier: str, execute: bool = False) -> Union[str, bool]:
        """
        改变玩家声望点数
        
        Args:
            points: 声望点数（可为负数）
            player_identifier: 玩家名字或SteamID
            execute: 是否直接执行命令
        
        Returns:
            如果execute为True，返回执行结果（bool）；否则返回命令字符串
            
        Examples:
            >>> inst.change_fame_points(100, "Player1")
            "#ChangeFamePoints 100 Player1"
        """
        command = f"#ChangeFamePoints {points} {player_identifier}"
        return self._execute_command(command, execute)
    
    def set_fame_points(self, points: int, player_identifier: str, execute: bool = False) -> Union[str, bool]:
        """
        设置玩家声望点数
        
        Args:
            points: 声望点数
            player_identifier: 玩家SteamID
            execute: 是否直接执行命令
        
        Returns:
            如果execute为True，返回执行结果（bool）；否则返回命令字符串
            
        Examples:
            >>> inst.set_fame_points(100, "76561198012345678")
            "#SetFamePoints 100 76561198012345678"
            >>> inst.set_fame_points(100, "76561198012345678", execute=True)
            True  # 直接执行命令并返回结果
        """
        command = f"#SetFamePoints {points} {player_identifier}"
        return self._execute_command(command, execute)
    
    # ========================= 服主常用 =========================
    
    def announce(self, message: str, execute: bool = False) -> Union[str, bool]:
        """
        红字公告广播
        
        Args:
            message: 公告内容
            execute: 是否直接执行命令
        
        Returns:
            如果execute为True，返回执行结果（bool）；否则返回命令字符串
            
        Examples:
            >>> inst.announce("服务器维护通知")
            "#Announce 服务器维护通知"
            >>> inst.announce("服务器维护通知", execute=True)
            True  # 直接执行并返回结果
        """
        command = f"#Announce {message}"
        return self._execute_command(command, execute)
    
    # ========================= 消息发送 =========================

    def send_public_message(self, message: str, execute: bool = False) -> Union[str, bool]:
        """
        发送公屏消息

        Args:
            message: 要发送的消息内容
            execute: 是否直接执行命令（True执行并返回结果，False返回消息内容）

        Returns:
            如果execute为True，返回执行结果（bool）；否则返回消息内容

        Examples:
            >>> inst.send_public_message("欢迎来到服务器！")
            "欢迎来到服务器！"
            >>> inst.send_public_message("服务器将在5分钟后重启", execute=True)
            True  # 直接发送消息并返回执行结果
        """
        if execute and self.sender:
            # 直接发送公屏消息（按t键，粘贴消息，按两下回车）
            return self.sender.send_command(
                window_title="SCUM  ",
                command=message,
                press_enter=True
            )
        elif execute and not self.sender:
            print("错误: 命令发送器未启用，请在初始化时设置 enable_sender=True")
            return False
        else:
            return message

    def send_admin_message(self, message: str, execute: bool = False) -> Union[str, bool]:
        """
        发送管理员消息（带#Announce命令）

        Args:
            message: 要发送的消息内容
            execute: 是否直接执行命令

        Returns:
            如果execute为True，返回执行结果（bool）；否则返回命令字符串

        Examples:
            >>> inst.send_admin_message("服务器公告：欢迎新玩家！")
            "#Announce 服务器公告：欢迎新玩家！"
            >>> inst.send_admin_message("重要通知：服务器维护", execute=True)
            True  # 直接执行命令并返回结果
        """
        command = f"#Announce {message}"
        return self._execute_command(command, execute)

    # ========================= 传送类 =========================
    
    def teleport_to_coordinates(self, x: float, y: float, z: float, 
                              player_identifier: Optional[str] = None,
                              execute: bool = False) -> Union[str, bool]:
        """
        传送到指定坐标
        
        Args:
            x: X坐标
            y: Y坐标  
            z: Z坐标
            player_identifier: 玩家名字或SteamID（可选，为空则传送自己）
            execute: 是否直接执行命令
        
        Returns:
            如果execute为True，返回执行结果（bool）；否则返回命令字符串
            
        Examples:
            >>> inst.teleport_to_coordinates(0, 0, 0)
            "#Teleport 0 0 0"
            >>> inst.teleport_to_coordinates(100, 200, 300, "Player1", execute=True)
            True  # 直接执行命令并返回结果
        """
        if player_identifier:
            command = f"#Teleport {x} {y} {z} {player_identifier}"
        else:
            command = f"#Teleport {x} {y} {z}"
        return self._execute_command(command, execute)
    
    def teleport_to_player(self, target_player: str, 
                         source_player: Optional[str] = None,
                         execute: bool = False) -> Union[str, bool]:
        """
        传送到玩家
        
        Args:
            target_player: 目标玩家名字或SteamID
            source_player: 要传送的玩家（可选，为空则传送自己）
            execute: 是否直接执行命令
        
        Returns:
            如果execute为True，返回执行结果（bool）；否则返回命令字符串
            
        Examples:
            >>> inst.teleport_to_player("Player1")
            "#TeleportTo Player1"
            >>> inst.teleport_to_player("Player1", "Player2", execute=True)
            True  # 直接执行命令并返回结果
        """
        if source_player:
            command = f"#TeleportTo {target_player} {source_player}"
        else:
            command = f"#TeleportTo {target_player}"
        return self._execute_command(command, execute)
    
    def teleport_to_me(self, player_identifier: str, execute: bool = False) -> Union[str, bool]:
        """
        传送玩家到我
        
        Args:
            player_identifier: 玩家名字或SteamID
            execute: 是否直接执行命令
        
        Returns:
            如果execute为True，返回执行结果（bool）；否则返回命令字符串
            
        Examples:
            >>> inst.teleport_to_me("Player1")
            "#TeleportToMe Player1"
            >>> inst.teleport_to_me("Player1", execute=True)
            True  # 直接执行命令并返回结果
        """
        command = f"#TeleportToMe {player_identifier}"
        return self._execute_command(command, execute)
    
    def teleport_random(self, player_identifier: Optional[str] = None,
                      execute: bool = False) -> Union[str, bool]:
        """
        随机传送
        
        Args:
            player_identifier: 玩家名字或SteamID（可选，为空则传送自己）
            execute: 是否直接执行命令
        
        Returns:
            如果execute为True，返回执行结果（bool）；否则返回命令字符串
            
        Examples:
            >>> inst.teleport_random()
            "#TeleportTo3pm"
            >>> inst.teleport_random("Player1", execute=True)
            True  # 直接执行命令并返回结果
        """
        if player_identifier:
            command = f"#TeleportTo3pm {player_identifier}"
        else:
            command = "#TeleportTo3pm"
        return self._execute_command(command, execute)
    
    # ========================= 物品生成 =========================
    
    def spawn_item(self, item_name: str, quantity: int = 1,
                   health: Optional[int] = None,
                   uses: Optional[int] = None,
                   dirtiness: Optional[int] = None,
                   location: Optional[Union[str, tuple]] = None,
                   keycard_sector: Optional[str] = None,
                   cash_value: Optional[int] = None,
                   ammo_count: Optional[int] = None,
                   execute: bool = False) -> Union[str, bool]:
        """
        生成物品
        
        Args:
            item_name: 物品名称
            quantity: 数量
            health: 物品耐久度
            uses: 物品使用次数
            dirtiness: 物品脏度
            location: 物品位置（坐标元组、坐标字符串或玩家SteamID）
            keycard_sector: 钥匙卡区域
            cash_value: 现金价值
            ammo_count: 弹药数量
            execute: 是否直接执行命令
        
        Returns:
            如果execute为True，返回执行结果（bool）；否则返回命令字符串
            
        Examples:
            >>> inst.spawn_item("Cigarette", 1)
            "#SpawnItem Cigarette 1"
            >>> inst.spawn_item("Magazine_AK47", 1, ammo_count=30, location="Player1", execute=True)
            True  # 直接执行命令
        """
        cmd = f"#SpawnItem {item_name} {quantity}"
        
        # 添加可选参数
        if health is not None:
            cmd += f" Health {health}"
        if uses is not None:
            cmd += f" Uses {uses}"
        if dirtiness is not None:
            cmd += f" Dirtiness {dirtiness}"
        if location is not None:
            if isinstance(location, tuple) and len(location) == 3:
                cmd += f' Location "{location[0]} {location[1]} {location[2]}"'
            elif isinstance(location, str):
                if " " in location and not location.startswith(("X=", "76561")):
                    cmd += f' Location "{location}"'
                else:
                    cmd += f" Location {location}"
        if keycard_sector is not None:
            cmd += f" KeyCardSector {keycard_sector}"
        if cash_value is not None:
            cmd += f" CashValue {cash_value}"
        if ammo_count is not None:
            cmd += f" AmmoCount {ammo_count}"
        
        return self._execute_command(cmd, execute)
    
    def spawn_animal(self, animal_type: str, quantity: int = 1,
                    location: Optional[Union[str, tuple]] = None,
                    execute: bool = False) -> Union[str, bool]:
        """
        生成动物
        
        Args:
            animal_type: 动物类型（如 BP_Bear2）
            quantity: 数量
            location: 生成位置（坐标元组、坐标字符串或玩家SteamID）
            execute: 是否直接执行命令
        
        Returns:
            如果execute为True，返回执行结果（bool）；否则返回命令字符串
            
        Examples:
            >>> inst.spawn_animal("BP_Bear2", 1)
            "#SpawnAnimal BP_Bear2 1"
            >>> inst.spawn_animal("BP_Bear2", 1, location="Player1", execute=True)
            True  # 直接执行命令并返回结果
        """
        cmd = f"#SpawnAnimal {animal_type} {quantity}"
        
        if location is not None:
            if isinstance(location, tuple) and len(location) == 3:
                cmd += f' Location "{location[0]} {location[1]} {location[2]}"'
            elif isinstance(location, str):
                if " " in location and not location.startswith(("X=", "76561")):
                    cmd += f' Location "{location}"'
                else:
                    cmd += f" Location {location}"
        
        return self._execute_command(cmd, execute)
    
    def spawn_zombie(self, zombie_type: str, quantity: int = 1,
                    location: Optional[Union[str, tuple]] = None,
                    execute: bool = False) -> Union[str, bool]:
        """
        生成僵尸
        
        Args:
            zombie_type: 僵尸类型（如 BP_Zombie, BP_Zombie_SuicideVest）
            quantity: 数量
            location: 生成位置（坐标元组、坐标字符串或玩家SteamID）
            execute: 是否直接执行命令
        
        Returns:
            如果execute为True，返回执行结果（bool）；否则返回命令字符串
            
        Examples:
            >>> inst.spawn_zombie("BP_Zombie", 1)
            "#SpawnZombie BP_Zombie 1"
            >>> inst.spawn_zombie("BP_Zombie_SuicideVest", 1, location=(0, 0, 0), execute=True)
            True  # 直接执行命令并返回结果
        """
        cmd = f"#SpawnZombie {zombie_type} {quantity}"
        
        if location is not None:
            if isinstance(location, tuple) and len(location) == 3:
                cmd += f' Location "{location[0]} {location[1]} {location[2]}"'
            elif isinstance(location, str):
                if " " in location and not location.startswith(("X=", "76561")):
                    cmd += f' Location "{location}"'
                else:
                    cmd += f" Location {location}"
        
        return self._execute_command(cmd, execute)
    
    def spawn_vehicle(self, vehicle_type: str, quantity: int = 1,
                     location: Optional[Union[str, tuple]] = None,
                     modifier: Optional[ModifierType] = None,
                     execute: bool = False) -> Union[str, bool]:
        """
        生成载具
        
        Args:
            vehicle_type: 载具类型（如 BPC_Laika）
            quantity: 数量
            location: 生成位置（坐标元组、坐标字符串或玩家SteamID）
            modifier: 载具修改器（Full/WheelsOnly/MinimalFunctional）
            execute: 是否直接执行命令
        
        Returns:
            如果execute为True，返回执行结果（bool）；否则返回命令字符串
            
        Examples:
            >>> inst.spawn_vehicle("BPC_Laika", 1)
            "#SpawnVehicle BPC_Laika 1"
            >>> inst.spawn_vehicle("BPC_Laika", 1, location="Player1", modifier=ModifierType.FULL, execute=True)
            True  # 直接执行命令并返回结果
        """
        cmd = f"#SpawnVehicle {vehicle_type} {quantity}"
        
        if location is not None:
            if isinstance(location, tuple) and len(location) == 3:
                cmd += f' Location "{location[0]} {location[1]} {location[2]}"'
            elif isinstance(location, str):
                if " " in location and not location.startswith(("X=", "76561")):
                    cmd += f' Location "{location}"'
                else:
                    cmd += f" Location {location}"
        
        if modifier is not None:
            cmd += f" Modifier {modifier.value}"
        
        return self._execute_command(cmd, execute)
    
    def schedule_cargo_drop(self, x: float = 0, y: float = 0, z: float = 0, execute: bool = False) -> Union[str, bool]:
        """
        生成随机空投
        
        Args:
            x: X坐标（默认0）
            y: Y坐标（默认0）  
            z: Z坐标（默认0）
            execute: 是否直接执行命令
        
        Returns:
            如果execute为True，返回执行结果（bool）；否则返回命令字符串
            
        Examples:
            >>> inst.schedule_cargo_drop()
            "#ScheduleWorldEvent BP_CargoDropEvent 0 0 0"
        """
        command = f"#ScheduleWorldEvent BP_CargoDropEvent {x} {y} {z}"
        return self._execute_command(command, execute)
    
    def spawn_full_magazine(self, magazine_type: str, ammo_count: int,
                          location: str, execute: bool = False) -> Union[str, bool]:
        """
        刷出满配弹夹
        
        Args:
            magazine_type: 弹夹类型（如 Magazine_AK15）
            ammo_count: 子弹数量
            location: 玩家SteamID
            execute: 是否直接执行命令
        
        Returns:
            如果execute为True，返回执行结果（bool）；否则返回命令字符串
            
        Examples:
            >>> inst.spawn_full_magazine("Magazine_AK15", 30, "76561198012345678")
            "#spawnitem Magazine_AK15 1 AmmoCount 30 Location 76561198012345678"
            >>> inst.spawn_full_magazine("Magazine_AK15", 30, "76561198012345678", execute=True)
            True  # 直接执行命令并返回结果
        """
        command = f"#spawnitem {magazine_type} 1 AmmoCount {ammo_count} Location {location}"
        return self._execute_command(command, execute)
    
    
    # ========================= 预设组合指令 =========================
    
    def give_starter_package(self, player_identifier: str, execute: bool = False) -> Union[List[str], bool]:
        """
        给玩家新手大礼包
        
        Args:
            player_identifier: 玩家名字或SteamID
            execute: 是否直接执行所有命令
        
        Returns:
            如果execute为True，返回整体执行结果（bool）；否则返回命令列表
            
        Examples:
            >>> inst.give_starter_package("Player1")
            ['#ChangeCurrencyBalance Normal 1000 Player1', '#ChangeFamePoints 50 Player1', ...]
            >>> inst.give_starter_package("Player1", execute=True)
            True  # 执行所有命令并返回整体结果
        """
        commands = [
            self.change_currency_balance(1000, player_identifier, execute=False),
            self.change_fame_points(50, player_identifier, execute=False),
            self.spawn_item("Backpack_Medium", 1, location=player_identifier, execute=False),
            self.spawn_item("Rifle_M16A4", 1, location=player_identifier, execute=False),
            self.spawn_item("Magazine_M16A4", 3, ammo_count=30, location=player_identifier, execute=False)
        ]
        
        if execute and self.sender:
            # 批量执行所有命令
            results = []
            for cmd in commands:
                result = self.sender.send_scum_command(str(cmd))
                results.append(result)
                if not result:
                    print(f"命令执行失败: {cmd}")
                    return False  # 如果有任何命令失败，返回False
            return all(results)  # 所有命令都成功才返回True
        elif execute and not self.sender:
            print("错误: 命令发送器未启用")
            return False
        else:
            return [str(cmd) for cmd in commands]

def main():
    """主函数 - 示例用法和测试"""
    print("=== SCUM 指令集模块测试 ===")
    
    # 创建指令集实例
    inst = InstructionSet()
    
    # 测试各种指令
    print("\\n1. 玩家管理指令:")
    print("   货币管理:")
    print(f"     {inst.change_currency_balance(999, 'Player1')}")
    print(f"     {inst.change_currency_balance(-500, 'Player1', CurrencyType.GOLD)}")
    print(f"     {inst.set_currency_balance(100, 'Player1')}")
    print("   玩家控制:")
    
    print("\\n2. 消息发送指令:")
    print(f"     {inst.send_public_message('欢迎来到服务器！')}")
    print(f"     {inst.send_admin_message('服务器重启通知')}")
    
    print("\\n3. 传送类指令:")
    print(f"     {inst.teleport_to_coordinates(0, 0, 0)}")
    print(f"     {inst.teleport_to_player('Player1')}")
    print(f"     {inst.teleport_to_me('Player1')}")
    print(f"     {inst.teleport_random()}")
    
    print("\\n4. 物品生成指令:")
    print("   基础生成:")
    print(f"     {inst.spawn_item('Cigarette', 1)}")
    print("   带参数生成:")
    print(f"     {inst.spawn_item('Magazine_AK47', 1, ammo_count=30, location='Player1')}")
    print(f"     {inst.spawn_item('Tool_Box', 1, uses=10, health=80)}")
    print("   动物和僵尸:")
    print(f"     {inst.spawn_animal('BP_Bear2', 1, location=(0, 0, 0))}")
    print(f"     {inst.spawn_zombie('BP_Zombie_SuicideVest', 1, location='Player1')}")
    print("   载具生成:")
    print(f"     {inst.spawn_vehicle('BPC_Laika', 1, location='Player1', modifier=ModifierType.FULL)}")
    
    print("\\n6. 预设组合指令:")
    print("   新手大礼包:")
    starter_commands = inst.give_starter_package("NewPlayer", execute=False)
    if isinstance(starter_commands, list):
        for i, cmd in enumerate(starter_commands, 1):
            print(f"     {i}. {cmd}")
    
    print("\\n=== 使用示例 ===")
    print("# 导入并使用指令集:")
    print("from instructionSet import InstructionSet, CurrencyType, ModifierType")
    print("\\ninst = InstructionSet()")
    print("\\n# 给玩家加钱")
    print("command = inst.change_currency_balance(1000, 'Player1')")
    print("print(command)  # 输出: #ChangeCurrencyBalance Normal 1000 Player1")
    print("\\n# 生成载具")
    print("command = inst.spawn_vehicle('BPC_Laika', 1, location='Player1', modifier=ModifierType.FULL)")
    print("print(command)  # 输出: #SpawnVehicle BPC_Laika 1 Location Player1 Modifier Full")


# ========================= 常用物品/载具/动物名称常量 =========================

class ItemNames:
    """常用物品名称"""
    # 武器
    RIFLE_AK47 = "Rifle_AK47"
    RIFLE_M16A4 = "Rifle_M16A4"
    PISTOL_GLOCK = "Pistol_Glock17"
    
    # 弹夹
    MAGAZINE_AK47 = "Magazine_AK47"
    MAGAZINE_M16A4 = "Magazine_M16A4"
    MAGAZINE_AK15 = "Magazine_AK15"
    
    # 工具
    TOOL_BOX = "Tool_Box"
    CIGARETTE = "Cigarette"
    CASH = "Cash"
    KEYCARD = "KeyCard"
    
    # 装备
    BACKPACK_MEDIUM = "Backpack_Medium"
    BACKPACK_LARGE = "Backpack_Large"


class VehicleNames:
    """常用载具名称"""
    LAIKA = "BPC_Laika"
    MOUNTAIN_BIKE = "BPC_MountainBike"
    MOTORBIKE = "BPC_Motorbike"
    TRUCK = "BPC_Truck"
    HELICOPTER = "BPC_Helicopter"


class AnimalNames:
    """常用动物名称"""
    BEAR = "BP_Bear2"
    WOLF = "BP_Wolf"
    DEER = "BP_Deer"
    BOAR = "BP_Boar"


class ZombieNames:
    """常用僵尸名称"""
    NORMAL_ZOMBIE = "BP_Zombie"
    SUICIDE_ZOMBIE = "BP_Zombie_SuicideVest"
    ARMORED_ZOMBIE = "BP_Zombie_Armored"


if __name__ == "__main__":
    main()
