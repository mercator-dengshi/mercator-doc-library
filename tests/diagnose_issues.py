#!/usr/bin/env python3
"""
诊断脚本 - 检查认证和权限问题
"""

import sys
sys.path.insert(0, 'backend')

from app.core.database import SessionLocal
from app.models.models import User, Category
from app.schemas.schemas import CategoryCreate
from pydantic import ValidationError

print("=" * 70)
print("🔍 诊断 Mercator 文档库问题")
print("=" * 70)

# 1. 检查用户数据
print("\n1️⃣  检查数据库中的用户...")
db = SessionLocal()
users = db.query(User).all()
for u in users:
    print(f"   👤 {u.email}")
    print(f"      - Name: {u.name}")
    print(f"      - Role: {u.role} (type: {type(u.role).__name__})")
    if hasattr(u.role, 'value'):
        print(f"      - Role value: {u.role.value}")
    print(f"      - Is active: {u.is_active}")
    print()

# 2. 检查分类创建的数据验证
print("\n2️⃣  测试分类创建的数据验证...")
test_cases = [
    {"name": "测试1", "slug": "test1"},
    {"name": "测试2", "slug": "test2", "icon": None},
    {"name": "测试3", "slug": "test3", "icon": ""},
    {"name": "测试4", "slug": "test4", "description": "", "icon": ""},
]

for i, data in enumerate(test_cases, 1):
    try:
        category = CategoryCreate(**data)
        print(f"   ✅ 测试{i}: 成功")
        print(f"      icon={category.icon!r}, description={category.description!r}")
    except ValidationError as e:
        print(f"   ❌ 测试{i}: 失败")
        print(f"      Error: {e}")
    print()

# 3. 检查现有分类
print("\n3️⃣  检查现有分类...")
categories = db.query(Category).all()
if categories:
    for cat in categories:
        print(f"   📁 {cat.name} (slug: {cat.slug})")
        print(f"      - Icon: {cat.icon!r}")
        print(f"      - Description: {cat.description!r}")
else:
    print("   ℹ️  暂无分类")

db.close()

print("\n" + "=" * 70)
print("✅ 诊断完成")
print("=" * 70)
