'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/lib/api-client';
import { Bot, Key, Trash2, RefreshCw, Plus, Copy, CheckCircle } from 'lucide-react';

interface AIAgent {
  id: string;
  name: string;
  description: string;
  api_key_prefix: string;
  permissions: {
    create_documents?: boolean;
    update_documents?: boolean;
    delete_documents?: boolean;
    read_documents?: boolean;
  };
  status: string;
  created_at: string;
  last_active_at?: string;
}

export default function APIKeyManager() {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newAgentName, setNewAgentName] = useState('');
  const [newAgentDesc, setNewAgentDesc] = useState('');
  const [createdApiKey, setCreatedApiKey] = useState<string | null>(null);
  const queryClient = useQueryClient();

  // 获取智能体列表
  const { data: agents, isLoading } = useQuery({
    queryKey: ['ai-agents'],
    queryFn: async () => {
      const response = await apiClient.get('/agents/');
      return response.data;
    }
  });

  // 创建智能体
  const createMutation = useMutation({
    mutationFn: async (data: { name: string; description: string }) => {
      const response = await apiClient.post('/agents/', {
        ...data,
        permissions: {
          create_documents: true,
          update_documents: true,
          delete_documents: false,
          read_documents: true
        }
      });
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['ai-agents'] });
      setCreatedApiKey(data.api_key);
      setShowCreateModal(false);
      setNewAgentName('');
      setNewAgentDesc('');
    }
  });

  // 删除智能体
  const deleteMutation = useMutation({
    mutationFn: async (agentId: string) => {
      await apiClient.delete(`/agents/${agentId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-agents'] });
    }
  });

  // 重置API密钥
  const resetKeyMutation = useMutation({
    mutationFn: async (agentId: string) => {
      const response = await apiClient.post(`/agents/${agentId}/reset-key`);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['ai-agents'] });
      setCreatedApiKey(data.api_key);
    }
  });

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    alert('✅ API密钥已复制到剪贴板');
  };

  if (isLoading) {
    return <div className="text-center py-8">加载中...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">API密钥管理</h2>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            管理外部AI智能体的API密钥，如OpenClaw、Cursor等
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus size={20} />
          创建智能体
        </button>
      </div>

      {/* API密钥列表 */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        {agents && agents.length > 0 ? (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {agents.map((agent: AIAgent) => (
              <div key={agent.id} className="p-6 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <Bot className="text-blue-600" size={24} />
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                        {agent.name}
                      </h3>
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        agent.status === 'active' 
                          ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                          : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-400'
                      }`}>
                        {agent.status}
                      </span>
                    </div>
                    
                    {agent.description && (
                      <p className="text-gray-600 dark:text-gray-400 text-sm mb-3">
                        {agent.description}
                      </p>
                    )}

                    <div className="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
                      <div className="flex items-center gap-1">
                        <Key size={14} />
                        <span className="font-mono">{agent.api_key_prefix}</span>
                      </div>
                      {agent.last_active_at && (
                        <span>最后活跃: {new Date(agent.last_active_at).toLocaleString('zh-CN')}</span>
                      )}
                    </div>

                    {/* 权限标签 */}
                    <div className="flex gap-2 mt-3">
                      {agent.permissions.create_documents && (
                        <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400 rounded">
                          创建文档
                        </span>
                      )}
                      {agent.permissions.update_documents && (
                        <span className="px-2 py-1 text-xs bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400 rounded">
                          更新文档
                        </span>
                      )}
                      {agent.permissions.delete_documents && (
                        <span className="px-2 py-1 text-xs bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400 rounded">
                          删除文档
                        </span>
                      )}
                    </div>
                  </div>

                  {/* 操作按钮 */}
                  <div className="flex gap-2">
                    <button
                      onClick={() => resetKeyMutation.mutate(agent.id)}
                      className="p-2 text-yellow-600 hover:bg-yellow-50 dark:hover:bg-yellow-900/20 rounded-lg transition-colors"
                      title="重置API密钥"
                    >
                      <RefreshCw size={18} />
                    </button>
                    <button
                      onClick={() => {
                        if (confirm('确定要删除这个智能体吗？此操作不可恢复！')) {
                          deleteMutation.mutate(agent.id);
                        }
                      }}
                      className="p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                      title="删除智能体"
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <Bot size={48} className="mx-auto text-gray-400 mb-4" />
            <p className="text-gray-600 dark:text-gray-400">暂无API密钥</p>
            <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
              点击"创建智能体"开始使用
            </p>
          </div>
        )}
      </div>

      {/* 创建智能体模态框 */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
              创建AI智能体
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  名称
                </label>
                <input
                  type="text"
                  value={newAgentName}
                  onChange={(e) => setNewAgentName(e.target.value)}
                  placeholder="例如: OpenClaw Writer"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  描述
                </label>
                <textarea
                  value={newAgentDesc}
                  onChange={(e) => setNewAgentDesc(e.target.value)}
                  placeholder="用于自动撰写和更新文档的AI智能体"
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded p-3">
                <p className="text-sm text-yellow-800 dark:text-yellow-400">
                  💡 提示: 默认权限为创建、更新、读取文档，不包含删除权限
                </p>
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowCreateModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                取消
              </button>
              <button
                onClick={() => createMutation.mutate({ name: newAgentName, description: newAgentDesc })}
                disabled={!newAgentName || createMutation.isPending}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
              >
                {createMutation.isPending ? '创建中...' : '创建'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 显示新创建的API密钥 */}
      {createdApiKey && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-lg w-full mx-4 p-6">
            <div className="flex items-center gap-3 mb-4">
              <CheckCircle className="text-green-600" size={32} />
              <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                API密钥创建成功
              </h3>
            </div>

            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded p-4 mb-4">
              <p className="text-sm text-red-800 dark:text-red-400 font-medium mb-2">
                ⚠️ 重要提示
              </p>
              <p className="text-sm text-red-700 dark:text-red-300">
                这是您的API密钥，<strong>仅显示一次</strong>！请立即复制并妥善保管。
                如果丢失，需要重新生成。
              </p>
            </div>

            <div className="bg-gray-100 dark:bg-gray-900 rounded p-4 mb-4">
              <code className="text-sm font-mono text-gray-900 dark:text-white break-all">
                {createdApiKey}
              </code>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => copyToClipboard(createdApiKey)}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Copy size={18} />
                复制密钥
              </button>
              <button
                onClick={() => setCreatedApiKey(null)}
                className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
