from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.core.database import get_db
from app.core.security import get_current_user, get_current_active_editor
from app.schemas.schemas import DocumentCreate, DocumentUpdate, DocumentResponse, DocumentListItem
from app.models.models import Document, User, Category, Tag, DocumentTag, EditorType, DocumentStatus
from datetime import datetime, timezone

router = APIRouter()


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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clear all trashed documents (admin only, permanent delete)"""
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can clear trash"
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
    current_user: User = Depends(get_current_active_editor),
    db: Session = Depends(get_db)
):
    # Check if slug already exists
    existing = db.query(Document).filter(Document.slug == doc_data.slug).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slug already exists"
        )
    
    # Create document with authenticated user
    new_doc = Document(
        title=doc_data.title,
        slug=doc_data.slug,
        content=doc_data.content,
        excerpt=doc_data.content[:200] if doc_data.content else None,
        category_id=doc_data.category_id,
        author_id=current_user.id,  # Use authenticated user ID
        last_editor_id=current_user.id,
        last_editor_type=EditorType.HUMAN,
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
    current_user: User = Depends(get_current_active_editor),
    db: Session = Depends(get_db)
):
    document = db.query(Document).filter(
        Document.id == doc_id,
        Document.deleted_at.is_(None)
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Permission check: admin can edit any, editor can only edit own
    if current_user.role.value == "editor" and document.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own documents"
        )
    
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
    document.last_editor_id = current_user.id
    document.last_editor_type = EditorType.HUMAN
    
    # Increment version
    document.version += 1
    document.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(document)
    
    return document


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    doc_id: UUID,
    current_user: User = Depends(get_current_active_editor),
    db: Session = Depends(get_db)
):
    """Soft delete a document (move to trash)"""
    document = db.query(Document).filter(
        Document.id == doc_id,
        Document.deleted_at.is_(None)
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Permission check: admin can delete any, editor can only delete own
    # If author_id is NULL (user was deleted), allow deletion
    if current_user.role.value == "editor":
        if document.author_id is not None and document.author_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own documents"
            )
    
    # Soft delete
    document.deleted_at = datetime.now(timezone.utc)
    document.status = DocumentStatus.ARCHIVED
    db.commit()
    
    return None


@router.post("/{doc_id}/restore", response_model=DocumentResponse)
def restore_document(
    doc_id: UUID,
    current_user: User = Depends(get_current_active_editor),
    db: Session = Depends(get_db)
):
    """Restore a soft-deleted document"""
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
    if current_user.role.value == "editor" and document.author_id != current_user.id:
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Permanently delete a document (admin only)"""
    # Admin only
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can permanently delete documents"
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
