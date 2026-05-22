from fastapi import APIRouter, HTTPException
from typing import List, Optional
import subprocess
import re
from datetime import datetime

router = APIRouter()


def get_git_tags() -> List[str]:
    """获取所有Git标签,按创建日期排序(最新的在前)"""
    try:
        # 使用creatordate排序,确保按实际打tag的时间排序
        import os
        # Git仓库根目录是项目根目录(backend的父目录)
        # version.py -> endpoints -> v1 -> api -> app -> backend -> project_root
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
        result = subprocess.run(
            ['git', 'tag', '-l', '--sort=-creatordate'],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=project_root
        )
        if result.returncode == 0:
            tags = [tag.strip() for tag in result.stdout.split('\n') if tag.strip()]
            return tags
        return []
    except Exception:
        return []


def get_tag_date(tag: str) -> Optional[str]:
    """获取标签的创建日期"""
    try:
        import os
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%ai', tag],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=project_root
        )
        if result.returncode == 0:
            date_str = result.stdout.strip()
            # 转换为更易读的格式
            dt = datetime.fromisoformat(date_str)
            return dt.strftime('%Y-%m-%d')
        return None
    except Exception:
        return None


def get_tag_commits(tag: str, limit: int = 5) -> List[str]:
    """获取标签对应的commit信息"""
    try:
        import os
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
        # 获取从上一个tag到当前tag的commits
        result = subprocess.run(
            ['git', 'log', '--oneline', f'{tag}~{limit}..{tag}'],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=project_root
        )
        if result.returncode == 0:
            commits = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            return commits[:limit]
        
        # 如果失败,尝试获取最近的commits
        result = subprocess.run(
            ['git', 'log', '--oneline', '-n', str(limit), tag],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=project_root
        )
        if result.returncode == 0:
            commits = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            return commits[:limit]
        
        return []
    except Exception:
        return []


@router.get("/version")
def get_version_info():
    """
    获取版本信息
    
    Returns:
    - latest_version: 最新版本号
    - release_date: 发布日期
    - changelog: 最近5个版本的更新日志
    """
    tags = get_git_tags()
    
    if not tags:
        return {
            "latest_version": "v0.0.0",
            "release_date": None,
            "changelog": []
        }
    
    latest_tag = tags[0]
    release_date = get_tag_date(latest_tag)
    
    # 生成最近5个版本的changelog
    changelog = []
    for tag in tags[:5]:
        commits = get_tag_commits(tag, limit=3)
        date = get_tag_date(tag)
        
        # 从tag名称提取描述(如果有)
        description = ""
        if '-' in tag:
            parts = tag.split('-', 1)
            if len(parts) > 1:
                description = parts[1].replace('-', ' ').title()
        
        changelog.append({
            "version": tag,
            "date": date,
            "description": description,
            "commits": commits
        })
    
    return {
        "latest_version": latest_tag,
        "release_date": release_date,
        "changelog": changelog
    }


@router.get("/version/latest")
def get_latest_version():
    """获取最新版本号"""
    tags = get_git_tags()
    if tags:
        return {"version": tags[0]}
    return {"version": "v0.0.0"}
