"""
系统配置管理 API 端点
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.database import get_db
from app.core.security import get_current_active_admin
from app.models.models import User
from app.models.system_config import SystemConfig, ConfigKeys

router = APIRouter()

# ⚠️ SECURITY IMPROVEMENT: Use environment variables instead of JSON files
# Configuration is now loaded from .env.production or system environment


class EmailConfig(BaseModel):
    """邮件服务器配置"""
    smtp_server: str = Field(..., description="SMTP服务器地址")
    smtp_port: int = Field(..., description="SMTP端口", ge=1, le=65535)
    smtp_user: str = Field(..., description="SMTP用户名")
    smtp_password: str = Field(..., description="SMTP密码/授权码")
    from_email: str = Field(..., description="发件人邮箱")
    from_name: str = Field("Mercator文档库", description="发件人名称")


def get_email_config_from_db(db: Session) -> dict:
    """从数据库读取邮件配置（优先使用）"""
    configs = db.query(SystemConfig).filter(
        SystemConfig.category == 'email'
    ).all()
    
    result = {}
    for config in configs:
        key = config.key.replace('email.', '')
        result[key] = config.get_value()
    
    # Fallback到环境变量(如果数据库中没有配置)
    if not result.get('smtp_server'):
        result['smtp_server'] = os.getenv('SMTP_SERVER', '')
        result['smtp_port'] = int(os.getenv('SMTP_PORT', '587'))
        result['smtp_user'] = os.getenv('SMTP_USER', '')
        result['smtp_password'] = os.getenv('SMTP_PASSWORD', '')
        result['from_email'] = os.getenv('FROM_EMAIL', '')
        result['from_name'] = os.getenv('FROM_NAME', 'Mercator文档库')
    
    return result


def save_config(config: dict):
    """
    保存系统配置（⚠️ SECURITY: 不再写入JSON文件，仅设置环境变量）
    
    注意：在生产环境中，应该通过 .env.production 文件或 systemd 服务配置来管理
    """
    # ⚠️ IMPORTANT: 不再保存到 JSON 文件，避免敏感信息泄露
    # 配置应该通过环境变量或数据库管理
    
    # 临时设置环境变量（当前进程有效）
    if 'email' in config:
        email = config['email']
        os.environ['SMTP_SERVER'] = str(email.get('smtp_server', ''))
        os.environ['SMTP_PORT'] = str(email.get('smtp_port', '587'))
        os.environ['SMTP_USER'] = str(email.get('smtp_user', ''))
        os.environ['SMTP_PASSWORD'] = str(email.get('smtp_password', ''))
        os.environ['FROM_EMAIL'] = str(email.get('from_email', ''))
        os.environ['FROM_NAME'] = str(email.get('from_name', 'Mercator文档库'))
    
    if 'ai_providers' in config and config['ai_providers']:
        ai = config['ai_providers'][0]
        os.environ['DEEPSEEK_API_KEY'] = str(ai.get('api_key', ''))
        os.environ['AI_MODEL'] = str(ai.get('model', 'deepseek-chat'))
        os.environ['AI_TEMPERATURE'] = str(ai.get('temperature', '0.7'))
        os.environ['AI_MAX_TOKENS'] = str(ai.get('max_tokens', '1000'))
    
    return True


@router.post("/email-config")
async def save_email_config(
    config: EmailConfig,
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """
    保存邮件服务器配置到数据库
    
    ✅ 配置持久化存储在数据库中,重启后不会丢失
    ✅ 支持多管理员通过仪表盘管理
    ✅ 敏感信息加密存储
    
    需要管理员权限
    """
    try:
        # 定义字段映射
        email_mappings = {
            'smtp_server': ConfigKeys.EMAIL_SMTP_SERVER,
            'smtp_port': ConfigKeys.EMAIL_SMTP_PORT,
            'smtp_user': ConfigKeys.EMAIL_SMTP_USER,
            'smtp_password': ConfigKeys.EMAIL_SMTP_PASSWORD,
            'from_email': ConfigKeys.EMAIL_FROM_EMAIL,
            'from_name': ConfigKeys.EMAIL_FROM_NAME,
        }
        
        # 保存到数据库
        for field, key in email_mappings.items():
            value = getattr(config, field)
            
            # 查询或创建配置记录
            sys_config = db.query(SystemConfig).filter_by(key=key).first()
            if not sys_config:
                sys_config = SystemConfig(
                    id=key,
                    key=key,
                    category='email',
                    description=f"邮件配置: {field}"
                )
                sys_config.created_by = current_user.id
                db.add(sys_config)
            
            # 设置值(自动加密)
            sys_config.set_value(str(value))
            sys_config.updated_by = current_user.id
        
        db.commit()
        
        return {
            "message": "✅ 邮件配置保存成功(已持久化到数据库)",
            "config": {
                "smtp_server": config.smtp_server,
                "smtp_port": config.smtp_port,
                "from_email": config.from_email,
                "from_name": config.from_name
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存配置失败: {str(e)}"
        )


@router.post("/email-config/test")
async def test_email_connection(
    config: EmailConfig,
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """
    测试邮件服务器连接
    
    需要管理员权限
    """
    try:
        # 根据端口选择连接方式
        if config.smtp_port == 465:
            # SSL连接
            server = smtplib.SMTP_SSL(config.smtp_server, config.smtp_port, timeout=10)
        else:
            # 普通连接
            server = smtplib.SMTP(config.smtp_server, config.smtp_port, timeout=10)
            server.ehlo()
            
            # 如果是587端口，启动TLS
            if config.smtp_port == 587:
                server.starttls()
                server.ehlo()
        
        # 尝试登录
        server.login(config.smtp_user, config.smtp_password)
        server.quit()
        
        return {
            "success": True,
            "message": "邮件服务器连接测试成功！",
            "details": {
                "server": config.smtp_server,
                "port": config.smtp_port,
                "user": config.smtp_user
            }
        }
    except smtplib.SMTPAuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="SMTP认证失败，请检查用户名和密码/授权码"
        )
    except smtplib.SMTPConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"无法连接到SMTP服务器 {config.smtp_server}:{config.smtp_port}"
        )
    except smtplib.SMTPException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SMTP错误: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"连接测试失败: {str(e)}"
        )


@router.get("/email-config")
async def get_email_config(
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """
    获取邮件服务器配置
    
    ✅ 从数据库读取配置
    
    需要管理员权限
    """
    email_config = get_email_config_from_db(db)
    
    # 不返回密码
    safe_config = {k: v for k, v in email_config.items() if k != 'smtp_password'}
    safe_config['smtp_password'] = '********' if email_config.get('smtp_password') else ''
    
    return safe_config

