'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/lib/api-client';
import { useAuthStore } from '@/stores/auth-store';

interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'editor' | 'viewer';
  is_active: boolean;
  ai_enabled: boolean;  // AI助手使用权限
  created_at: string;
}

export default function UserManager() {
  const queryClient = useQueryClient();
  const { user: currentUser } = useAuthStore();
  const [editingUser, setEditingUser] = useState<User | null>(null);

  const { data: users, isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: async () => {
      const response = await apiClient.get('/users');
      return response.data;
    },
  });

  const updateRoleMutation = useMutation({
    mutationFn: async ({ userId, role }: { userId: string; role: string }) => {
      const response = await apiClient.put(`/users/${userId}/role`, { role });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setEditingUser(null);
      alert('角色更新成功');
    },
    onError: (err: any) => {
      alert(err.response?.data?.detail || '更新角色失败');
    },
  });

  const updateAiPermissionMutation = useMutation({
    mutationFn: async ({ userId, aiEnabled }: { userId: string; aiEnabled: boolean }) => {
      const response = await apiClient.put(`/users/${userId}/ai-permission?ai_enabled=${aiEnabled}`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
    onError: (err: any) => {
      alert(err.response?.data?.detail || '更新AI权限失败');
    },
  });

  const deleteUserMutation = useMutation({
    mutationFn: async (userId: string) => {
      await apiClient.delete(`/users/${userId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      alert('用户已删除');
    },
    onError: (err: any) => {
      alert(err.response?.data?.detail || '删除用户失败');
    },
  });

  const handleRoleChange = (user: User, newRole: string) => {
    if (user.id === currentUser?.id && newRole !== 'admin') {
      alert('不能降低自己的角色权限');
      return;
    }
    
    if (confirm(`确定要将 "${user.name}" 的角色改为 "${getRoleName(newRole)}" 吗？`)) {
      updateRoleMutation.mutate({ userId: user.id, role: newRole });
    }
  };

  const getRoleName = (role: string) => {
    const roles: Record<string, string> = {
      admin: '管理员',
      editor: '编辑者',
      viewer: '查看者',
    };
    return roles[role] || role;
  };

  const getRoleColor = (role: string) => {
    const colors: Record<string, string> = {
      admin: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
      editor: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      viewer: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200',
    };
    return colors[role] || '';
  };

  if (isLoading) {
    return <div className="animate-pulse space-y-2"><div className="h-8 bg-gray-200 rounded"></div></div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">用户管理</h3>
        <p className="text-sm text-gray-500">{users?.length || 0} 个用户</p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b border-gray-200 dark:border-gray-700">
              <th className="text-left py-3 px-4 font-medium text-gray-600 dark:text-gray-400">姓名</th>
              <th className="text-left py-3 px-4 font-medium text-gray-600 dark:text-gray-400">邮箱</th>
              <th className="text-left py-3 px-4 font-medium text-gray-600 dark:text-gray-400">角色</th>
              <th className="text-left py-3 px-4 font-medium text-gray-600 dark:text-gray-400">状态</th>
              <th className="text-left py-3 px-4 font-medium text-gray-600 dark:text-gray-400">AI助手</th>
              <th className="text-left py-3 px-4 font-medium text-gray-600 dark:text-gray-400">注册时间</th>
              <th className="text-left py-3 px-4 font-medium text-gray-600 dark:text-gray-400">操作</th>
            </tr>
          </thead>
          <tbody>
            {users?.map((user: User) => (
              <tr key={user.id} className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                <td className="py-3 px-4">
                  <div className="font-medium">{user.name}</div>
                </td>
                <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400">{user.email}</td>
                <td className="py-3 px-4">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getRoleColor(user.role)}`}>
                    {getRoleName(user.role)}
                  </span>
                </td>
                <td className="py-3 px-4">
                  <span className={`px-2 py-1 rounded text-xs ${user.is_active ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'}`}>
                    {user.is_active ? '活跃' : '禁用'}
                  </span>
                </td>
                <td className="py-3 px-4">
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={user.ai_enabled}
                      onChange={(e) => {
                        if (confirm(`确定要${e.target.checked ? '开启' : '关闭'} "${user.name}" 的AI助手权限吗？`)) {
                          updateAiPermissionMutation.mutate({ 
                            userId: user.id, 
                            aiEnabled: e.target.checked 
                          });
                        }
                      }}
                      disabled={updateAiPermissionMutation.isPending}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                    <span className="ml-2 text-xs text-gray-600 dark:text-gray-400">
                      {user.ai_enabled ? '已开启' : '未开启'}
                    </span>
                  </label>
                </td>
                <td className="py-3 px-4 text-sm text-gray-500">
                  {new Date(user.created_at).toLocaleDateString('zh-CN')}
                </td>
                <td className="py-3 px-4">
                  <div className="flex items-center gap-2">
                    {user.id !== currentUser?.id && (
                      <select
                        value={user.role}
                        onChange={(e) => handleRoleChange(user, e.target.value)}
                        disabled={updateRoleMutation.isPending}
                        className="px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="viewer">查看者</option>
                        <option value="editor">编辑者</option>
                        <option value="admin">管理员</option>
                      </select>
                    )}
                    {user.id === currentUser?.id && (
                      <span className="text-xs text-gray-400">当前用户</span>
                    )}
                    {user.id !== currentUser?.id && (
                      <button
                        onClick={() => {
                          if (confirm(`确定要删除用户 "${user.name}" 吗？此操作不可恢复！`)) {
                            deleteUserMutation.mutate(user.id);
                          }
                        }}
                        disabled={deleteUserMutation.isPending}
                        className="px-2 py-1 text-xs text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
                      >
                        删除
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {users && users.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <p>暂无用户</p>
        </div>
      )}
    </div>
  );
}
