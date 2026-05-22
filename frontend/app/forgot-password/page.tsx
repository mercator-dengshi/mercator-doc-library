'use client';

import { useState } from 'react';
import Link from 'next/link';
import { toast } from 'sonner';

export default function ForgotPasswordPage() {
  const [step, setStep] = useState<'email' | 'verify'>('email');
  const [email, setEmail] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [devCode, setDevCode] = useState<string>('');

  const handleSendCode = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
      const response = await fetch('/api/v1/auth/forgot-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email })
      });
      
      if (!response.ok) {
        throw new Error('发送验证码失败');
      }
      
      const data = await response.json();
      
      // In development mode, show the code
      if (data.code) {
        setDevCode(data.code.toString());
        toast.success(`开发模式 - 验证码: ${data.code}`);
      } else {
        toast.success('验证码已发送到您的邮箱');
      }
      
      setStep('verify');
      
    } catch (error: any) {
      toast.error(error.message || '发送验证码失败，请重试');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validation
    if (newPassword !== confirmPassword) {
      toast.error('新密码和确认密码不一致');
      return;
    }
    
    if (newPassword.length < 8) {
      toast.error('新密码至少需要8个字符');
      return;
    }
    
    setIsLoading(true);
    
    try {
      const response = await fetch('/api/v1/auth/reset-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          email,
          verification_code: verificationCode,
          new_password: newPassword
        })
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '重置密码失败');
      }
      
      toast.success('密码重置成功！请使用新密码登录');
      
      // Redirect to login after 2 seconds
      setTimeout(() => {
        window.location.href = '/login';
      }, 2000);
      
    } catch (error: any) {
      toast.error(error.message || '重置密码失败，请重试');
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
              {step === 'email' ? '忘记密码' : '重置密码'}
            </h1>
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
              {step === 'email' 
                ? '请输入您的邮箱地址，我们将发送验证码'
                : '请输入验证码和新密码'}
            </p>
          </div>

          {step === 'email' ? (
            <form onSubmit={handleSendCode} className="space-y-6">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  邮箱地址
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                  placeholder="请输入您的邮箱"
                />
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? '发送中...' : '发送验证码'}
              </button>
            </form>
          ) : (
            <form onSubmit={handleResetPassword} className="space-y-6">
              <div>
                <label htmlFor="code" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  验证码
                </label>
                <input
                  id="code"
                  name="code"
                  type="text"
                  required
                  value={verificationCode}
                  onChange={(e) => setVerificationCode(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                  placeholder="请输入6位验证码"
                  maxLength={6}
                />
                {devCode && (
                  <p className="mt-2 text-sm text-yellow-600 dark:text-yellow-400">
                    开发模式验证码：<strong>{devCode}</strong>
                  </p>
                )}
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
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                  placeholder="请输入新密码（至少8个字符）"
                />
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
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                  placeholder="请再次输入新密码"
                />
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? '处理中...' : '重置密码'}
              </button>

              <button
                type="button"
                onClick={() => setStep('email')}
                className="w-full bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 font-medium py-2 px-4 rounded-lg transition-colors"
              >
                返回
              </button>
            </form>
          )}

          <div className="mt-6 text-center">
            <Link
              href="/login"
              className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
            >
              返回登录
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
