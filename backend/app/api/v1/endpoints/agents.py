from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.schemas import AIAgentCreate, AIAgentResponse
from app.models.models import AIAgent, User
import hashlib
import secrets

router = APIRouter()


@router.post("/", response_model=AIAgentResponse, status_code=status.HTTP_201_CREATED)
def create_agent(
    agent_data: AIAgentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ✅ 创建API密钥
    
    为当前用户创建一个新的API密钥，用于外部工具调用文档API
    """
    # Generate API key
    api_key = f"sk-live-{secrets.token_urlsafe(32)}"
    api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    api_key_prefix = api_key[:12] + "..."
    
    # Create agent
    new_agent = AIAgent(
        name=agent_data.name,
        description=agent_data.description,
        api_key_hash=api_key_hash,
        api_key_prefix=api_key_prefix,
        permissions=agent_data.permissions.dict(),
        owner_id=current_user.id  # ✅ 设置所有者
    )
    
    db.add(new_agent)
    db.commit()
    db.refresh(new_agent)
    
    # Return with API key (only shown once)
    response = AIAgentResponse.model_validate(new_agent)
    response.api_key = api_key
    
    return response


@router.get("/", response_model=List[AIAgentResponse])
def list_agents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ✅ 列出当前用户的所有AI智能体
    
    返回该用户创建的所有智能体列表
    """
    agents = db.query(AIAgent).filter(
        AIAgent.owner_id == current_user.id
    ).order_by(AIAgent.created_at.desc()).all()
    
    return agents


@router.get("/{agent_id}", response_model=AIAgentResponse)
def get_agent(agent_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    ✅ 获取智能体详情
    
    只能查看自己创建的智能体
    """
    agent = db.query(AIAgent).filter(
        AIAgent.id == agent_id,
        AIAgent.owner_id == current_user.id
    ).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found or access denied"
        )
    
    return agent


@router.put("/{agent_id}", response_model=AIAgentResponse)
def update_agent(
    agent_id: str,
    agent_data: AIAgentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ✅ 更新智能体配置
    
    可以修改名称、描述、权限等
    """
    agent = db.query(AIAgent).filter(
        AIAgent.id == agent_id,
        AIAgent.owner_id == current_user.id
    ).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found or access denied"
        )
    
    # 更新字段
    agent.name = agent_data.name
    agent.description = agent_data.description
    agent.permissions = agent_data.permissions.dict()
    
    db.commit()
    db.refresh(agent)
    
    return agent


@router.delete("/{agent_id}")
def delete_agent(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ✅ 删除智能体
    
    ⚠️ 删除后API密钥将永久失效
    """
    agent = db.query(AIAgent).filter(
        AIAgent.id == agent_id,
        AIAgent.owner_id == current_user.id
    ).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found or access denied"
        )
    
    db.delete(agent)
    db.commit()
    
    return {"message": "✅ Agent deleted successfully"}


@router.post("/{agent_id}/reset-key", response_model=AIAgentResponse)
def reset_api_key(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ✅ 重置API密钥
    
    ⚠️ 旧密钥立即失效，新密钥仅显示一次
    """
    agent = db.query(AIAgent).filter(
        AIAgent.id == agent_id,
        AIAgent.owner_id == current_user.id
    ).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found or access denied"
        )
    
    # 生成新密钥
    new_api_key = f"sk-live-{secrets.token_urlsafe(32)}"
    new_api_key_hash = hashlib.sha256(new_api_key.encode()).hexdigest()
    new_api_key_prefix = new_api_key[:12] + "..."
    
    # 更新数据库
    agent.api_key_hash = new_api_key_hash
    agent.api_key_prefix = new_api_key_prefix
    
    db.commit()
    db.refresh(agent)
    
    # 返回响应(包含新密钥，仅显示一次)
    response = AIAgentResponse.model_validate(agent)
    response.api_key = new_api_key  # ⚠️ 仅此次返回
    
    return response
