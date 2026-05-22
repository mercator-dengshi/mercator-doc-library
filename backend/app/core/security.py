from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.database import get_db
from app.models.models import User, AIAgent, AIAgentStatus
import hashlib

settings = get_settings()
# Use bcrypt with proper version handling
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user from JWT token.
    Raises HTTPException if token is invalid or user not found.
    """
    token = credentials.credentials
    
    # Decode and validate token
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract user ID from token
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )
    
    return user


def get_current_active_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to check if current user is an admin.
    """
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Admin access required.",
        )
    return current_user


def get_current_active_editor(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to check if current user is an editor or admin.
    """
    if current_user.role.value not in ["admin", "editor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Editor access required.",
        )
    return current_user


def get_current_agent(
    x_api_key: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> AIAgent:
    """
    ✅ 通过API密钥认证AI智能体(如OpenClaw等外部工具)
    
    使用方式:
    - Header: X-API-Key: sk-live-xxxxx
    
    Args:
        x_api_key: API密钥(从Header中获取)
        db: 数据库会话
    
    Returns:
        AIAgent: 认证的AI智能体对象
    
    Raises:
        HTTPException: 如果API密钥无效或智能体被禁用
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required",
            headers={"WWW-Authenticate": "X-API-Key"},
        )
    
    # Hash the provided API key for comparison
    api_key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
    
    # Query agent by hashed API key
    agent = db.query(AIAgent).filter(
        AIAgent.api_key_hash == api_key_hash,
        AIAgent.status == AIAgentStatus.ACTIVE
    ).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key",
            headers={"WWW-Authenticate": "X-API-Key"},
        )
    
    # Update last active timestamp
    agent.last_active_at = datetime.utcnow()
    db.commit()
    
    return agent
