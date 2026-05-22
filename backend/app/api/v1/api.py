from fastapi import APIRouter
from app.api.v1.endpoints import auth, documents, search, agents, users, categories, config, version

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(documents.router, prefix="/docs", tags=["Documents"])
api_router.include_router(search.router, prefix="/search", tags=["Search"])
api_router.include_router(agents.router, prefix="/agents", tags=["AI Agents"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(categories.router, prefix="/categories", tags=["Categories"])
api_router.include_router(config.router, prefix="/config", tags=["System Configuration"])
api_router.include_router(version.router, prefix="", tags=["Version"])
