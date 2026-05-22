from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_active_editor, get_current_active_admin, get_current_user
from app.models.models import Category, User, Document
from app.schemas.schemas import CategoryCreate, CategoryUpdate, CategoryResponse

router = APIRouter()

@router.get("/", response_model=List[CategoryResponse])
def list_categories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all categories with document count (public)"""
    categories = db.query(Category).offset(skip).limit(limit).all()
    
    # Add document count to each category
    for category in categories:
        category.document_count = db.query(Document).filter(
            Document.category_id == category.id,
            Document.deleted_at.is_(None)
        ).count()
    
    return categories

@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: UUID,
    db: Session = Depends(get_db)
):
    """Get category by ID (public)"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Create a new category (admin only)"""
    # Check if category with same slug already exists
    existing = db.query(Category).filter(Category.slug == category_data.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category with this slug already exists")
    
    new_category = Category(
        name=category_data.name,
        slug=category_data.slug,
        description=category_data.description,
        parent_id=category_data.parent_id,
        icon=category_data.icon
    )
    
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    
    new_category.document_count = 0
    return new_category

@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: UUID,
    category_data: CategoryUpdate,
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Update category (admin only)"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Update fields
    if category_data.name is not None:
        category.name = category_data.name
    if category_data.slug is not None:
        # Check slug uniqueness
        existing = db.query(Category).filter(
            Category.slug == category_data.slug,
            Category.id != category_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Category with this slug already exists")
        category.slug = category_data.slug
    if category_data.description is not None:
        category.description = category_data.description
    if category_data.parent_id is not None:
        category.parent_id = category_data.parent_id
    if category_data.icon is not None:
        category.icon = category_data.icon
    if category_data.sort_order is not None:
        category.sort_order = category_data.sort_order
    if category_data.is_visible is not None:
        category.is_visible = category_data.is_visible
    
    db.commit()
    db.refresh(category)
    
    # Add document count
    category.document_count = db.query(Document).filter(
        Document.category_id == category.id,
        Document.deleted_at.is_(None)
    ).count()
    
    return category

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: UUID,
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Delete category (admin only)"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Check if category has active documents
    active_docs_count = db.query(Document).filter(
        Document.category_id == category_id,
        Document.deleted_at.is_(None)
    ).count()
    
    if active_docs_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete category with {active_docs_count} active documents. Move or delete documents first."
        )
    
    # Check for child categories
    if category.children:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete category with child categories. Delete children first."
        )
    
    db.delete(category)
    db.commit()
    
    return None
