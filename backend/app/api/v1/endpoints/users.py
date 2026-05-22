from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_active_admin
from app.models.models import User, UserRole
from app.schemas.schemas import UserResponse, UserRoleUpdate

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """List all users (admin only)"""
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Get user by ID (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: UUID,
    role_data: UserRoleUpdate,
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Update user role (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent demoting yourself
    if user.id == current_user.id and role_data.role != UserRole.ADMIN:
        raise HTTPException(status_code=400, detail="Cannot demote yourself")
    
    user.role = role_data.role
    db.commit()
    db.refresh(user)
    
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: UUID,
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Delete user (admin only)
    
    Note: Before deleting, all documents by this user will have their author_id set to NULL.
    This is because documents should not be deleted when a user is removed.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent deleting yourself
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    # Handle documents authored by this user
    from app.models.models import Document
    documents = db.query(Document).filter(Document.author_id == user_id).all()
    for doc in documents:
        doc.author_id = None  # Set to NULL instead of deleting documents
    
    db.delete(user)
    db.commit()
    
    return None

@router.put("/{user_id}/ai-permission", response_model=UserResponse)
def update_user_ai_permission(
    user_id: UUID,
    ai_enabled: bool,
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Update user AI assistant permission (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.ai_enabled = ai_enabled
    db.commit()
    db.refresh(user)
    
    return user
