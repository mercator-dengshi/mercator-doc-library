from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.core.database import engine, Base
from app.api.v1 import api_router
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


def create_application() -> FastAPI:
    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="A modern documentation platform for humans and AI agents",
    )

    # CORS Middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API Router
    application.include_router(api_router, prefix="/api/v1")

    # Startup event: Auto-migrate database
    @application.on_event("startup")
    async def startup_event():
        try:
            logger.info("检查数据库表结构...")
            # 创建所有表(如果不存在)
            Base.metadata.create_all(bind=engine)
            logger.info("✅ 数据库表结构检查完成")
            
            # 修改documents.author_id允许NULL
            from sqlalchemy import text
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name='documents' AND column_name='author_id'
                """))
                
                row = result.fetchone()
                if row and row[0] == 'NO':
                    logger.info("修改documents.author_id允许NULL...")
                    # 先删除外键约束
                    conn.execute(text("""
                        ALTER TABLE documents 
                        DROP CONSTRAINT IF EXISTS documents_author_id_fkey
                    """))
                    # 修改为允许NULL
                    conn.execute(text("""
                        ALTER TABLE documents 
                        ALTER COLUMN author_id DROP NOT NULL
                    """))
                    # 重新添加外键约束(SET NULL)
                    conn.execute(text("""
                        ALTER TABLE documents 
                        ADD CONSTRAINT documents_author_id_fkey 
                        FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE SET NULL
                    """))
                    conn.commit()
                    logger.info("✅ 成功修改author_id为可空")
                else:
                    logger.info("✅ author_id已经允许NULL")
        except Exception as e:
            logger.error(f"⚠️ 数据库迁移失败: {str(e)}")

    return application


app = create_application()


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "version": settings.APP_VERSION
    }
