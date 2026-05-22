'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import apiClient from '@/lib/api-client';
import { useAuthStore } from '@/stores/auth-store';
import CategoryManager from '@/components/CategoryManager';
import RecycleBin from '@/components/RecycleBin';
import UserManager from '@/components/UserManager';
import EmailConfig from '@/components/admin/EmailConfig';
import AIConfig from '@/components/admin/AIConfig';
import DocumentManager from '@/components/admin/DocumentManager';
import { 
  LayoutDashboard, 
  FileText, 
  FolderTree, 
  Users, 
  Settings,
  Mail,
  Bot,
  Trash2,
  TrendingUp,
  Activity
} from 'lucide-react';

type Tab = 'dashboard' | 'documents' | 'categories' | 'users' | 'recycle-bin' | 'email-config' | 'ai-config';

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState<Tab>('dashboard');
  const { user: currentUser } = useAuthStore();
  const isAdmin = currentUser?.role === 'admin';

  // Fetch statistics
  const { data: stats } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: async () => {
      const [docsRes, categoriesRes, usersRes] = await Promise.all([
        apiClient.get('/docs/?limit=1'),
        apiClient.get('/categories/?limit=1'),
        apiClient.get('/users/')
      ]);
      
      return {
        documents: docsRes.data.total || docsRes.headers['x-total-count'] || 0,
        categories: categoriesRes.data.total || categoriesRes.headers['x-total-count'] || 0,
        users: Array.isArray(usersRes.data) ? usersRes.data.length : 0
      };
    }
  });

  // Fetch version info
  const { data: versionInfo } = useQuery({
    queryKey: ['version-info'],
    queryFn: async () => {
      const response = await apiClient.get('/version');
      return response.data;
    },
    staleTime: 1000 * 60 * 5 // 5分钟缓存
  });

  const tabs: { id: Tab; label: string; icon: any; description?: string }[] = [
    { id: 'dashboard', label: '仪表盘', icon: LayoutDashboard, description: '系统概览和统计' },
    { id: 'documents', label: '文档管理', icon: FileText, description: '管理所有文档' },
    { id: 'categories', label: '分类管理', icon: FolderTree, description: '管理文档分类' },
    ...(isAdmin ? [{ id: 'users' as Tab, label: '用户管理', icon: Users, description: '管理用户和权限' }] : []),
    { id: 'recycle-bin', label: '回收站', icon: Trash2, description: '恢复或删除文档' },
    { id: 'email-config', label: '邮件配置', icon: Mail, description: 'SMTP服务器设置' },
    { id: 'ai-config', label: 'AI配置', icon: Bot, description: '大模型API配置' },
  ];

  const ActiveIcon = tabs.find(t => t.id === activeTab)?.icon || LayoutDashboard;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            后台管理
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            管理系统内容、用户和配置
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar Navigation */}
          <div className="lg:col-span-1">
            <nav className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4 space-y-2">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                      activeTab === tab.id
                        ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 border-l-4 border-blue-600'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                    }`}
                  >
                    <Icon size={20} />
                    <div className="text-left">
                      <div className="font-medium">{tab.label}</div>
                      {tab.description && (
                        <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                          {tab.description}
                        </div>
                      )}
                    </div>
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">
            {activeTab === 'dashboard' && (
              <DashboardContent stats={stats} onNavigate={setActiveTab} versionInfo={versionInfo} />
            )}
            {activeTab === 'documents' && <DocumentManager />}
            {activeTab === 'categories' && <CategoryManager />}
            {activeTab === 'users' && isAdmin && <UserManager />}
            {activeTab === 'recycle-bin' && <RecycleBin />}
            {activeTab === 'email-config' && <EmailConfig />}
            {activeTab === 'ai-config' && <AIConfig />}
          </div>
        </div>
      </div>
    </div>
  );
}

