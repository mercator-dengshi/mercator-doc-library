from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, text
from typing import List, Dict, Any
import json
import os
from app.core.database import get_db
from app.schemas.schemas import SearchResult, SearchRequest, SearchResponse
from app.models.models import Document, Category, Tag, DocumentTag

router = APIRouter()


def extract_search_keywords(query: str) -> Dict[str, Any]:
    """
    简单关键词提取(不使用AI,降低成本)
    将查询字符串按空格和常见分隔符拆分
    """
    import re
    
    # 移除标点符号,保留中文、英文、数字
    cleaned = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', query)
    
    # 按空格拆分
    keywords = [kw.strip() for kw in cleaned.split() if kw.strip()]
    
    # 如果没有提取到关键词,使用原始查询
    if not keywords:
        keywords = [query]
    
    return {
        'keywords': keywords,
        'intent': query,
        'filters': {},
        'suggestions': keywords[:3]  # 最多3个建议
    }


def perform_fulltext_search(db: Session, keywords: Dict[str, Any], limit: int = 20) -> List[SearchResult]:
    """
    在PostgreSQL中进行全文搜索
    """
    keyword_list = keywords.get('keywords', [])
    
    if not keyword_list:
        return []
    
    # 构建搜索条件：在标题和内容中搜索关键词
    search_conditions = []
    for keyword in keyword_list:
        search_conditions.append(
            or_(
                Document.title.ilike(f'%{keyword}%'),
                Document.content.ilike(f'%{keyword}%')
            )
        )
    
    # 执行查询
    query = db.query(Document).filter(
        or_(*search_conditions),
        Document.deleted_at.is_(None),  # 不搜索已删除的文档
        Document.status == 'published'  # 只搜索已发布的文档
    )
    
    # 计算相关性评分
    documents = query.limit(limit).all()
    
    results = []
    for doc in documents:
        # 计算匹配度（简单实现：根据关键词出现次数）
        score = 0.0
        content_preview = None
        
        for keyword in keyword_list:
            # 标题匹配权重更高
            if keyword.lower() in doc.title.lower():
                score += 0.5
            
            # 内容匹配
            if keyword.lower() in doc.content.lower():
                score += 0.3
                # 提取内容预览（包含关键词的片段）
                if not content_preview:
                    idx = doc.content.lower().find(keyword.lower())
                    if idx != -1:
                        start = max(0, idx - 50)
                        end = min(len(doc.content), idx + len(keyword) + 100)
                        content_preview = "..." + doc.content[start:end] + "..."
        
        # 获取分类信息
        category = None
        if doc.category:
            category = {
                'id': doc.category.id,
                'name': doc.category.name,
                'slug': doc.category.slug,
                'description': doc.category.description,
                'parent_id': doc.category.parent_id,
                'icon': doc.category.icon,
                'sort_order': doc.category.sort_order,
                'is_visible': doc.category.is_visible,
                'document_count': 0,
                'children': [],
                'created_at': doc.category.created_at
            }
        
        # 获取标签
        tags = [dt.tag.name for dt in doc.tags] if doc.tags else []
        
        results.append(SearchResult(
            id=doc.id,
            title=doc.title,
            slug=doc.slug,
            excerpt=doc.excerpt,
            content_preview=content_preview,
            score=min(score, 1.0),  # 最高1.0
            match_type='fulltext',
            category=category,
            tags=tags,
            updated_at=doc.updated_at
        ))
    
    # 按评分排序
    results.sort(key=lambda x: x.score, reverse=True)
    
    return results


@router.post("", response_model=SearchResponse)
@router.post("/", response_model=SearchResponse)
def search_documents(
    search_request: SearchRequest,
    db: Session = Depends(get_db)
):
    """
    语义搜索文档
    1. 使用AI理解搜索意图
    2. 提取关键词
    3. 在数据库中搜索
    4. 返回结果
    """
    try:
        # Step 1: AI理解搜索意图并提取关键词
        keywords = extract_search_keywords(search_request.query)
        
        # Step 2: 数据库全文搜索
        results = perform_fulltext_search(db, keywords, limit=search_request.limit)
        
        # Step 3: 返回结果
        return SearchResponse(
            query=search_request.query,
            results=results,
            total=len(results),
            suggestions=keywords.get('suggestions', [])
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"搜索失败: {str(e)}"
        )


@router.get("/legacy", response_model=List[SearchResult])
def legacy_search_documents(
    q: str = Query(..., min_length=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    旧的GET搜索端点（向后兼容）
    使用路径: GET /api/v1/search/legacy?q=关键词
    """
    # 使用相同的搜索逻辑
    keywords = {'keywords': [q], 'intent': q, 'filters': {}, 'suggestions': [q]}
    results = perform_fulltext_search(db, keywords, limit=limit)
    return results[skip:skip+limit]


@router.post("/semantic", response_model=List[SearchResult])
def semantic_search(
    query: dict,
    db: Session = Depends(get_db)
):
    """
    语义搜索端点（向后兼容）
    """
    query_text = query.get('query', '')
    if not query_text:
        return []
    
    keywords = extract_search_keywords(query_text)
    results = perform_fulltext_search(db, keywords)
    return results
