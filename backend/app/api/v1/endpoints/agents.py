from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.schemas import AIAgentCreate, AIAgentResponse, AIChatRequest, AIChatResponse
from app.models.models import AIAgent, User, Document
from app.models.system_config import SystemConfig, ConfigKeys
import hashlib
import secrets
import os

router = APIRouter()


@router.post("/", response_model=AIAgentResponse, status_code=status.HTTP_201_CREATED)
def create_agent(agent_data: AIAgentCreate, db: Session = Depends(get_db)):
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
        permissions=agent_data.permissions.dict()
    )
    
    db.add(new_agent)
    db.commit()
    db.refresh(new_agent)
    
    # Return with API key (only shown once)
    response = AIAgentResponse.model_validate(new_agent)
    response.api_key = api_key
    
    return response


@router.post("/chat", response_model=AIChatResponse)
def chat_with_ai(
    request: AIChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    与AI助手对话
    支持上下文感知和文档引用
    
    注意: 用户必须具有ai_enabled权限才能使用此功能
    """
    # 检查用户是否有AI助手权限
    if not current_user.ai_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您没有AI助手使用权限，请联系管理员开通"
        )
    
    # Get conversation history
    messages = request.messages or []
    
    # Build system prompt based on context
    system_prompt = """你是一个专业的文档库AI助手。你的任务是帮助用户：
1. 回答关于文档内容的问题
2. 提供文档编写建议
3. 协助文档分类和标签管理
4. 解答技术问题

请保持回答简洁、专业、有帮助性。如果不确定，诚实地告诉用户。
"""
    
    # If document context is provided, add it to the prompt
    if request.document_context:
        system_prompt += f"\n\n当前正在查看的文档：{request.document_context.get('title', 'Unknown')}\n"
        system_prompt += f"文档内容摘要：{request.document_context.get('content', '')[:500]}...\n"
    
    # Prepare messages for AI API
    ai_messages = [{"role": "system", "content": system_prompt}] + messages
    
    # Call AI API (OpenAI or other providers)
    try:
        ai_response = call_ai_api(ai_messages, request.model, db)  # ✅ 传递db参数
        
        return AIChatResponse(
            message={
                "role": "assistant",
                "content": ai_response
            },
            usage={
                "prompt_tokens": len(str(messages)),
                "completion_tokens": len(ai_response),
                "total_tokens": len(str(messages)) + len(ai_response)
            }
        )
    except Exception as e:
        # In development mode, return a mock response
        import os
        if os.getenv("ENVIRONMENT") == "development":
            return AIChatResponse(
                message={
                    "role": "assistant",
                    "content": f"【开发模式】这是一个模拟回复。您说：{messages[-1].get('content', '')[:50]}..."
                },
                usage={
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                    "total_tokens": 30
                }
            )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI service error: {str(e)}"
        )


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


def call_ai_api(messages: list, model: str = None, db: Session = None) -> str:
    """
    调用AI API（OpenAI或其他提供商）
    ✅ 从数据库读取API密钥和模型配置
    
    Args:
        messages: 对话消息列表
        model: 可选的模型名称，如果未提供则使用配置中的模型
        db: 数据库会话(可选，用于从数据库读取配置)
    """
    # 从数据库读取AI配置
    api_key = None
    base_url = None
    temperature = 0.7
    max_tokens = 1000
    configured_model = None
    
    if db:
        try:
            # 查询AI配置
            configs = db.query(SystemConfig).filter(
                SystemConfig.category == 'ai'
            ).all()
            
            for config in configs:
                key = config.key.replace('ai.', '')
                value = config.get_value()
                
                if key == 'api_key':
                    api_key = value
                elif key == 'base_url':
                    base_url = value if value else None
                elif key == 'model':
                    configured_model = value
                elif key == 'temperature':
                    temperature = float(value) if value else 0.7
                elif key == 'max_tokens':
                    max_tokens = int(value) if value else 1000
        except Exception as e:
            print(f"⚠️  Failed to load AI config from database: {e}")
    
    # Use configured model if no model specified
    if not model and configured_model:
        model = configured_model
    elif not model:
        # Default model if nothing configured
        model = "deepseek-chat"
    
    # Fallback to environment variables (if database has no config)
    if not api_key:
        api_key = os.getenv("DEEPSEEK_API_KEY", "")
        if not base_url:
            base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    
    if not api_key:
        # No API key configured, return mock response
        return "AI服务尚未配置。请在后台仪表盘的'AI配置'中设置API密钥。"
    
    # Example using OpenAI API
    # In production, install: pip install openai
    try:
        from openai import OpenAI
        
        print(f"[AI DEBUG] Initializing OpenAI client...")
        print(f"[AI DEBUG] api_key={api_key[:10]}..." if api_key else "[AI DEBUG] api_key=None")
        print(f"[AI DEBUG] base_url={base_url}")
        print(f"[AI DEBUG] model={model}")
        print(f"[AI DEBUG] temperature={temperature}, max_tokens={max_tokens}")
        
        # Create client - ONLY pass api_key and base_url, nothing else!
        # OpenAI SDK v1.x 只支持这些参数
        if base_url:
            client = OpenAI(api_key=api_key, base_url=base_url)
        else:
            client = OpenAI(api_key=api_key)
        
        print(f"[AI DEBUG] Client created successfully")
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        print(f"[AI DEBUG] Response received")
        return response.choices[0].message.content
    except ImportError as e:
        error_msg = f"OpenAI SDK未安装: {str(e)}"
        print(f"[AI ERROR] {error_msg}")
        return "OpenAI SDK未安装。请运行：pip install openai"
    except Exception as e:
        # 记录详细错误信息
        error_msg = f"AI API调用失败: {str(e)}"
        print(f"[AI ERROR] {error_msg}")
        print(f"[AI ERROR] Error type: {type(e).__name__}")
        print(f"[AI ERROR] Traceback:", exc_info=True)
        print(f"[AI CONFIG] provider=deepseek, model={model}, base_url={base_url}")
        print(f"[AI CONFIG] api_key length: {len(api_key) if api_key else 0}")
        # 返回用户友好的错误消息
        return f"抱歉，AI服务暂时不可用。错误信息: {str(e)[:100]}"