// Dashboard Content Component
function DashboardContent({ stats, onNavigate, versionInfo }: { stats?: any; onNavigate?: (tab: Tab) => void; versionInfo?: any }) {
  const latestVersion = versionInfo?.latest_version || 'v0.8.2';
  const releaseDate = versionInfo?.release_date || '2026-05-21';
  const changelog = versionInfo?.changelog || [];
  return (
    <div className="space-y-6">
      {/* 系统概览 */}
      <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg shadow-lg p-6 text-white">
        <h2 className="text-2xl font-bold mb-2">👋 欢迎使用 Mercator 文档库管理系统</h2>
        <p className="text-blue-100">当前版本: {latestVersion} | 发布日期: {releaseDate}</p>
      </div>

      {/* 系统环境信息 */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <Settings size={20} />
          系统环境
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div className="space-y-2">
            <div className="flex justify-between py-2 border-b border-gray-100 dark:border-gray-700">
              <span className="text-gray-600 dark:text-gray-400">前端框架</span>
              <span className="font-mono text-gray-900 dark:text-white">Next.js 16.2.6 + React 19</span>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-100 dark:border-gray-700">
              <span className="text-gray-600 dark:text-gray-400">后端框架</span>
              <span className="font-mono text-gray-900 dark:text-white">FastAPI + Python 3.12</span>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-100 dark:border-gray-700">
              <span className="text-gray-600 dark:text-gray-400">数据库</span>
              <span className="font-mono text-gray-900 dark:text-white">PostgreSQL 15 (Docker)</span>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between py-2 border-b border-gray-100 dark:border-gray-700">
              <span className="text-gray-600 dark:text-gray-400">文档地址</span>
              <a href="https://docs.mercator.cn" target="_blank" rel="noopener noreferrer" className="font-mono text-blue-600 dark:text-blue-400 hover:underline">https://docs.mercator.cn</a>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-100 dark:border-gray-700">
              <span className="text-gray-600 dark:text-gray-400">API服务</span>
              <a href="https://docsapi.mercator.cn" target="_blank" rel="noopener noreferrer" className="font-mono text-blue-600 dark:text-blue-400 hover:underline">https://docsapi.mercator.cn</a>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-100 dark:border-gray-700">
              <span className="text-gray-600 dark:text-gray-400">AI提供商</span>
              <span className="font-mono text-gray-900 dark:text-white">DeepSeek (deepseek-v4-flash)</span>
            </div>
          </div>
        </div>
      </div>

      {/* 常用命令 */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <Activity size={20} />
          常用命令速查
        </h3>
        <div className="space-y-3">
          <div className="bg-gray-50 dark:bg-gray-900 rounded p-3">
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">一键启动所有服务</p>
            <code className="text-sm font-mono text-green-600 dark:text-green-400 break-all">
              cd mercator_doc_library && docker compose up -d postgres && cd backend && nohup ../.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload & cd ../frontend && npm run dev
            </code>
          </div>
          <div className="bg-gray-50 dark:bg-gray-900 rounded p-3">
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">将用户提升为管理员</p>
            <code className="text-sm font-mono text-blue-600 dark:text-blue-400 break-all">
              psql -U mercator -d mercator_db -c "UPDATE users SET role='admin' WHERE email='user@example.com';"
            </code>
          </div>
          <div className="bg-gray-50 dark:bg-gray-900 rounded p-3">
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">查看后端日志</p>
            <code className="text-sm font-mono text-purple-600 dark:text-purple-400">
              tail -f /tmp/backend.log
            </code>
          </div>
          <div className="bg-gray-50 dark:bg-gray-900 rounded p-3">
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">重启后端服务</p>
            <code className="text-sm font-mono text-orange-600 dark:text-orange-400 break-all">
              ps aux | grep uvicorn | grep -v grep | awk {'{print $2}'} | xargs kill && cd backend && nohup ../.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
            </code>
          </div>
        </div>
      </div>

      {/* 开机自启配置 */}
      <div className="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-lg shadow-sm border border-green-200 dark:border-green-800 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <Settings size={20} className="text-green-600" />
          开机自启配置
        </h3>
        <div className="space-y-4">
          <div className="bg-white dark:bg-gray-800 rounded p-4 border border-green-200 dark:border-green-700">
            <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
              ✅ <strong>已启用systemd开机自启服务</strong>
            </p>
            <p className="text-xs text-gray-600 dark:text-gray-400 mb-3">
              系统启动时将自动启动PostgreSQL、后端API和前端服务
            </p>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between py-1 border-b border-gray-100 dark:border-gray-700">
                <span className="text-gray-600 dark:text-gray-400">服务名称</span>
                <span className="font-mono text-gray-900 dark:text-white">mercator.service</span>
              </div>
              <div className="flex justify-between py-1 border-b border-gray-100 dark:border-gray-700">
                <span className="text-gray-600 dark:text-gray-400">状态</span>
                <span className="text-green-600 dark:text-green-400 font-medium">enabled (开机自启)</span>
              </div>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="bg-gray-50 dark:bg-gray-900 rounded p-3">
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">启动服务</p>
              <code className="text-sm font-mono text-green-600 dark:text-green-400 break-all">
                sudo systemctl start mercator
              </code>
            </div>
            <div className="bg-gray-50 dark:bg-gray-900 rounded p-3">
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">停止服务</p>
              <code className="text-sm font-mono text-red-600 dark:text-red-400">
                sudo systemctl stop mercator
              </code>
            </div>
            <div className="bg-gray-50 dark:bg-gray-900 rounded p-3">
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">查看状态</p>
              <code className="text-sm font-mono text-blue-600 dark:text-blue-400">
                sudo systemctl status mercator
              </code>
            </div>
            <div className="bg-gray-50 dark:bg-gray-900 rounded p-3">
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">查看日志</p>
              <code className="text-sm font-mono text-purple-600 dark:text-purple-400">
                journalctl -u mercator -f
              </code>
            </div>
          </div>
        </div>
      </div>

      {/* 版本更新日志 */}
      {changelog.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <TrendingUp size={20} />
            版本更新日志
          </h3>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {changelog.map((item: any, index: number) => {
              const colors = ['border-blue-500', 'border-green-500', 'border-purple-500', 'border-orange-500', 'border-gray-300'];
              const colorClass = colors[index % colors.length];
              
              return (
                <div key={item.version} className={`border-l-4 ${colorClass} pl-4`}>
                  <p className="font-medium text-gray-900 dark:text-white">
                    {item.version} {item.date && `(${item.date})`}
                  </p>
                  {item.commits && item.commits.length > 0 && (
                    <ul className="text-sm text-gray-600 dark:text-gray-400 mt-1 space-y-1">
                      {item.commits.slice(0, 3).map((commit: string, idx: number) => (
                        <li key={idx}>• {commit.substring(8)}</li>
                      ))}
                    </ul>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
