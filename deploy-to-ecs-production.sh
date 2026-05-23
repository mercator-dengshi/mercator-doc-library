#!/bin/bash
# ECS生产环境部署脚本 - 纯净版
# 功能: 仅部署核心代码,排除所有临时文档、测试脚本等

set -e

# ECS配置
ECS_HOST="39.107.238.22"
ECS_USER="root"
ECS_PASSWORD="Mercator.cn@0871"
ECS_PATH="/opt/mercator_doc_library"

echo "=========================================="
echo "🚀 Mercator Doc Library ECS生产环境部署"
echo "=========================================="
echo ""

# 检查是否安装了 sshpass (用于密码认证)
if ! command -v sshpass &> /dev/null; then
    echo "⚠️  未检测到 sshpass,尝试使用 SSH 密钥认证..."
    USE_SSHPASS=false
else
    USE_SSHPASS=true
fi

# 1. 清理ECS上的旧文件(不备份,纯生产环境)
echo "📦 步骤1: 清理ECS上的旧文件..."
if [ "$USE_SSHPASS" = true ]; then
    sshpass -p "${ECS_PASSWORD}" ssh -o StrictHostKeyChecking=no ${ECS_USER}@${ECS_HOST} << 'EOF'
        echo "   删除旧项目目录..."
        rm -rf /opt/mercator_doc_library
        echo "   ✅ 清理完成"
EOF
else
    ssh -o StrictHostKeyChecking=no ${ECS_USER}@${ECS_HOST} << 'EOF'
        echo "   删除旧项目目录..."
        rm -rf /opt/mercator_doc_library
        echo "   ✅ 清理完成"
EOF
fi

# 2. 打包核心文件(使用git archive自动排除.gitignore中的文件)
echo ""
echo "📦 步骤2: 打包核心文件(仅包含生产必需文件)..."
cd "$(dirname "$0")"

# 创建临时打包目录
TEMP_DIR=$(mktemp -d)
PROJECT_NAME="mercator_doc_library"

# 使用git archive导出干净的项目(自动排除.gitignore中的文件)
# 这会排除: docs/, scripts/, tests/, *.md(除README), 临时文件等
git archive --format=tar HEAD 2>/dev/null | tar x -C "$TEMP_DIR"

# 进入临时目录压缩
cd "$TEMP_DIR"
tar czf "${PROJECT_NAME}.tar.gz" .

PACKAGE_SIZE=$(du -h ${PROJECT_NAME}.tar.gz | cut -f1)
echo "   ✅ 打包完成: ${PROJECT_NAME}.tar.gz"
echo "   大小: ${PACKAGE_SIZE}"

# 3. 上传到ECS
echo ""
echo "📤 步骤3: 上传到ECS..."
if [ "$USE_SSHPASS" = true ]; then
    sshpass -p "${ECS_PASSWORD}" scp -o StrictHostKeyChecking=no "${PROJECT_NAME}.tar.gz" ${ECS_USER}@${ECS_HOST}:/tmp/
else
    scp -o StrictHostKeyChecking=no "${PROJECT_NAME}.tar.gz" ${ECS_USER}@${ECS_HOST}:/tmp/
fi

# 4. 在ECS上解压和部署
echo ""
echo "🔧 步骤4: 在ECS上部署..."
if [ "$USE_SSHPASS" = true ]; then
    sshpass -p "${ECS_PASSWORD}" ssh -o StrictHostKeyChecking=no ${ECS_USER}@${ECS_HOST} << EOF
    # 创建项目目录
    mkdir -p ${ECS_PATH}
    
    # 解压文件
    cd ${ECS_PATH}
    tar xzf /tmp/${PROJECT_NAME}.tar.gz
    
    # 清理临时文件
    rm -f /tmp/${PROJECT_NAME}.tar.gz
    
    echo "   ✅ 解压完成"
EOF
else
    ssh -o StrictHostKeyChecking=no ${ECS_USER}@${ECS_HOST} << EOF
    # 创建项目目录
    mkdir -p ${ECS_PATH}
    
    # 解压文件
    cd ${ECS_PATH}
    tar xzf /tmp/${PROJECT_NAME}.tar.gz
    
    # 清理临时文件
    rm -f /tmp/${PROJECT_NAME}.tar.gz
    
    echo "   ✅ 解压完成"
EOF
fi

