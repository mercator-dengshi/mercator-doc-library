#!/bin/bash
# ============================================================================
# ECS快速部署脚本(简化版)
# ============================================================================

set -e

ECS_HOST="39.107.238.22"
DEPLOY_DIR="/opt/mercator-doc-library"

echo "=========================================="
echo "  Mercator Doc Library - ECS部署"
echo "=========================================="
echo ""

# 1. 备份数据库
echo "💾 备份ECS数据库..."
ssh root@$ECS_HOST << 'ENDSSH'
mkdir -p /opt/backups
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
pg_dump -U mercator -d mercator_docs -F c -f /opt/backups/db_backup_$TIMESTAMP.dump 2>/dev/null && echo "✅ 数据库备份完成" || echo "⚠️  数据库备份跳过"
ENDSSH

# 2. 上传代码
echo ""
echo "📤 上传代码到ECS..."
scp -r /home/mercator/Documents/qoder_projects/mercator_doc_library/* root@$ECS_HOST:$DEPLOY_DIR/ --exclude='node_modules' --exclude='.git' --exclude='venv' --exclude='__pycache__' --exclude='*.log' --exclude='docs' --exclude='scripts' --exclude='deploy-*.sh' --exclude='rollback-*.sh' --exclude='auto-deploy.sh' --exclude='setup-ecs-env.sh' --exclude='.env.production.template' || true

# 使用rsync替代
echo "使用rsync同步文件..."
rsync -avz --delete \
  --exclude='node_modules' \
  --exclude='.git' \
  --exclude='venv' \
  --exclude='__pycache__' \
  --exclude='*.log' \
  --exclude='docs/' \
  --exclude='scripts/' \
  --exclude='deploy-*.sh' \
  --exclude='rollback-*.sh' \
  --exclude='auto-deploy.sh' \
  --exclude='setup-ecs-env.sh' \
  --exclude='.env.production.template' \
  /home/mercator/Documents/qoder_projects/mercator_doc_library/ \
  root@$ECS_HOST:$DEPLOY_DIR/

echo "✅ 代码上传完成"

# 3. 重启服务
echo ""
echo "🔄 重启ECS服务..."
ssh root@$ECS_HOST << 'ENDSSH'
cd /opt/mercator-doc-library/backend

# 重建虚拟环境
echo "重建Python虚拟环境..."
rm -rf venv
python3 -m venv venv
venv/bin/python3 -m pip install --upgrade pip --quiet
venv/bin/python3 -m pip install -r requirements.txt --quiet

# 重启后端
echo "重启后端服务..."
systemctl restart mercator-backend

# 健康检查
sleep 5
if systemctl is-active --quiet mercator-backend; then
    echo "✅ 后端服务运行正常"
else
    echo "❌ 后端服务启动失败"
    journalctl -u mercator-backend --no-pager -n 20
fi
ENDSSH

echo ""
echo "=========================================="
echo "  ✅ 部署完成!"
echo "=========================================="
echo ""
echo "⚠️  重要提示:"
echo "  1. 配置环境变量: ssh root@$ECS_HOST"
echo "  2. 编辑: vim /etc/systemd/system/mercator-backend.service"
echo "  3. 替换所有 YOUR_XXX_HERE 占位符"
echo "  4. 重启: systemctl daemon-reload && systemctl restart mercator-backend"
echo "  5. 查看日志: journalctl -u mercator-backend -f"
