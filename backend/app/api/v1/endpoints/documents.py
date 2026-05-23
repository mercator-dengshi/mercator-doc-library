from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.core.database import get_db
from app.core.security import get_current_user, get_current_active_editor, get_current_agent
from app.schemas.schemas import DocumentCreate, DocumentUpdate, DocumentResponse, DocumentListItem
from app.models.models import Document, User, Category, Tag, DocumentTag, EditorType, DocumentStatus, AIAgent
from datetime import datetime, timezone

router = APIRouter()


def get_editor_from_api_key_or_token(
    x_api_key: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    ✅ 从API密钥或JWT Token获取编辑者
    
    优先级:
    1. X-API-Key (外部智能体)
    2. Authorization Bearer Token (人类用户)
    
    Returns: dict with 'type' ('agent' or 'user') and 'id'
    """
    # Try API key first
    if x_api_key:
        try:
            from app.core.security import get_current_agent
            agent = get_current_agent(x_api_key=x_api_key, db=db)
            return {"type": "agent", "id": agent.id, "obj": agent}
        except HTTPException:
            pass
    
    # Fallback to JWT token
    if authorization and authorization.startswith("Bearer "):
        from app.core.security import security, decode_token
        token = authorization.replace("Bearer ", "")
        payload = decode_token(token)
        if payload:
            user_id = payload.get("sub")
            user = db.query(User).filter(User.id == user_id).first()
            if user and user.is_active:
                return {"type": "user", "id": user.id, "obj": user}
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Use X-API-Key or Authorization header."
    )


@router.get("/", response_model=List[DocumentListItem])
def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,  # Changed from UUID to str to accept slug
    db: Session = Depends(get_db)
):
    """List documents with optional category filter (accepts category slug or UUID)"""
    query = db.query(Document).filter(Document.deleted_at.is_(None))
    
    if category:
        # Try to find category by slug first, then by UUID
        cat_by_slug = db.query(Category).filter(Category.slug == category).first()
        if cat_by_slug:
            query = query.filter(Document.category_id == cat_by_slug.id)
        else:
            # Try as UUID
            try:
                from uuid import UUID
                cat_uuid = UUID(category)
                query = query.filter(Document.category_id == cat_uuid)
            except ValueError:
                # Invalid UUID format, return empty results
                return []
    
    # Eager load relationships to avoid N+1 queries
    from sqlalchemy.orm import joinedload
    query = query.options(
        joinedload(Document.author),
        joinedload(Document.category)
    )
    
    documents = query.offset(skip).limit(limit).all()
    return documents


@router.get("/trash", response_model=List[DocumentListItem])
def list_trashed_documents(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List soft-deleted documents (recycle bin)"""
    query = db.query(Document).filter(Document.deleted_at.isnot(None))
    
    # Editors only see their own trashed documents
    # If author_id is NULL (user was deleted), also show these documents
    if current_user.role.value == "editor":
        query = query.filter(
            (Document.author_id == current_user.id) | (Document.author_id.is_(None))
        )
    
    documents = query.order_by(Document.deleted_at.desc()).offset(skip).limit(limit).all()
    return documents


@router.post("/trash/clear", status_code=status.HTTP_204_NO_CONTENT)
def clear_trash(
    editor = Depends(get_editor_from_api_key_or_token),
    db: Session = Depends(get_db)
):
    """
    ✅ 清空回收站(仅管理员)
    
    支持两种认证方式:
    - JWT Token (人类用户): Authorization: Bearer xxx
    - API Key (外部智能体): X-API-Key: sk-live-xxx
    """
    # Admin only check
    if editor['type'] == 'user':
        user = editor['obj']
        if user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can clear trash"
            )
    else:
        # Agents cannot clear trash
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AI agents cannot clear trash"
        )
    
    trashed_docs = db.query(Document).filter(Document.deleted_at.isnot(None)).all()
    
    for doc in trashed_docs:
        db.delete(doc)
    
    db.commit()
    
    return None


@router.get("/{doc_slug}", response_model=DocumentResponse)
def get_document(doc_slug: str, db: Session = Depends(get_db)):
    from sqlalchemy.orm import joinedload
    
    document = db.query(Document).options(
        joinedload(Document.author),
        joinedload(Document.category),
        joinedload(Document.last_editor)
    ).filter(
        Document.slug == doc_slug,
        Document.deleted_at.is_(None)
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return document


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def create_document(
    doc_data: DocumentCreate,
    editor = Depends(get_editor_from_api_key_or_token),
    db: Session = Depends(get_db)
):
    """
    ✅ 创建文档
    
    支持两种认证方式:
    - JWT Token (人类用户): Authorization: Bearer xxx
    - API Key (外部智能体): X-API-Key: sk-live-xxx
    """
    # Check if slug already exists
    existing = db.query(Document).filter(Document.slug == doc_data.slug).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slug already exists"
        )
    
    # Determine editor type and ID
    editor_id = editor['id']
    editor_type = EditorType.AI if editor['type'] == 'agent' else EditorType.HUMAN
    
    # For agents, we need to get the owner_id
    author_id = editor_id
    last_editor_id_for_db = None  # 默认值
    
    if editor['type'] == 'agent':
        # Agent编辑: author_id使用owner_id, last_editor_id设为None(因为agent不在users表中)
        author_id = editor['obj'].owner_id or editor_id
        last_editor_id_for_db = None  # AI agent不在users表中,不能设置last_editor_id
    else:
        # Human编辑: 使用user ID
        last_editor_id_for_db = editor_id
    
    # Create document
    new_doc = Document(
        title=doc_data.title,
        slug=doc_data.slug,
        content=doc_data.content,
        excerpt=doc_data.content[:200] if doc_data.content else None,
        category_id=doc_data.category_id,
        author_id=author_id,
        last_editor_id=last_editor_id_for_db,  # ✅ 修复: AI agent时为None
        last_editor_type=editor_type,
        custom_metadata=doc_data.metadata,
        is_public=doc_data.is_public,
        ai_editable=doc_data.ai_editable,
        status=DocumentStatus.PUBLISHED,
        published_at=datetime.now(timezone.utc)
    )
    
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)
    
    return new_doc


