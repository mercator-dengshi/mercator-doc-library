from fastapi import APIRouter, HTTPException
from typing import List, Optional
import os
import json
from datetime import datetime

router = APIRouter()


def load_version_info():
    """
    从version.json文件加载版本信息
    
    这个文件在构建时由generate_version.py脚本生成,
    这样即使在没有Git的生产环境也能正常显示版本信息
    """
    try:
        # version.json位于 backend/app/version.json
        version_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'version.json'
        )
        
        if os.path.exists(version_file):
            with open(version_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            print(f"Warning: version.json not found at {version_file}")
            return None
    except Exception as e:
        print(f"Error loading version.json: {e}")
        return None


@router.get("/version")
def get_version_info():
    """
    获取版本信息
    
    Returns:
    - latest_version: 最新版本号
    - release_date: 发布日期
    - changelog: 最近5个版本的更新日志
    
    注意: 版本信息从version.json文件读取,该文件在构建时生成
    """
    version_data = load_version_info()
    
    if not version_data:
        # 如果version.json不存在,返回默认值
        return {
            "latest_version": "v0.0.0",
            "release_date": None,
            "changelog": [],
            "note": "Version info not available. Run generate_version.py to create version.json"
        }
    
    return version_data


@router.get("/version/latest")
def get_latest_version():
    """获取最新版本号"""
    version_data = load_version_info()
    
    if version_data and version_data.get('latest_version'):
        return {"version": version_data['latest_version']}
    
    return {"version": "v0.0.0"}
