#!/bin/bash
# ============================================================================
# ECS环境变量配置脚本
# ⚠️ 重要: 执行前请修改下面的敏感信息!
# ============================================================================

echo "=========================================="
echo "  ECS环境变量配置"
echo "=========================================="
echo ""

# SSH到ECS并配置环境变量
ssh root@39.107.238.22 << 'ENDSSH'

echo "📝 配置后端服务环境变量..."

# 备份当前配置
if [ -f /etc/systemd/system/mercator-backend.service ]; then
    cp /etc/systemd/system/mercator-backend.service /etc/systemd/system/mercator-backend.service.backup.$(date +%Y%m%d_%H%M%S)
fi

# 更新systemd服务文件,添加环境变量
cat > /etc/systemd/system/mercator-backend.service << 'EOF'
[Unit]
Description=Mercator Doc Library Backend
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/mercator-doc-library/backend

# Environment Variables
Environment="DATABASE_URL=postgresql://mercator:YOUR_DB_PASSWORD@localhost:5432/mercator_docs"
Environment="ENCRYPTION_KEY=YOUR_ENCRYPTION_KEY_HERE"
Environment="SMTP_SERVER=smtp.qq.com"
Environment="SMTP_PORT=587"
Environment="SMTP_USER=your_email@qq.com"
Environment="SMTP_PASSWORD=YOUR_AUTH_CODE_HERE"
Environment="FROM_EMAIL=your_email@qq.com"
Environment="FROM_NAME=Mercator文档库"
Environment="DEEPSEEK_API_KEY=sk-YOUR_API_KEY_HERE"
Environment="AI_MODEL=deepseek-chat"
Environment="AI_TEMPERATURE=0.7"
Environment="AI_MAX_TOKENS=1000"
Environment="SECRET_KEY=YOUR_JWT_SECRET_KEY_HERE"
Environment="ACCESS_TOKEN_EXPIRE_MINUTES=30"
Environment="HOST=0.0.0.0"
Environment="PORT=8000"
Environment="DEBUG=false"

ExecStart=/opt/mercator-doc-library/backend/venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "✅ systemd服务配置已更新"
echo ""
echo "⚠️  重要提示:"
echo "  1. 请编辑 /etc/systemd/system/mercator-backend.service"
echo "  2. 替换所有 YOUR_XXX_HERE 占位符为实际值"
echo "  3. 运行: systemctl daemon-reload"
echo "  4. 运行: systemctl restart mercator-backend"
echo ""

ENDSSH

echo "✅ 配置脚本已执行"
echo ""
echo "下一步操作:"
echo "  1. SSH到ECS: ssh root@39.107.238.22"
echo "  2. 编辑环境变量: vim /etc/systemd/system/mercator-backend.service"
echo "  3. 替换所有占位符为实际值"
echo "  4. 重启服务: systemctl daemon-reload && systemctl restart mercator-backend"
echo "  5. 查看日志: journalctl -u mercator-backend -f"
