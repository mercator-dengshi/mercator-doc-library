#!/usr/bin/env python3
"""
版本信息生成脚本
在构建/部署时运行,从Git标签生成version.json文件
"""
import subprocess
import json
import os
from datetime import datetime


def get_git_tags():
    """获取所有Git标签,按创建日期排序(最新的在前)"""
    try:
        result = subprocess.run(
            ['git', 'tag', '-l', '--sort=-creatordate'],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        if result.returncode == 0:
            tags = [tag.strip() for tag in result.stdout.split('\n') if tag.strip()]
            return tags
        return []
    except Exception as e:
        print(f"Warning: Failed to get git tags: {e}")
        return []


def get_tag_date(tag):
    """获取标签的创建日期"""
    try:
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%ai', tag],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        if result.returncode == 0:
            date_str = result.stdout.strip()
            dt = datetime.fromisoformat(date_str)
            return dt.strftime('%Y-%m-%d')
        return None
    except Exception:
        return None


def get_tag_commits(tag, limit=5):
    """获取标签对应的commit信息"""
    try:
        # 获取从上一个tag到当前tag的commits
        result = subprocess.run(
            ['git', 'log', '--oneline', f'{tag}~{limit}..{tag}'],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=os.path.dirname(os.path.abspath(__file__))
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
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        if result.returncode == 0:
            commits = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            return commits[:limit]
        
        return []
    except Exception:
        return []


def generate_version_info():
    """生成版本信息并保存为JSON文件"""
    print("📦 Generating version information...")
    
    tags = get_git_tags()
    
    if not tags:
        print("⚠️  No git tags found, using default version v0.0.0")
        version_data = {
            "latest_version": "v0.0.0",
            "release_date": None,
            "changelog": [],
            "generated_at": datetime.utcnow().isoformat()
        }
    else:
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
        
        version_data = {
            "latest_version": latest_tag,
            "release_date": release_date,
            "changelog": changelog,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    # 保存到backend/app/version.json
    output_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'backend',
        'app',
        'version.json'
    )
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(version_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Version info saved to: {output_path}")
    print(f"📌 Latest version: {version_data['latest_version']}")
    if version_data['release_date']:
        print(f"📅 Release date: {version_data['release_date']}")
    print(f"📝 Changelog entries: {len(version_data['changelog'])}")


if __name__ == '__main__':
    generate_version_info()
