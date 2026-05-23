from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, get_current_user
from app.schemas.schemas import UserCreate, LoginRequest, AuthResponse, UserResponse, PasswordChangeRequest, PasswordResetRequest, PasswordResetConfirmRequest
from app.models.models import User, UserRole
from datetime import datetime, timezone
import secrets
import smtplib
import email.utils
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
    print(f"\n{'='*80}")
    print(f"[FORGOT_PASSWORD] {'='*80}")
    print(f"[FORGOT_PASSWORD] Request received at: {datetime.now(timezone.utc).isoformat()}")
    print(f"[FORGOT_PASSWORD] Email: {request.email}")
    
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        # Don't reveal if email exists or not for security
        print(f"[FORGOT_PASSWORD] User not found (security: returning success anyway)")
        return {"message": "If the email exists, a verification code has been sent"}
    
    # Generate verification code (6 digits)
    verification_code = secrets.randbelow(900000) + 100000
    print(f"[FORGOT_PASSWORD] Generated code: {verification_code}")
    
    # Store verification code in user metadata with expiration (15 minutes)
    from datetime import timedelta
    expiry_time = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    # ️ IMPORTANT: SQLAlchemy JSONB fields require creating a new dict object
    # to trigger change detection. Direct modification won't work!
    old_metadata = user.custom_metadata.copy() if user.custom_metadata else {}
    print(f"[FORGOT_PASSWORD] Old metadata: {old_metadata}")
    
    # Create a NEW dictionary (not modify in place)
    new_metadata = dict(old_metadata)  # Copy existing metadata
    new_metadata['password_reset_code'] = str(verification_code)
    new_metadata['password_reset_expiry'] = expiry_time.isoformat()
    
    # Assign the new dict to trigger SQLAlchemy change detection
    user.custom_metadata = new_metadata
    db.commit()
    db.refresh(user)  # Refresh to ensure we have the latest data
    print(f"[FORGOT_PASSWORD] Saved to DB - Code: {user.custom_metadata['password_reset_code']}, Expiry: {user.custom_metadata['password_reset_expiry']}")
    
    # Verify immediately after commit
    user_check = db.query(User).filter(User.email == request.email).first()
    check_metadata = user_check.custom_metadata or {}
    print(f"[FORGOT_PASSWORD] Verification read-back - Code: {check_metadata.get('password_reset_code')}, Expiry: {check_metadata.get('password_reset_expiry')}")
    
    # Send email with verification code
    try:
        print(f"[FORGOT_PASSWORD] Sending email with code: {verification_code}")
        send_password_reset_email(request.email, verification_code)
        print(f"[FORGOT_PASSWORD] Email sent successfully")
        
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
    print(f"\n{'='*80}")
    print(f"[RESET_PASSWORD] {'='*80}")
    print(f"[RESET_PASSWORD] Request received at: {datetime.now(timezone.utc).isoformat()}")
    
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        print(f"[RESET_PASSWORD] User not found for email: {request.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or verification code"
        )
    
    # Verify the code
    # First, refresh the user to get the latest data from database
    db.refresh(user)
    metadata = user.custom_metadata or {}
    stored_code = metadata.get('password_reset_code')
    expiry_str = metadata.get('password_reset_expiry')
    
    print(f"[RESET_PASSWORD] Email: {request.email}")
    print(f"[RESET_PASSWORD] Received code: {request.verification_code}")
    print(f"[RESET_PASSWORD] Stored code: {stored_code}")
    print(f"[RESET_PASSWORD] Expiry: {expiry_str}")
    print(f"[RESET_PASSWORD] Full metadata: {metadata}")
    
    if not stored_code or not expiry_str:
        print(f"[RESET_PASSWORD] No pending password reset request")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending password reset request"
        )
    
    # Check if code has expired
    try:
        expiry_time = datetime.fromisoformat(expiry_str)
        print(f"[RESET_PASSWORD] Current time (UTC): {datetime.now(timezone.utc)}")
        print(f"[RESET_PASSWORD] Expiry time: {expiry_time}")
        print(f"[RESET_PASSWORD] Is expired: {datetime.now(timezone.utc) > expiry_time}")
        
        if datetime.now(timezone.utc) > expiry_time:
            print(f"[RESET_PASSWORD] Verification code has expired")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification code has expired"
            )
    except Exception as e:
        print(f"[RESET_PASSWORD] Error parsing expiry time: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code format"
        )
    
    # Verify code matches
    if str(request.verification_code) != stored_code:
        print(f"[RESET_PASSWORD] Code mismatch! Received: {request.verification_code}, Stored: {stored_code}")
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
        from_name = os.getenv("FROM_NAME", "Mercator文档库")
    
    # If still no configuration, log and return (development mode)
    if not smtp_server or not smtp_user or not smtp_password:
        print(f"[EMAIL] Password reset code for {email}: {code}")
        print("[EMAIL] SMTP not configured, running in development mode")
        return
    
    # Build email message
    msg = MIMEMultipart()
    
    # ✅ 确保 From 字段格式正确
    print(f"[EMAIL DEBUG] Raw from_email: {from_email}")
    print(f"[EMAIL DEBUG] Raw from_name: {from_name}")
    print(f"[EMAIL DEBUG] Raw smtp_user: {smtp_user}")
    
    # Priority: from_email config > smtp_user
    actual_from_email = from_email if from_email else smtp_user
    actual_from_name = from_name if from_name else "Mercator文档库"
    
    # Format: "Name <email>"
    if actual_from_email:
        msg['From'] = f"{actual_from_name} <{actual_from_email}>"
    else:
        # Absolute fallback
        msg['From'] = f"{actual_from_name} <noreply@mercator.cn>"
    
    msg['To'] = email
    msg['Subject'] = '密码重置验证码 - Mercator文档库'
    msg['Reply-To'] = actual_from_email  # Add Reply-To header
    msg['Date'] = email.utils.formatdate(localtime=True)  # Add Date header
    
    print(f"[EMAIL DEBUG] Final From: {msg['From']}")
    print(f"[EMAIL DEBUG] Reply-To: {msg['Reply-To']}")
    print(f"[EMAIL DEBUG] To: {msg['To']}")
    print(f"[EMAIL DEBUG] Subject: {msg['Subject']}")
    
    # Build HTML and plain text versions
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #2563eb;">密码重置验证码</h2>
            <p>您好，</p>
            <p>您正在请求重置 Mercator 文档库的密码。</p>
            <div style="background-color: #f3f4f6; padding: 15px; border-radius: 5px; margin: 20px 0; text-align: center;">
                <h1 style="margin: 0; color: #2563eb; font-size: 32px; letter-spacing: 5px;">{code}</h1>
            </div>
            <p>此验证码将在 <strong>15分钟</strong> 后过期。</p>
            <p style="color: #6b7280; font-size: 14px;">如果您没有请求重置密码，请忽略此邮件。</p>
            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
            <p style="color: #6b7280; font-size: 12px;">此邮件由系统自动发送，请勿回复。</p>
            <p style="color: #6b7280; font-size: 12px;">Mercator 文档库团队</p>
        </div>
    </body>
    </html>
    """
    
    plain_body = f"""
您好，

您正在请求重置 Mercator 文档库的密码。

您的验证码是：{code}

此验证码将在 15分钟 后过期。

如果您没有请求重置密码，请忽略此邮件。

祝好，
Mercator 文档库团队
    """
    
    # Attach both HTML and plain text versions
    msg.attach(MIMEText(plain_body, 'plain', 'utf-8'))
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))
    
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
