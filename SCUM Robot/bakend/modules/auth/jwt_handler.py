"""
JWT 认证处理器
"""

import jwt
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Request
import os
from dotenv import load_dotenv

load_dotenv()

# JWT 配置
JWT_SECRET_PLACEHOLDERS = {
    "change-me",
    "please-change-me",
    "replace-me",
    "replace-with-a-strong-random-string",
    "your-very-long-random-secret",
}


def _resolve_jwt_secret_key() -> str:
    configured_secret = (os.getenv('JWT_SECRET_KEY') or '').strip()
    if configured_secret and configured_secret.lower() not in JWT_SECRET_PLACEHOLDERS:
        return configured_secret

    generated_secret = secrets.token_urlsafe(32)
    if configured_secret:
        print("[WARN] JWT_SECRET_KEY 仍是占位值，已改用临时随机密钥。请在 .env 中配置真实密钥。")
    else:
        print("[WARN] 未设置 JWT_SECRET_KEY，已改用临时随机密钥。请在 .env 中配置真实密钥。")
    return generated_secret


JWT_SECRET_KEY = _resolve_jwt_secret_key()
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', '30'))
JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRE_DAYS', '7'))


class JWTHandler:
    """JWT 处理器"""
    
    def __init__(self):
        self.secret_key = JWT_SECRET_KEY
        self.algorithm = JWT_ALGORITHM
        self.access_token_expire_minutes = JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = JWT_REFRESH_TOKEN_EXPIRE_DAYS
    
    def create_access_token(self, user_data: Dict[str, Any], expire_minutes: Optional[int] = None) -> str:
        """
        创建访问令牌

        Args:
            user_data: 用户数据
            expire_minutes: 自定义过期时间（分钟），如果为None则使用默认值

        Returns:
            str: JWT 访问令牌
        """
        if expire_minutes is None:
            expire_minutes = self.access_token_expire_minutes
        expire = datetime.utcnow() + timedelta(minutes=expire_minutes)
        
        payload = {
            "user_id": user_data["user_id"],
            "steam_id": user_data["steam_id"],
            "username": user_data["username"],
            "user_type": user_data["user_type"],
            "is_admin": user_data.get("is_admin", False),
            "is_super_admin": user_data.get("is_super_admin", False),
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user_id: int) -> str:
        """
        创建刷新令牌
        
        Args:
            user_id: 用户ID
            
        Returns:
            str: JWT 刷新令牌
        """
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        payload = {
            "user_id": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        验证令牌
        
        Args:
            token: JWT 令牌
            
        Returns:
            Optional[Dict]: 解码后的载荷，验证失败返回 None
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def decode_token(self, token: str) -> Dict[str, Any]:
        """
        解码令牌（不验证过期时间）
        
        Args:
            token: JWT 令牌
            
        Returns:
            Dict: 解码后的载荷
            
        Raises:
            HTTPException: 令牌无效时抛出异常
        """
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                options={"verify_exp": False}
            )
            return payload
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def refresh_access_token(self, refresh_token: str, user_data: Dict[str, Any]) -> Optional[str]:
        """
        使用刷新令牌生成新的访问令牌
        
        Args:
            refresh_token: 刷新令牌
            user_data: 用户数据
            
        Returns:
            Optional[str]: 新的访问令牌，失败返回 None
        """
        payload = self.verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None
        
        return self.create_access_token(user_data)


class JWTBearer(HTTPBearer):
    """JWT Bearer 认证"""
    
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)
        self.jwt_handler = JWTHandler()
    
    async def __call__(self, request: Request) -> Optional[Dict[str, Any]]:
        # 跳过OPTIONS预检请求的认证检查
        if request.method == "OPTIONS":
            return {"skip_auth": True, "method": "OPTIONS"}

        try:
            credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        except HTTPException as e:
            # 将403错误转换为401错误
            if e.status_code == 403:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="缺少认证令牌",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            raise e

        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="无效的认证方案",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            payload = self.jwt_handler.verify_token(credentials.credentials)
            if not payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="令牌已过期或无效",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            if payload.get("type") != "access":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="无效的令牌类型",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            return payload
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="缺少认证令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )


# 全局实例
jwt_handler = JWTHandler()
jwt_bearer = JWTBearer()


# 权限检查依赖项
def require_admin(current_user: Dict[str, Any] = Depends(jwt_bearer)) -> Dict[str, Any]:
    """
    检查管理员权限

    Args:
        current_user: JWT 载荷

    Returns:
        Dict: 用户信息

    Raises:
        HTTPException: 权限不足时抛出异常
    """
    # 跳过OPTIONS预检请求的权限检查
    if current_user and current_user.get("skip_auth") and current_user.get("method") == "OPTIONS":
        return current_user

    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


def require_super_admin(current_user: Dict[str, Any] = Depends(jwt_bearer)) -> Dict[str, Any]:
    """
    检查超级管理员权限

    Args:
        current_user: JWT 载荷

    Returns:
        Dict: 用户信息

    Raises:
        HTTPException: 权限不足时抛出异常
    """
    # 跳过OPTIONS预检请求的权限检查
    if current_user and current_user.get("skip_auth") and current_user.get("method") == "OPTIONS":
        return current_user

    if not current_user.get("is_super_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限"
        )
    return current_user


def check_user_or_admin(payload: Dict[str, Any], target_user_id: int) -> Dict[str, Any]:
    """
    检查是否为目标用户本人或管理员

    Args:
        payload: JWT 载荷
        target_user_id: 目标用户ID

    Returns:
        Dict: 用户信息

    Raises:
        HTTPException: 权限不足时抛出异常
    """
    current_user_id = payload.get("user_id")
    is_admin = payload.get("is_admin", False)

    if current_user_id != target_user_id and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只能访问自己的信息或需要管理员权限"
        )

    return payload
