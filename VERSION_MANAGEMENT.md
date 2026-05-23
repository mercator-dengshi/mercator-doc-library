# 版本信息管理

## 概述

本项目的版本信息采用**构建时生成,运行时读取**的策略,确保在开发和生产环境都能正常显示版本信息。

## 工作原理

### 开发环境

1. **生成版本文件**: 运行 `python3 generate_version.py`
   - 脚本会从Git标签读取版本信息
   - 生成 `backend/app/version.json` 文件
   
2. **API读取**: 后端API直接读取 `version.json` 文件
   - 不需要调用Git命令
   - 性能更好,更可靠

### 生产环境 (ECS)

1. **构建阶段**: 在部署前运行 `python3 generate_version.py`
   - 将生成的 `version.json` 打包到应用中
   
2. **运行阶段**: ECS上不需要Git仓库
   - API直接读取已打包的 `version.json`
   - 即使没有 `.git` 目录也能正常显示版本

## 使用方法

### 本地开发

```bash
# 1. 创建Git标签(可选)
git tag v0.8.3-new-feature

# 2. 生成版本文件
python3 generate_version.py

# 3. 启动后端服务
cd backend && ../.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### ECS部署

```bash
# 1. 克隆代码(包含.git目录)
git clone <repository-url>
cd mercator_doc_library

# 2. 生成版本文件(在构建时执行)
python3 generate_version.py

# 3. 部署应用(复制整个项目到ECS)
#    version.json会被一起复制过去

# 4. 在ECS上启动服务
#    不需要.git目录,version.json已经包含了所有版本信息
```

## 版本文件格式

`backend/app/version.json` 示例:

```json
{
  "latest_version": "v0.8.2-fix-api-key-management",
  "release_date": "2026-05-23",
  "changelog": [
    {
      "version": "v0.8.2-fix-api-key-management",
      "date": "2026-05-23",
      "description": "Fix Api Key Management",
      "commits": [
        "7ffe8bd ✅ 修复API密钥管理权限问题",
        "09b2104 ✅ 调试API密钥列表显示问题"
      ]
    }
  ],
  "generated_at": "2026-05-23T03:37:39.890159"
}
```

## API端点

### GET /api/v1/version

获取完整版本信息:

```json
{
  "latest_version": "v0.8.2-fix-api-key-management",
  "release_date": "2026-05-23",
  "changelog": [...]
}
```

### GET /api/v1/version/latest

仅获取最新版本号:

```json
{
  "version": "v0.8.2-fix-api-key-management"
}
```

## 优势

1. ✅ **不依赖Git**: 生产环境不需要`.git`目录
2. ✅ **性能更好**: 不需要每次API调用都执行Git命令
3. ✅ **更可靠**: 避免了Git命令执行失败的风险
4. ✅ **易于维护**: 版本信息与代码一起打包部署

## 注意事项

- 每次发布新版本后,记得运行 `python3 generate_version.py` 更新版本信息
- 可以将此脚本添加到CI/CD流程中自动化执行
- `version.json` 应该被提交到Git仓库,确保版本信息可追溯
