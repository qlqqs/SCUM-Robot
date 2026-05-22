"""
服务层结果和错误处理
"""

from typing import Optional, Any, Dict
from enum import Enum


class ServiceErrorType(Enum):
    """服务错误类型"""
    # 通用错误
    NOT_FOUND = "not_found"
    ALREADY_EXISTS = "already_exists"
    INVALID_DATA = "invalid_data"
    VALIDATION_ERROR = "validation_error"
    PERMISSION_DENIED = "permission_denied"
    
    # 类目相关错误
    CATEGORY_NOT_FOUND = "category_not_found"
    CATEGORY_NAME_EXISTS = "category_name_exists"
    CATEGORY_HAS_SUBCATEGORIES = "category_has_subcategories"
    CATEGORY_HAS_ITEMS = "category_has_items"
    CATEGORY_INACTIVE = "category_inactive"
    
    # 子类目相关错误
    SUBCATEGORY_NOT_FOUND = "subcategory_not_found"
    SUBCATEGORY_NAME_EXISTS = "subcategory_name_exists"
    SUBCATEGORY_HAS_ITEMS = "subcategory_has_items"
    SUBCATEGORY_INACTIVE = "subcategory_inactive"
    PARENT_CATEGORY_NOT_FOUND = "parent_category_not_found"
    PARENT_CATEGORY_INACTIVE = "parent_category_inactive"
    
    # 物品相关错误
    ITEM_NOT_FOUND = "item_not_found"
    ITEM_NAME_EXISTS = "item_name_exists"
    ITEM_INACTIVE = "item_inactive"
    ITEM_OUT_OF_STOCK = "item_out_of_stock"
    ITEM_INVALID_PRICE = "item_invalid_price"
    ITEM_INVALID_STOCK = "item_invalid_stock"
    
    # 关联关系错误
    INVALID_CATEGORY_SUBCATEGORY_RELATION = "invalid_category_subcategory_relation"

    # 用户相关错误
    USER_NOT_FOUND = "user_not_found"
    USER_ALREADY_EXISTS = "user_already_exists"
    DUPLICATE_ENTRY = "duplicate_entry"
    AUTHENTICATION_FAILED = "authentication_failed"
    INSUFFICIENT_BALANCE = "insufficient_balance"
    INVALID_PARAMETER = "invalid_parameter"

    # 数据库错误
    DATABASE_ERROR = "database_error"
    CONNECTION_ERROR = "connection_error"
    TRANSACTION_ERROR = "transaction_error"


class ServiceError:
    """服务错误信息"""
    
    def __init__(self, error_type: ServiceErrorType, message: str, details: Optional[Dict[str, Any]] = None):
        self.error_type = error_type
        self.message = message
        self.details = details or {}
    
    def __str__(self):
        return f"{self.error_type.value}: {self.message}"
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "error_type": self.error_type.value,
            "message": self.message,
            "details": self.details
        }


class ServiceResult:
    """服务层结果"""

    def __init__(self, success: bool, data: Optional[Any] = None, error: Optional[ServiceError] = None, message: str = ""):
        self.success = success
        self.data = data
        self.error = error
        self.message = message

    @classmethod
    def success(cls, data: Any = None, message: str = "操作成功"):
        """创建成功结果"""
        return cls(success=True, data=data, message=message)

    @classmethod
    def error(cls, error_type: ServiceErrorType, message: str, details: Optional[Dict[str, Any]] = None):
        """创建错误结果"""
        error = ServiceError(error_type, message, details)
        return cls(success=False, error=error, message=message)

    @classmethod
    def success_result(cls, data: Any = None):
        """创建成功结果"""
        return cls(success=True, data=data)

    @classmethod
    def error_result(cls, error_type: ServiceErrorType, message: str, details: Optional[Dict[str, Any]] = None):
        """创建错误结果"""
        error = ServiceError(error_type, message, details)
        return cls(success=False, error=error)
    
    def is_success(self) -> bool:
        """是否成功"""
        return self.success
    
    def is_error(self) -> bool:
        """是否错误"""
        return not self.success
    
    def get_data(self):
        """获取数据"""
        return self.data
    
    def get_error(self) -> Optional[ServiceError]:
        """获取错误信息"""
        return self.error
    
    def get_error_message(self) -> str:
        """获取错误消息"""
        return self.error.message if self.error else ""
    
    def get_error_type(self) -> Optional[ServiceErrorType]:
        """获取错误类型"""
        return self.error.error_type if self.error else None


# 便捷函数
def success(data: Any = None) -> ServiceResult:
    """创建成功结果"""
    return ServiceResult.success_result(data)


def error(error_type: ServiceErrorType, message: str, details: Optional[Dict[str, Any]] = None) -> ServiceResult:
    """创建错误结果"""
    return ServiceResult.error_result(error_type, message, details)


# 常用错误创建函数
def not_found_error(resource: str, identifier: Any) -> ServiceResult:
    """资源未找到错误"""
    return error(
        ServiceErrorType.NOT_FOUND,
        f"{resource} {identifier} 不存在",
        {"resource": resource, "identifier": identifier}
    )


def already_exists_error(resource: str, field: str, value: Any) -> ServiceResult:
    """资源已存在错误"""
    return error(
        ServiceErrorType.ALREADY_EXISTS,
        f"{resource}{field} '{value}' 已存在，请使用其他{field}",
        {"resource": resource, "field": field, "value": value}
    )


def validation_error(message: str, details: Optional[Dict[str, Any]] = None) -> ServiceResult:
    """验证错误"""
    return error(ServiceErrorType.VALIDATION_ERROR, message, details)


def database_error(message: str, details: Optional[Dict[str, Any]] = None) -> ServiceResult:
    """数据库错误"""
    return error(ServiceErrorType.DATABASE_ERROR, f"数据库操作失败: {message}", details)


# 特定业务错误函数
def category_not_found_error(category_id: int) -> ServiceResult:
    """类目未找到错误"""
    return error(
        ServiceErrorType.CATEGORY_NOT_FOUND,
        f"类目ID {category_id} 不存在",
        {"category_id": category_id}
    )


def subcategory_not_found_error(subcategory_id: int) -> ServiceResult:
    """子类目未找到错误"""
    return error(
        ServiceErrorType.SUBCATEGORY_NOT_FOUND,
        f"子类目ID {subcategory_id} 不存在",
        {"subcategory_id": subcategory_id}
    )


def item_not_found_error(item_id: int) -> ServiceResult:
    """物品未找到错误"""
    return error(
        ServiceErrorType.ITEM_NOT_FOUND,
        f"物品ID {item_id} 不存在",
        {"item_id": item_id}
    )


def name_exists_error(resource_type: str, name: str, context: str = "") -> ServiceResult:
    """名称已存在错误"""
    context_msg = f"在{context}下" if context else ""
    if resource_type == "category":
        error_type = ServiceErrorType.CATEGORY_NAME_EXISTS
    elif resource_type == "subcategory":
        error_type = ServiceErrorType.SUBCATEGORY_NAME_EXISTS
    elif resource_type == "item":
        error_type = ServiceErrorType.ITEM_NAME_EXISTS
    else:
        error_type = ServiceErrorType.ALREADY_EXISTS
    
    return error(
        error_type,
        f"{resource_type}名称 '{name}' {context_msg}已存在，请使用其他名称",
        {"resource_type": resource_type, "name": name, "context": context}
    )
