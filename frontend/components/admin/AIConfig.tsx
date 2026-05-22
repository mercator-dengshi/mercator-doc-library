'use client';

import { useState, useEffect } from 'react';
import { Bot, Save, TestTube, Key } from 'lucide-react';
import { toast } from 'sonner';
import apiClient from '@/lib/api-client';

export default function AIConfig() {
  const [config, setConfig] = useState({
    provider: 'openai',
    api_key: '',
    model: 'gpt-3.5-turbo',
    temperature: '0.7',
    max_tokens: '1000',
    base_url: 'https://api.openai.com/v1'
  });
  const [isLoading, setIsLoading] = useState(false);

  // Load existing config on mount
  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const response = await apiClient.get('/config/ai-config');
      if (response.data.provider) {
        setConfig({
          provider: response.data.provider || 'openai',
          api_key: '', // Don't load full API key for security
          model: response.data.model || 'gpt-3.5-turbo',
          temperature: String(response.data.temperature || '0.7'),
          max_tokens: String(response.data.max_tokens || '1000'),
          base_url: response.data.base_url || 'https://api.openai.com/v1'
        });
      }
    } catch (error) {
      console.error('Failed to load AI config:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
      const response = await apiClient.post('/config/ai-config', {
        provider: config.provider,
        api_key: config.api_key,
        model: config.model,
        temperature: parseFloat(config.temperature),
        max_tokens: parseInt(config.max_tokens),
        base_url: config.base_url
      });
      
      toast.success(response.data.message || 'AI配置保存成功！');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || error.message || '保存失败，请重试');
    } finally {
      setIsLoading(false);
    }
  };

  const handleTestConnection = async () => {
    if (!config.api_key) {
      toast.error('请先填写API密钥');
      return;
    }

    setIsLoading(true);
    
    try {
      const response = await apiClient.post('/config/ai-config/test', {
        provider: config.provider,
        api_key: config.api_key,
        model: config.model,
        temperature: parseFloat(config.temperature),
        max_tokens: parseInt(config.max_tokens),
        base_url: config.base_url
      });
      
      toast.success(response.data.message || 'AI API连接测试成功！');
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
          <Bot className="text-purple-600 dark:text-purple-400" size={24} />
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            AI助手配置
          </h2>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          配置大模型API以启用AI助手功能
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Provider */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            AI服务提供商
          </label>
          <select
            value={config.provider}
            onChange={(e) => setConfig({ ...config, provider: e.target.value })}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
          >
            <option value="openai">OpenAI (GPT)</option>
            <option value="anthropic">Anthropic (Claude)</option>
            <option value="deepseek">DeepSeek</option>
            <option value="azure">Azure OpenAI</option>
            <option value="custom">自定义API</option>
          </select>
        </div>

        {/* API Key */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            API密钥
          </label>
          <div className="relative">
            <input
              type="password"
              value={config.api_key}
              onChange={(e) => setConfig({ ...config, api_key: e.target.value })}
              placeholder="sk-..."
              className="w-full px-4 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
            />
            <Key className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
          </div>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            请妥善保管您的API密钥，不要泄露给他人
          </p>
        </div>

        {/* Base URL (for custom providers and deepseek) */}
        {(config.provider === 'custom' || config.provider === 'deepseek') && (
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              API基础URL
            </label>
            <input
              type="url"
              value={config.base_url}
              onChange={(e) => setConfig({ ...config, base_url: e.target.value })}
              placeholder={config.provider === 'deepseek' ? 'https://api.deepseek.com/v1' : 'https://api.example.com/v1'}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
            />
            {config.provider === 'deepseek' && (
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                DeepSeek API地址: https://api.deepseek.com/v1
              </p>
            )}
          </div>
        )}

        {/* Model */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            模型名称
          </label>
          <select
            value={config.model}
            onChange={(e) => setConfig({ ...config, model: e.target.value })}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
          >
            {config.provider === 'openai' && (
              <>
                <option value="gpt-3.5-turbo">GPT-3.5 Turbo (推荐)</option>
                <option value="gpt-4">GPT-4</option>
                <option value="gpt-4-turbo">GPT-4 Turbo</option>
              </>
            )}
            {config.provider === 'anthropic' && (
              <>
                <option value="claude-3-opus">Claude 3 Opus</option>
                <option value="claude-3-sonnet">Claude 3 Sonnet</option>
                <option value="claude-3-haiku">Claude 3 Haiku</option>
              </>
            )}
            {config.provider === 'deepseek' && (
              <>
                <option value="deepseek-v4-flash">DeepSeek V4 Flash (推荐 - 非思考模式)</option>
                <option value="deepseek-v4-pro">DeepSeek V4 Pro (思考模式)</option>
                <option value="deepseek-chat">DeepSeek Chat (已弃用,2026/07/24)</option>
                <option value="deepseek-reasoner">DeepSeek Reasoner (已弃用,2026/07/24)</option>
              </>
            )}
            {config.provider === 'custom' && (
              <option value="custom-model">自定义模型</option>
            )}
          </select>
        </div>

        {/* Temperature */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            温度 (Temperature): {config.temperature}
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={config.temperature}
            onChange={(e) => setConfig({ ...config, temperature: e.target.value })}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
          />
          <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
            <span>精确 (0)</span>
            <span>平衡 (0.5)</span>
            <span>创意 (1.0)</span>
          </div>
          <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            控制回答的随机性：较低值更精确，较高值更有创意
          </p>
        </div>

        {/* Max Tokens */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            最大Token数
          </label>
          <input
            type="number"
            value={config.max_tokens}
            onChange={(e) => setConfig({ ...config, max_tokens: e.target.value })}
            placeholder="1000"
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
          />
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            限制单次回答的最大长度（1 Token ≈ 0.75个英文单词）
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4 pt-4">
          <button
            type="submit"
            disabled={isLoading}
            className="flex-1 bg-purple-600 hover:bg-purple-700 text-white font-medium py-2 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
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
      <div className="mt-8 p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
        <h3 className="text-sm font-semibold text-purple-900 dark:text-purple-300 mb-2">
          如何获取API密钥？
        </h3>
        <div className="text-xs text-purple-800 dark:text-purple-400 space-y-2">
          <p><strong>OpenAI:</strong> 访问 <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener noreferrer" className="underline hover:text-purple-600">https://platform.openai.com/api-keys</a></p>
          <p><strong>Anthropic:</strong> 访问 <a href="https://console.anthropic.com/" target="_blank" rel="noopener noreferrer" className="underline hover:text-purple-600">https://console.anthropic.com/</a></p>
          <p><strong>DeepSeek:</strong> 访问 <a href="https://platform.deepseek.com/" target="_blank" rel="noopener noreferrer" className="underline hover:text-purple-600">https://platform.deepseek.com/</a> 获取API密钥</p>
          <p><strong>Azure:</strong> 在Azure Portal中创建OpenAI资源并获取密钥</p>
          <p className="mt-2 pt-2 border-t border-purple-200 dark:border-purple-700">
            <strong>⚠️ DeepSeek模型更新:</strong><br />
            • deepseek-chat 和 deepseek-reasoner 将于 2026/07/24 弃用<br />
            • 请使用 deepseek-v4-flash (非思考模式) 或 deepseek-v4-pro (思考模式)
          </p>
          <p className="mt-2 text-xs opacity-75">
            💡 提示：建议设置使用限额以防止意外费用
          </p>
        </div>
      </div>
    </div>
  );
}
