from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Any
from datetime import datetime
from uuid import UUID
from app.models.models import UserRole, DocumentStatus, EditorType, AIAgentStatus


# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    avatar_url: Optional[str] = None


class UserResponse(BaseModel):
    id: UUID
    email: str
    name: str
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Auth Schemas
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int


class AuthResponse(BaseModel):
    user: UserResponse
    tokens: TokenResponse


# Password Change Schemas
class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    email: EmailStr
    verification_code: str
    new_password: str = Field(..., min_length=8)


class UserRoleUpdate(BaseModel):
    role: UserRole


# Category Schemas
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    icon: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    icon: Optional[str] = None
    sort_order: Optional[int] = None
    is_visible: Optional[bool] = None


class CategoryResponse(CategoryBase):
    id: UUID
    sort_order: int
    is_visible: bool
    document_count: int = 0
    children: List['CategoryResponse'] = []
    created_at: datetime

    class Config:
        from_attributes = True


# Tag Schemas
class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    slug: str = Field(..., min_length=1, max_length=50)
    color: Optional[str] = "#3B82F6"


class TagResponse(TagBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# Document Schemas
class DocumentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    content: str
    category_id: Optional[UUID] = None
    tags: Optional[List[str]] = []
    metadata: Optional[dict] = {}
    is_public: bool = True
    ai_editable: bool = False


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[dict] = None
    version: int
    change_summary: Optional[str] = None


class DocumentResponse(BaseModel):
    id: UUID
    title: str
    slug: str
    content: str  # Added content field
    excerpt: Optional[str] = None
    version: int
    category: Optional[CategoryResponse] = None
    tags: List[TagResponse] = []
    metadata: dict = Field(default_factory=dict, alias='custom_metadata')
    is_public: bool
    ai_editable: bool
    status: DocumentStatus
    author: Optional[UserResponse] = None
    last_editor: Optional[UserResponse] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class DocumentListItem(BaseModel):
    id: UUID
    title: str
    slug: str
    excerpt: Optional[str] = None
    version: int
    category: Optional[CategoryResponse] = None
    tags: List[str] = []
    updated_at: datetime
    author: Optional[UserResponse] = None

    class Config:
        from_attributes = True


# Edit History Schema
class EditHistoryResponse(BaseModel):
    version: int
    edited_at: datetime
    editor_type: EditorType
    editor_id: str
    editor_name: Optional[str] = None
    change_summary: Optional[str] = None
    diff_url: Optional[str] = None

    class Config:
        from_attributes = True


# AI Agent Schemas
class AIAgentPermissions(BaseModel):
    categories: Optional[List[UUID]] = []
    actions: Optional[List[str]] = ["create", "update"]
    max_edits_per_hour: Optional[int] = 50


class AIAgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    permissions: AIAgentPermissions


class AIAgentResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    api_key: Optional[str] = None  # Only shown once on creation
    api_key_prefix: str
    permissions: AIAgentPermissions
    status: AIAgentStatus
    total_edits: int = 0
    created_at: datetime
    last_active_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# AI Chat Schemas
class AIChatRequest(BaseModel):
    messages: List[dict] = []  # [{"role": "user", "content": "..."}]
    model: Optional[str] = None  # 如果为None,后端将使用配置的默认模型
    document_context: Optional[dict] = None  # {"title": "...", "content": "..."}


class AIChatResponse(BaseModel):
    message: dict  # {"role": "assistant", "content": "..."}
    usage: dict  # {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}


# Search Schema
class SearchResult(BaseModel):
    id: UUID
    title: str
    slug: str
    excerpt: Optional[str] = None
    content_preview: Optional[str] = None  # 匹配的内容片段
    score: float
    match_type: str  # "fulltext" 或 "semantic"
    category: Optional[CategoryResponse] = None
    tags: List[str] = []
    updated_at: datetime


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="搜索查询")
    limit: int = Field(default=20, ge=1, le=50, description="返回结果数量")


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total: int
    suggestions: List[str] = []


# Pagination Schema
class PaginationMeta(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool


# Response Wrapper
class SuccessResponse(BaseModel):
    data: Any
    message: Optional[str] = None
