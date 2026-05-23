'use client';

import Link from 'next/link';
import { useAuthStore } from '@/stores/auth-store';

export default function Navbar() {
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    window.location.href = '/login';
  };

  return (
    <nav className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="/" className="text-xl font-bold text-blue-600 dark:text-blue-400">
            Mercator Doc Library
          </Link>

          {/* Navigation Links */}
          <div className="flex items-center gap-6">
            <Link href="/docs" className="text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400">
              文档
            </Link>

            {/* Admin Link (only for admin users) */}
            {user?.role === 'admin' && (
              <Link
                href="/admin"
                className="text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400"
              >
                管理
              </Link>
            )}

            {/* User Menu */}
            {user ? (
              <div className="flex items-center gap-3">
                <span className="text-sm text-gray-600 dark:text-gray-300">
                  {user.name}
                </span>
                <Link
                  href="/change-password"
                  className="px-4 py-2 text-sm text-blue-600 border border-blue-600 rounded hover:bg-blue-50 dark:hover:bg-blue-900/20"
                >
                  修改密码
                </Link>
                <button
                  onClick={handleLogout}
                  className="px-4 py-2 text-sm text-red-600 border border-red-600 rounded hover:bg-red-50 dark:hover:bg-red-900/20"
                >
                  退出
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <Link href="/login" className="text-gray-600 dark:text-gray-300 hover:text-blue-600">
                  登录
                </Link>
                <Link
                  href="/register"
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  注册
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