# 5. 在ECS上安装依赖和启动服务
echo ""
echo "⚙️  步骤5: 在ECS上安装依赖和启动服务..."
if [ "$USE_SSHPASS" = true ]; then
    sshpass -p "${ECS_PASSWORD}" ssh -o StrictHostKeyChecking=no ${ECS_USER}@${ECS_HOST} << 'EOF'
    cd /opt/mercator_doc_library
    
    # 创建前端 .env.production 文件（如果不存在）
    if [ ! -f frontend/.env.production ]; then
        echo "   创建前端 .env.production..."
        cat > frontend/.env.production << 'ENV_EOF'
NEXT_PUBLIC_API_URL=https://docsapi.mercator.cn/api/v1
ENV_EOF
    fi
    
    # 生成后端 .env 文件（从模板）
    echo "   检查后端 .env 文件..."
    if [ -f backend/.env.template ]; then
        # 检查是否已有 .env 文件，如果有则保留（避免覆盖敏感配置）
        if [ ! -f backend/.env ]; then
            echo "   ⚠️  .env 文件不存在，需要从本地上传或使用 generate_env.sh 脚本生成"
            echo "   请运行: scp backend/.env root@${ECS_HOST}:/opt/mercator_doc_library/backend/.env"
        else
            echo "   ✅ .env 文件已存在，跳过生成"
        fi
    else
        echo "   ⚠️  .env.template 不存在，请确保从本地上传 .env 文件"
    fi
    
    # 生成版本信息
    echo "   生成版本信息..."
    python3 generate_version.py
    
    # 后端依赖
    echo "   安装后端依赖..."
    cd backend
    pip3 install -r requirements.txt -q --break-system-packages
    
    # 前端依赖和构建
    echo "   安装前端依赖并构建..."
    cd ../frontend
    npm install
    npm run build
    
    # 重启服务
    echo "   重启服务..."
    systemctl restart mercator-backend || echo "   ⚠️  backend服务重启失败,可能需要手动启动"
    systemctl restart mercator-frontend || echo "   ⚠️  frontend服务重启失败,可能需要手动启动"
    
    echo "   ✅ 部署完成"
EOF
else
    ssh -o StrictHostKeyChecking=no ${ECS_USER}@${ECS_HOST} << 'EOF'
    cd /opt/mercator_doc_library
    
    # 创建前端 .env.production 文件（如果不存在）
    if [ ! -f frontend/.env.production ]; then
        echo "   创建前端 .env.production..."
        cat > frontend/.env.production << 'ENV_EOF'
NEXT_PUBLIC_API_URL=https://docsapi.mercator.cn/api/v1
ENV_EOF
    fi
    
    # 生成后端 .env 文件（从模板）
    echo "   检查后端 .env 文件..."
    if [ -f backend/.env.template ]; then
        # 检查是否已有 .env 文件，如果有则保留（避免覆盖敏感配置）
        if [ ! -f backend/.env ]; then
            echo "   ⚠️  .env 文件不存在，需要从本地上传或使用 generate_env.sh 脚本生成"
            echo "   请运行: scp backend/.env root@${ECS_HOST}:/opt/mercator_doc_library/backend/.env"
        else
            echo "   ✅ .env 文件已存在，跳过生成"
        fi
    else
        echo "   ⚠️  .env.template 不存在，请确保从本地上传 .env 文件"
    fi
    
    # 生成版本信息
    echo "   生成版本信息..."
    python3 generate_version.py
    
    # 后端依赖
    echo "   安装后端依赖..."
    cd backend
    pip3 install -r requirements.txt -q --break-system-packages
    
    # 前端依赖和构建
    echo "   安装前端依赖并构建..."
    cd ../frontend
    npm install
    npm run build
    
    # 重启服务
    echo "   重启服务..."
    systemctl restart mercator-backend || echo "   ⚠️  backend服务重启失败,可能需要手动启动"
    systemctl restart mercator-frontend || echo "   ⚠️  frontend服务重启失败,可能需要手动启动"
    
    echo "   ✅ 部署完成"
EOF
fi

# 6. 清理本地临时文件
echo ""
echo "🧹 清理本地临时文件..."
rm -rf "$TEMP_DIR"

echo ""
echo "=========================================="
echo "✅ 部署完成!"
echo "=========================================="
echo ""
echo "访问地址:"
echo "  - 前端: https://your-domain.com"
echo "  - 后端API: https://your-domain.com/api/v1"
echo ""
echo "检查服务状态:"
if [ "$USE_SSHPASS" = true ]; then
    echo "  sshpass -p '${ECS_PASSWORD}' ssh root@${ECS_HOST} 'systemctl status mercator-backend mercator-frontend'"
else
    echo "  ssh root@${ECS_HOST} 'systemctl status mercator-backend mercator-frontend'"
fi
echo ""
