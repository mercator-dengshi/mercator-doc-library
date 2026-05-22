'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/stores/auth-store';
import { toast } from 'sonner';

export default function ChangePasswordPage() {
  const router = useRouter();
  const { user, getAccessToken } = useAuthStore();
  
  const [formData, setFormData] = useState({
    old_password: '',
    new_password: '',
    confirm_password: ''
  });
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validation
    if (formData.new_password !== formData.confirm_password) {
      toast.error('新密码和确认密码不一致');
      return;
    }
    
    if (formData.new_password.length < 8) {
      toast.error('新密码至少需要8个字符');
      return;
    }
    
    setIsLoading(true);
    
    try {
      const accessToken = getAccessToken();
      if (!accessToken) {
        toast.error('请先登录');
        return;
      }

      const response = await fetch('/api/v1/auth/change-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({
          old_password: formData.old_password,
          new_password: formData.new_password
        })
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '修改密码失败');
      }
      
      toast.success('密码修改成功！');
      
      // Clear form
      setFormData({
        old_password: '',
        new_password: '',
        confirm_password: ''
      });
      
      // Redirect after 2 seconds
      setTimeout(() => {
        router.push('/');
      }, 2000);
      
    } catch (error: any) {
      toast.error(error.message || '修改密码失败，请重试');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md mx-auto">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              修改密码
            </h1>
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
              请输入当前密码和新密码
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="old_password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                当前密码
              </label>
              <input
                id="old_password"
                name="old_password"
                type="password"
                required
                value={formData.old_password}
                onChange={(e) => setFormData({ ...formData, old_password: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                placeholder="请输入当前密码"
              />
            </div>

            <div>
              <label htmlFor="new_password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                新密码
              </label>
              <input
                id="new_password"
                name="new_password"
                type="password"
                required
                value={formData.new_password}
                onChange={(e) => setFormData({ ...formData, new_password: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                placeholder="请输入新密码（至少8个字符）"
              />
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                密码长度至少为8个字符
              </p>
            </div>

            <div>
              <label htmlFor="confirm_password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                确认新密码
              </label>
              <input
                id="confirm_password"
                name="confirm_password"
                type="password"
                required
                value={formData.confirm_password}
                onChange={(e) => setFormData({ ...formData, confirm_password: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                placeholder="请再次输入新密码"
              />
            </div>

            <div className="flex space-x-4">
              <button
                type="submit"
                disabled={isLoading}
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? '处理中...' : '修改密码'}
              </button>
              <Link
                href="/"
                className="flex-1 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 font-medium py-2 px-4 rounded-lg transition-colors text-center"
              >
                取消
              </Link>
            </div>
          </form>

          <div className="mt-6 text-center">
            <Link
              href="/forgot-password"
              className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
            >
              忘记密码？
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
