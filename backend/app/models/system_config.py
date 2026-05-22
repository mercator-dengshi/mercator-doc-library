"""
系统配置模型 - 数据库存储
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime
from datetime import datetime
from app.core.database import Base
from cryptography.fernet import Fernet
import os


class SystemConfig(Base):
    """系统配置表 - 加密存储敏感信息"""
    __tablename__ = 'system_configs'
    
    id = Column(String, primary_key=True, index=True)  # 配置键,如 'email.smtp_password'
    key = Column(String, unique=True, nullable=False, index=True)  # 配置键
    category = Column(String, nullable=False, index=True)  # 分类: email, ai, general
    encrypted_value = Column(Text, nullable=True)  # 加密后的值
    is_encrypted = Column(Boolean, default=True)  # 是否加密
    description = Column(Text, nullable=True)  # 配置说明
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String, nullable=True)  # 创建者用户ID
    updated_by = Column(String, nullable=True)  # 更新者用户ID
    
    @staticmethod
    def get_cipher() -> Fernet:
        """获取加密器"""
        encryption_key = os.getenv("ENCRYPTION_KEY")
        if not encryption_key:
            # 如果没有设置环境变量,使用默认密钥(仅开发环境!)
            # 生产环境必须设置ENCRYPTION_KEY环境变量
            encryption_key = "c3VwZXJfc2VjcmV0X2tleV9mb3JfZGV2ZWxvcG1lbnQ="
            print("⚠️  WARNING: Using default encryption key! Set ENCRYPTION_KEY in production!")
        
        return Fernet(encryption_key.encode())
    
    def set_value(self, value: str):
        """加密并设置值"""
        if self.is_encrypted and value:
            cipher = self.get_cipher()
            self.encrypted_value = cipher.encrypt(value.encode()).decode()
        else:
            self.encrypted_value = value
    
    def get_value(self) -> str:
        """解密并获取值"""
        if self.is_encrypted and self.encrypted_value:
            try:
                cipher = self.get_cipher()
                return cipher.decrypt(self.encrypted_value.encode()).decode()
            except Exception as e:
                print(f"❌ Decryption failed: {e}")
                return ""
        return self.encrypted_value or ""
    
    def to_dict(self, include_value: bool = False) -> dict:
        """转换为字典(默认不包含敏感值)"""
        result = {
            "id": self.id,
            "key": self.key,
            "category": self.category,
            "is_encrypted": self.is_encrypted,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_value:
            result["value"] = self.get_value()
        else:
            # 不返回实际值,只显示是否有值
            result["has_value"] = bool(self.encrypted_value)
        
        return result


# 配置键常量
class ConfigKeys:
    """系统配置键常量"""
    # Email配置
    EMAIL_SMTP_SERVER = "email.smtp_server"
    EMAIL_SMTP_PORT = "email.smtp_port"
    EMAIL_SMTP_USER = "email.smtp_user"
    EMAIL_SMTP_PASSWORD = "email.smtp_password"
    EMAIL_FROM_EMAIL = "email.from_email"
    EMAIL_FROM_NAME = "email.from_name"
    
    # AI配置
    AI_PROVIDER = "ai.provider"
    AI_API_KEY = "ai.api_key"
    AI_MODEL = "ai.model"
    AI_BASE_URL = "ai.base_url"
    AI_TEMPERATURE = "ai.temperature"
    AI_MAX_TOKENS = "ai.max_tokens"
