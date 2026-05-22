'use client';

import { useState, useEffect } from 'react';
import { Mail, Save, TestTube } from 'lucide-react';
import { toast } from 'sonner';
import apiClient from '@/lib/api-client';

export default function EmailConfig() {
  const [config, setConfig] = useState({
    smtp_server: '',
    smtp_port: '587',
    smtp_user: '',
    smtp_password: '',
    from_email: '',
    from_name: 'Mercator文档库'
  });
  const [isLoading, setIsLoading] = useState(false);

  // Load existing config on mount
  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const response = await apiClient.get('/config/email-config');
      if (response.data.smtp_server) {
        setConfig({
          smtp_server: response.data.smtp_server || '',
          smtp_port: String(response.data.smtp_port || '587'),
          smtp_user: response.data.smtp_user || '',
          smtp_password: '', // Don't load password for security
          from_email: response.data.from_email || '',
          from_name: response.data.from_name || 'Mercator文档库'
        });
      }
    } catch (error) {
      console.error('Failed to load email config:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
      const response = await apiClient.post('/config/email-config', {
        smtp_server: config.smtp_server,
        smtp_port: parseInt(config.smtp_port),
        smtp_user: config.smtp_user,
        smtp_password: config.smtp_password,
        from_email: config.from_email,
        from_name: config.from_name
      });
      
      toast.success(response.data.message || '邮件配置保存成功！');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || error.message || '保存失败，请重试');
    } finally {
      setIsLoading(false);
    }
  };

  const handleTestConnection = async () => {
    if (!config.smtp_server || !config.smtp_user || !config.smtp_password) {
      toast.error('请先填写完整的SMTP配置信息');
      return;
    }

    setIsLoading(true);
    
    try {
      const response = await apiClient.post('/config/email-config/test', {
        smtp_server: config.smtp_server,
        smtp_port: parseInt(config.smtp_port),
        smtp_user: config.smtp_user,
        smtp_password: config.smtp_password,
        from_email: config.from_email,
        from_name: config.from_name
      });
      
      toast.success(response.data.message || '邮件服务器连接测试成功！');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || error.message || '连接测试失败');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <Mail className="text-blue-600 dark:text-blue-400" size={24} />
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            邮件服务器配置
          </h2>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          配置SMTP服务器以发送密码重置邮件和系统通知
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* SMTP Server */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            SMTP服务器地址
          </label>
          <input
            type="text"
            value={config.smtp_server}
            onChange={(e) => setConfig({ ...config, smtp_server: e.target.value })}
            placeholder="smtp.example.com"
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
          />
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            例如：smtp.gmail.com, smtp.qq.com, smtp.163.com
          </p>
        </div>

        {/* SMTP Port */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            SMTP端口
          </label>
          <input
            type="number"
            value={config.smtp_port}
            onChange={(e) => setConfig({ ...config, smtp_port: e.target.value })}
            placeholder="587"
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
          />
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            常用端口：587 (TLS), 465 (SSL), 25 (无加密)
          </p>
        </div>

        {/* SMTP User */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            SMTP用户名
          </label>
          <input
            type="text"
            value={config.smtp_user}
            onChange={(e) => setConfig({ ...config, smtp_user: e.target.value })}
            placeholder="noreply@example.com"
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
          />
        </div>

        {/* SMTP Password */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            SMTP密码 / 授权码
          </label>
          <input
            type="password"
            value={config.smtp_password}
            onChange={(e) => setConfig({ ...config, smtp_password: e.target.value })}
            placeholder="输入SMTP密码或授权码"
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
          />
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            某些邮箱服务商（如QQ、163）需要使用授权码而非登录密码
          </p>
        </div>

        {/* From Email */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            发件人邮箱
          </label>
          <input
            type="email"
            value={config.from_email}
            onChange={(e) => setConfig({ ...config, from_email: e.target.value })}
            placeholder="noreply@example.com"
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
          />
        </div>

        {/* From Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            发件人名称
          </label>
          <input
            type="text"
            value={config.from_name}
            onChange={(e) => setConfig({ ...config, from_name: e.target.value })}
            placeholder="Mercator文档库"
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
          />
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4 pt-4">
          <button
            type="submit"
            disabled={isLoading}
            className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            <Save size={18} />
            {isLoading ? '保存中...' : '保存配置'}
          </button>
          <button
            type="button"
            onClick={handleTestConnection}
            disabled={isLoading}
            className="flex-1 bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            <TestTube size={18} />
            {isLoading ? '测试中...' : '测试连接'}
          </button>
        </div>
      </form>

      {/* Help Section */}
      <div className="mt-8 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
        <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-300 mb-2">
          常见邮箱SMTP配置
        </h3>
        <div className="text-xs text-blue-800 dark:text-blue-400 space-y-1">
          <p><strong>Gmail:</strong> smtp.gmail.com:587 (需要开启两步验证并生成应用密码)</p>
          <p><strong>QQ邮箱:</strong> smtp.qq.com:587 (需要在设置中开启SMTP并获取授权码)</p>
          <p><strong>163邮箱:</strong> smtp.163.com:587 (需要开启SMTP服务并获取授权码)</p>
          <p><strong>Outlook:</strong> smtp-mail.outlook.com:587</p>
        </div>
      </div>
    </div>
  );
}
