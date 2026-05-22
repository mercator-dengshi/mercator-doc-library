import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, Text, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    avatar_url = Column(String(500))
    role = Column(SQLEnum(UserRole), default=UserRole.VIEWER, nullable=False)
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    ai_enabled = Column(Boolean, default=False)  # AI助手使用权限
    last_login_at = Column(DateTime(timezone=True))
    custom_metadata = Column(JSONB, default=dict)  # Store verification codes and other metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    documents = relationship("Document", back_populates="author", foreign_keys="Document.author_id")
    sessions = relationship("Session", back_populates="user")


class Category(Base):
    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"))
    icon = Column(String(50))
    sort_order = Column(Integer, default=0)
    is_visible = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    parent = relationship("Category", remote_side=[id], backref="children")
    documents = relationship("Document", back_populates="category")


class Tag(Base):
    __tablename__ = "tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False, index=True)
    slug = Column(String(50), unique=True, nullable=False, index=True)
    color = Column(String(7), default="#3B82F6")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    documents = relationship("DocumentTag", back_populates="tag")


class DocumentStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class EditorType(str, enum.Enum):
    HUMAN = "human"
    AI = "ai"


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    content = Column(Text, nullable=False)
    excerpt = Column(Text)
    version = Column(Integer, default=1, nullable=False)
    
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), index=True)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    last_editor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    last_editor_type = Column(SQLEnum(EditorType), default=EditorType.HUMAN)
    
    is_public = Column(Boolean, default=True, index=True)
    ai_editable = Column(Boolean, default=False, index=True)
    
    # Custom metadata stored as JSON
    custom_metadata = Column("metadata", JSON, default=dict)
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.PUBLISHED, index=True)
    
    published_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, index=True)
    deleted_at = Column(DateTime(timezone=True), index=True)

    # Relationships
    category = relationship("Category", back_populates="documents")
    author = relationship("User", back_populates="documents", foreign_keys=[author_id])
    last_editor = relationship("User", foreign_keys=[last_editor_id])
    tags = relationship("DocumentTag", back_populates="document")
    edit_history = relationship("EditHistory", back_populates="document", order_by="EditHistory.version")


class DocumentTag(Base):
    __tablename__ = "document_tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    tag_id = Column(UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="tags")
    tag = relationship("Tag", back_populates="documents")


class EditHistory(Base):
    __tablename__ = "edit_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    content_snapshot = Column(Text, nullable=False)
    title_snapshot = Column(String(255))
    
    editor_type = Column(SQLEnum(EditorType), nullable=False)
    editor_id = Column(String(255), nullable=False)
    editor_name = Column(String(100))
    
    change_summary = Column(Text)
    diff_data = Column(JSON)
    metadata_snapshot = Column(JSON)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)

    # Relationships
    document = relationship("Document", back_populates="edit_history")


class AIAgentStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"


class AIAgent(Base):
    __tablename__ = "ai_agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    api_key_hash = Column(String(255), unique=True, nullable=False, index=True)
    api_key_prefix = Column(String(20))
    
    permissions = Column(JSON, default=dict)
    
    status = Column(SQLEnum(AIAgentStatus), default=AIAgentStatus.ACTIVE, index=True)
    is_verified = Column(Boolean, default=False)
    
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    
    total_edits = Column(Integer, default=0)
    last_active_at = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    refresh_token_hash = Column(String(255), nullable=False)
    access_token_jti = Column(String(255), unique=True)
    
    device_name = Column(String(100))
    ip_address = Column(INET)
    user_agent = Column(Text)
    
    is_active = Column(Boolean, default=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    last_used_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="sessions")
