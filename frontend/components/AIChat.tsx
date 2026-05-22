'use client';

import { useState, useRef, useEffect } from 'react';
import { useAuthStore } from '@/stores/auth-store';
import { Send, Bot, User, X, Minimize2, Maximize2 } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

interface AIChatProps {
  documentContext?: {
    title: string;
    content: string;
  };
}

export default function AIChat({ documentContext }: AIChatProps) {
  const { getAccessToken } = useAuthStore();
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: '您好！我是AI助手，有什么可以帮助您的吗？'
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const accessToken = getAccessToken();
    console.log('=== AI助手调试信息 ===');
    console.log('Token存在:', !!accessToken);
    console.log('Token长度:', accessToken?.length);
    console.log('Token前10字符:', accessToken?.substring(0, 10));
    
    if (!accessToken) {
      console.error(' Token不存在，请先登录');
      alert('请先登录');
      return;
    }

    const userMessage: Message = {
      role: 'user',
      content: input.trim()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // 使用完整的API URL,避免在生产环境中请求到错误的域名
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
      const chatUrl = `${apiUrl}/agents/chat`;
      
      console.log('发送AI请求...', {
        url: chatUrl,
        hasToken: !!accessToken,
        tokenLength: accessToken?.length
      });
      
      const response = await fetch(chatUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({
          messages: [...messages, userMessage].map(({ role, content }) => ({
            role,
            content
          })),
          // 不指定model,让后端使用配置的默认模型
          document_context: documentContext
        })
      });

      console.log('API响应状态:', response.status, response.statusText);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('API错误响应:', errorText);
        throw new Error(`API请求失败: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      console.log('AI响应成功:', data);
      
      setMessages(prev => [...prev, data.message]);
    } catch (error: any) {
      console.error('AI chat error:', error);
      console.error('错误详情:', error.message, error.stack);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `抱歉，我遇到了一些问题：${error.message || '请稍后再试。'}`
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 bg-blue-600 hover:bg-blue-700 text-white p-4 rounded-full shadow-lg transition-all hover:scale-110 z-50"
        title="打开AI助手"
      >
        <Bot size={28} />
      </button>
    );
  }

  return (
    <div
      className={`fixed bottom-6 right-6 bg-white dark:bg-gray-800 rounded-lg shadow-2xl border border-gray-200 dark:border-gray-700 transition-all z-50 ${
        isMinimized ? 'w-80 h-16' : 'w-96 h-[600px]'
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-t-lg">
        <div className="flex items-center space-x-2">
          <Bot size={20} />
          <span className="font-semibold">AI助手</span>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setIsMinimized(!isMinimized)}
            className="hover:bg-blue-500 p-1 rounded transition-colors"
            title={isMinimized ? '最大化' : '最小化'}
          >
            {isMinimized ? <Maximize2 size={16} /> : <Minimize2 size={16} />}
          </button>
          <button
            onClick={() => setIsOpen(false)}
            className="hover:bg-blue-500 p-1 rounded transition-colors"
            title="关闭"
          >
            <X size={16} />
          </button>
        </div>
      </div>

      {!isMinimized && (
        <>
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 h-[calc(600px-140px)]">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-2 ${
                    message.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
                  }`}
                >
                  <div className="flex items-start space-x-2">
                    {message.role === 'assistant' && <Bot size={16} className="mt-1 flex-shrink-0" />}
                    <div className="whitespace-pre-wrap break-words text-sm">
                      {message.content}
                    </div>
                    {message.role === 'user' && <User size={16} className="mt-1 flex-shrink-0" />}
                  </div>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 dark:bg-gray-700 rounded-lg px-4 py-2">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="border-t border-gray-200 dark:border-gray-700 p-4">
            <div className="flex space-x-2">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="输入消息... (Shift+Enter换行)"
                rows={1}
                className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white resize-none text-sm"
                disabled={isLoading}
              />
              <button
                onClick={handleSend}
                disabled={!input.trim() || isLoading}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white p-2 rounded-lg transition-colors"
                title="发送"
              >
                <Send size={20} />
              </button>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-2 text-center">
              AI助手可能会产生不准确的信息，请验证重要信息
            </p>
          </div>
        </>
      )}
    </div>
  );
}