@router.put("/{doc_id}", response_model=DocumentResponse)
def update_document(
    doc_id: UUID,
    doc_data: DocumentUpdate,
    editor = Depends(get_editor_from_api_key_or_token),
    db: Session = Depends(get_db)
):
    """
    ✅ 更新文档
    
    支持两种认证方式:
    - JWT Token (人类用户): Authorization: Bearer xxx
    - API Key (外部智能体): X-API-Key: sk-live-xxx
    """
    document = db.query(Document).filter(
        Document.id == doc_id,
        Document.deleted_at.is_(None)
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Determine editor type and ID
    editor_id = editor['id']
    editor_type = EditorType.AI if editor['type'] == 'agent' else EditorType.HUMAN
    
    # For agents, last_editor_id should be None (agents are not in users table)
    last_editor_id_for_db = None if editor['type'] == 'agent' else editor_id
    
    # Permission check
    if editor['type'] == 'user':
        # Human user: admin can edit any, editor can only edit own
        user = editor['obj']
        if user.role.value == "editor" and document.author_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only edit your own documents"
            )
    # For agents, we could add permission checks based on agent.permissions
    
    # Check if document is archived
    if document.status == DocumentStatus.ARCHIVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot edit archived document"
        )
    
    # Version check (optimistic locking)
    if doc_data.version != document.version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Version conflict. Current version: {document.version}"
        )
    
    # Update fields
    if doc_data.title:
        document.title = doc_data.title
    if doc_data.content:
        document.content = doc_data.content
        document.excerpt = doc_data.content[:200]
    if doc_data.metadata:
        document.custom_metadata = doc_data.metadata
    
    # Update editor info
    document.last_editor_id = last_editor_id_for_db  # ✅ 修复: AI agent时为None
    document.last_editor_type = editor_type
    
    # Increment version
    document.version += 1
    document.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(document)
    
    return document


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    doc_id: UUID,
    editor = Depends(get_editor_from_api_key_or_token),
    db: Session = Depends(get_db)
):
    """
    ✅ 软删除文档(移入回收站)
    
    支持两种认证方式:
    - JWT Token (人类用户): Authorization: Bearer xxx
    - API Key (外部智能体): X-API-Key: sk-live-xxx
    """
    document = db.query(Document).filter(
        Document.id == doc_id,
        Document.deleted_at.is_(None)
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Permission check
    if editor['type'] == 'user':
        # Human user: admin can delete any, editor can only delete own
        user = editor['obj']
        if user.role.value == "editor":
            if document.author_id is not None and document.author_id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only delete your own documents"
                )
    # For agents, we could add permission checks based on agent.permissions
    
    # Soft delete
    document.deleted_at = datetime.now(timezone.utc)
    document.status = DocumentStatus.ARCHIVED
    db.commit()
    
    return None


@router.post("/{doc_id}/restore", response_model=DocumentResponse)
def restore_document(
    doc_id: UUID,
    editor = Depends(get_editor_from_api_key_or_token),
    db: Session = Depends(get_db)
):
    """
    ✅ 恢复已删除的文档
    
    支持两种认证方式:
    - JWT Token (人类用户): Authorization: Bearer xxx
    - API Key (外部智能体): X-API-Key: sk-live-xxx
    """
    document = db.query(Document).filter(
        Document.id == doc_id,
        Document.deleted_at.isnot(None)
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found in trash"
        )
    
    # Permission check
    if editor['type'] == 'user':
        user = editor['obj']
        if user.role.value == "editor" and document.author_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only restore your own documents"
            )
    
    # Restore
    document.deleted_at = None
    document.status = DocumentStatus.PUBLISHED
    db.commit()
    db.refresh(document)
    
    return document


@router.delete("/{doc_id}/permanent", status_code=status.HTTP_204_NO_CONTENT)
def permanent_delete_document(
    doc_id: UUID,
    editor = Depends(get_editor_from_api_key_or_token),
    db: Session = Depends(get_db)
):
    """
    ✅ 永久删除文档(仅管理员)
    
    支持两种认证方式:
    - JWT Token (人类用户): Authorization: Bearer xxx
    - API Key (外部智能体): X-API-Key: sk-live-xxx
    """
    # Admin only check
    if editor['type'] == 'user':
        user = editor['obj']
        if user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can permanently delete documents"
            )
    else:
        # Agents cannot permanently delete
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AI agents cannot permanently delete documents"
        )
    
    document = db.query(Document).filter(Document.id == doc_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Hard delete
    db.delete(document)
    db.commit()
    
    return None
