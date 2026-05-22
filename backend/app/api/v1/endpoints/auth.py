from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, get_current_user
from app.schemas.schemas import UserCreate, LoginRequest, AuthResponse, UserResponse, PasswordChangeRequest, PasswordResetRequest, PasswordResetConfirmRequest
from app.models.models import User, UserRole
from datetime import datetime, timezone
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

router = APIRouter()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        name=user_data.name,
        role=UserRole.VIEWER  # Use enum instead of string
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Generate tokens
    access_token = create_access_token(data={"sub": str(new_user.id), "type": "human"})
    refresh_token = create_refresh_token(data={"sub": str(new_user.id)})
    
    return AuthResponse(
        user=UserResponse.model_validate(new_user),
        tokens={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": 1800
        }
    )


@router.post("/login", response_model=AuthResponse)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    # Find user
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    
    # Update last login
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    
    # Generate tokens
    access_token = create_access_token(data={"sub": str(user.id), "type": "human"})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return AuthResponse(
        user=UserResponse.model_validate(user),
        tokens={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": 1800
        }
    )


@router.post("/change-password", status_code=status.HTTP_200_OK)
def change_password(
    request: PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    修改当前用户密码
    需要验证旧密码
    """
    
    # Verify old password
    if not verify_password(request.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Validate new password strength
    if len(request.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters long"
        )
    
    # Hash and update password
    hashed_password = get_password_hash(request.new_password)
    current_user.password_hash = hashed_password
    current_user.updated_at = datetime.now(timezone.utc)
    db.commit()
    
    return {"message": "Password changed successfully"}


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
def forgot_password(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    请求重置密码（发送验证码到邮箱）
    """
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        # Don't reveal if email exists or not for security
        return {"message": "If the email exists, a verification code has been sent"}
    
    # Generate verification code (6 digits)
    verification_code = secrets.randbelow(900000) + 100000
    
    # Store verification code in user metadata with expiration (15 minutes)
    from datetime import timedelta
    expiry_time = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    # In production, you should use Redis or a dedicated table for verification codes
    # For now, we'll store it in user's custom_metadata
    user.custom_metadata = user.custom_metadata or {}
    user.custom_metadata['password_reset_code'] = str(verification_code)
    user.custom_metadata['password_reset_expiry'] = expiry_time.isoformat()
    db.commit()
    
    # Send email with verification code
    try:
        send_password_reset_email(request.email, verification_code)
        
        # In development mode (or if ENVIRONMENT not set), also return the code for convenience
        import os
        environment = os.getenv("ENVIRONMENT", "development")
        if environment == "development":
            return {
                "message": "Verification code sent to your email",
                "code": verification_code
            }
        
        return {"message": "Verification code sent to your email"}
    except Exception as e:
        # In development, return the code directly even if email fails
        import os
        environment = os.getenv("ENVIRONMENT", "development")
        if environment == "development":
            return {
                "message": f"Development mode - Verification code: {verification_code}",
                "code": verification_code
            }
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email"
        )


@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(
    request: PasswordResetConfirmRequest,
    db: Session = Depends(get_db)
):
    """
    使用验证码重置密码
    """
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or verification code"
        )
    
    # Verify the code
    metadata = user.custom_metadata or {}
    stored_code = metadata.get('password_reset_code')
    expiry_str = metadata.get('password_reset_expiry')
    
    if not stored_code or not expiry_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending password reset request"
        )
    
    # Check if code has expired
    expiry_time = datetime.fromisoformat(expiry_str)
    if datetime.now(timezone.utc) > expiry_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code has expired"
        )
    
    # Verify code matches
    if str(request.verification_code) != stored_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )
    
    # Validate new password strength
    if len(request.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters long"
        )
    
    # Update password
    hashed_password = get_password_hash(request.new_password)
    user.password_hash = hashed_password
    user.updated_at = datetime.now(timezone.utc)
    
    # Clear verification code from metadata
    # Need to create a new dict to trigger SQLAlchemy change detection
    if user.custom_metadata:
        new_metadata = user.custom_metadata.copy()
        new_metadata.pop('password_reset_code', None)
        new_metadata.pop('password_reset_expiry', None)
        user.custom_metadata = new_metadata
    else:
        user.custom_metadata = {}
    
    db.commit()
    
    return {"message": "Password reset successfully"}


def send_password_reset_email(email: str, code: int):
    """
    发送密码重置验证码邮件
    使用系统配置的SMTP服务器
    """
    import os
    
    # ✅ 从数据库读取邮件配置
    smtp_server = None
    smtp_port = None
    smtp_user = None
    smtp_password = None
    from_email = None
    from_name = "Mercator文档库"
    
    try:
        from app.models.system_config import SystemConfig, ConfigKeys
        from app.core.database import SessionLocal
        
        db = SessionLocal()
        configs = db.query(SystemConfig).filter(
            SystemConfig.category == 'email'
        ).all()
        
        for config in configs:
            key = config.key.replace('email.', '')
            value = config.get_value()
            
            if key == 'smtp_server':
                smtp_server = value
            elif key == 'smtp_port':
                smtp_port = int(value) if value else 587
            elif key == 'smtp_user':
                smtp_user = value
            elif key == 'smtp_password':
                smtp_password = value
            elif key == 'from_email':
                from_email = value
            elif key == 'from_name':
                from_name = value if value else "Mercator文档库"
        
        db.close()
    except Exception as e:
        print(f"⚠️  Failed to load email config from database: {e}")
    
    # Fallback to environment variables (if database has no config)
    if not smtp_server:
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER", "")
        smtp_password = os.getenv("SMTP_PASSWORD", "")
        from_email = os.getenv("FROM_EMAIL", smtp_user)
    
    # If still no configuration, log and return (development mode)
    if not smtp_server or not smtp_user or not smtp_password:
        print(f"[EMAIL] Password reset code for {email}: {code}")
        print("[EMAIL] SMTP not configured, running in development mode")
        return
    
    # Build email message
    msg = MIMEMultipart()
    msg['From'] = f"{from_name} <{from_email}>"
    msg['To'] = email
    msg['Subject'] = '密码重置验证码 - Mercator文档库'
    
    body = f"""
    您好，
    
    您正在请求重置Mercator文档库的密码。
    
    您的验证码是：{code}
    
    此验证码将在15分钟后过期。
    
    如果您没有请求重置密码，请忽略此邮件。
    
    祝好，
    Mercator团队
    """
    
    msg.attach(MIMEText(body, 'plain'))
    
    # Send email
    try:
        # Choose connection method based on port
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
            if smtp_port == 587:
                server.ehlo()
                server.starttls()
                server.ehlo()
        
        server.login(smtp_user, smtp_password)
        server.sendmail(from_email, email, msg.as_string())
        server.quit()
        
        print(f"[EMAIL] Password reset email sent successfully to {email}")
        
    except Exception as e:
        print(f"[EMAIL] Failed to send email: {e}")
        raise
