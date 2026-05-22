#!/bin/bash
# ============================================================================
# ECS环境变量自动配置脚本
# 功能: 自动生成并配置systemd服务文件的环境变量
# ============================================================================

set -e

ECS_HOST="39.107.238.22"

echo "=========================================="
echo "  ECS环境变量自动配置"
echo "=========================================="
echo ""

# 生成密钥
echo "🔑 生成加密密钥..."
ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")

echo "✅ ENCRYPTION_KEY已生成"
echo "✅ JWT_SECRET已生成"
echo ""

# 询问用户配置信息
echo "📝 请输入以下配置信息:"
echo ""

read -p "数据库密码 (mercator用户): " DB_PASSWORD
read -p "SMTP服务器 (默认smtp.qq.com): " SMTP_SERVER
SMTP_SERVER=${SMTP_SERVER:-smtp.qq.com}
read -p "SMTP端口 (默认587): " SMTP_PORT
SMTP_PORT=${SMTP_PORT:-587}
read -p "SMTP用户名 (邮箱): " SMTP_USER
read -s -p "SMTP授权码 (不是登录密码!): " SMTP_PASSWORD
echo ""
read -p "发件人邮箱 (默认同SMTP用户名): " FROM_EMAIL
FROM_EMAIL=${FROM_EMAIL:-$SMTP_USER}
read -p "发件人名称 (默认Mercator文档库): " FROM_NAME
FROM_NAME=${FROM_NAME:-Mercator文档库}
read -p "DeepSeek API Key: " DEEPSEEK_API_KEY
echo ""

echo "⚠️  确认配置信息:"
echo "  数据库密码: ${DB_PASSWORD:0:3}***"
echo "  SMTP服务器: $SMTP_SERVER:$SMTP_PORT"
echo "  SMTP用户: $SMTP_USER"
echo "  发件人: $FROM_EMAIL ($FROM_NAME)"
echo "  DeepSeek API: ${DEEPSEEK_API_KEY:0:10}***"
echo ""

read -p "确认配置? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "❌ 取消配置"
    exit 1
fi

# SSH到ECS配置环境变量
echo ""
echo "📤 正在配置ECS..."

ssh root@$ECS_HOST << ENDSSH
# 备份当前配置
if [ -f /etc/systemd/system/mercator-backend.service ]; then
    cp /etc/systemd/system/mercator-backend.service /etc/systemd/system/mercator-backend.service.backup.\$(date +%Y%m%d_%H%M%S)
    echo "✅ 已备份旧配置"
fi

# 创建新的systemd服务文件
cat > /etc/systemd/system/mercator-backend.service << 'EOF'
[Unit]
Description=Mercator Doc Library Backend
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/mercator-doc-library/backend

# Database Configuration
Environment="DATABASE_URL=postgresql://mercator:${DB_PASSWORD}@localhost:5432/mercator_docs"

# Encryption
Environment="ENCRYPTION_KEY=${ENCRYPTION_KEY}"

# Email Configuration (SMTP)
Environment="SMTP_SERVER=${SMTP_SERVER}"
Environment="SMTP_PORT=${SMTP_PORT}"
Environment="SMTP_USER=${SMTP_USER}"
Environment="SMTP_PASSWORD=${SMTP_PASSWORD}"
Environment="FROM_EMAIL=${FROM_EMAIL}"
Environment="FROM_NAME=${FROM_NAME}"

# AI Provider Configuration
Environment="DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}"
Environment="AI_MODEL=deepseek-chat"
Environment="AI_TEMPERATURE=0.7"
Environment="AI_MAX_TOKENS=1000"

# JWT Authentication
Environment="SECRET_KEY=${JWT_SECRET}"
Environment="ACCESS_TOKEN_EXPIRE_MINUTES=30"

# Server Configuration
Environment="HOST=0.0.0.0"
Environment="PORT=8000"
Environment="DEBUG=false"

ExecStart=/opt/mercator-doc-library/backend/venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "✅ systemd服务文件已更新"

# 重新加载并重启服务
systemctl daemon-reload
echo "✅ systemd配置已重载"

systemctl restart mercator-backend
echo "✅ 后端服务已重启"

# 等待服务启动
sleep 5

# 健康检查
if systemctl is-active --quiet mercator-backend; then
    echo "✅ 后端服务运行正常"
    echo ""
    echo "服务状态:"
    systemctl status mercator-backend --no-pager -l | head -15
else
    echo "❌ 后端服务启动失败"
    echo ""
    echo "错误日志:"
    journalctl -u mercator-backend --no-pager -n 30
fi

ENDSSH

echo ""
echo "=========================================="
echo "  ✅ ECS配置完成!"
echo "=========================================="
echo ""
echo "💾 重要信息已保存:"
echo "  ENCRYPTION_KEY: ${ENCRYPTION_KEY}"
echo "  JWT_SECRET: ${JWT_SECRET}"
echo ""
echo "⚠️  请妥善保管以上密钥,建议保存到密码管理器!"
echo ""
echo "下一步操作:"
echo "  1. 测试邮件发送: curl -X POST http://$ECS_HOST:8000/api/v1/auth/forgot-password -H 'Content-Type: application/json' -d '{\"email\": \"test@example.com\"}'"
echo "  2. 查看实时日志: ssh root@$ECS_HOST 'journalctl -u mercator-backend -f'"
echo "  3. 访问应用: http://$ECS_HOST:3000"
