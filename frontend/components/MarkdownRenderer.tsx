'use client';

import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MarkdownRendererProps {
  content: string;
}

export default function MarkdownRenderer({ content }: MarkdownRendererProps) {
  return (
    <div className="prose dark:prose-invert max-w-none">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // 自定义标题样式
          h1: ({ node, ...props }) => (
            <h1 className="text-3xl font-bold mt-8 mb-4 pb-2 border-b" {...props} />
          ),
          h2: ({ node, ...props }) => (
            <h2 className="text-2xl font-semibold mt-6 mb-3" {...props} />
          ),
          h3: ({ node, ...props }) => (
            <h3 className="text-xl font-semibold mt-4 mb-2" {...props} />
          ),
          // 自定义链接样式
          a: ({ node, ...props }) => (
            <a className="text-blue-600 hover:underline dark:text-blue-400" {...props} />
          ),
          // 自定义代码块
          code: ({ node, inline, className, children, ...props }: any) => {
            if (inline) {
              return (
                <code className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-sm font-mono" {...props}>
                  {children}
                </code>
              );
            }
            return (
              <code className={className} {...props}>
                {children}
              </code>
            );
          },
          // 自定义引用块
          blockquote: ({ node, ...props }) => (
            <blockquote className="border-l-4 border-gray-300 dark:border-gray-600 pl-4 italic my-4" {...props} />
          ),
          // 自定义表格
          table: ({ node, ...props }) => (
            <div className="overflow-x-auto my-4">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700" {...props} />
            </div>
          ),
          th: ({ node, ...props }) => (
            <th className="px-4 py-2 bg-gray-50 dark:bg-gray-800 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider" {...props} />
          ),
          td: ({ node, ...props }) => (
            <td className="px-4 py-2 whitespace-nowrap text-sm" {...props} />
          ),
          // 自定义列表
          ul: ({ node, ...props }) => (
            <ul className="list-disc list-inside my-2 space-y-1" {...props} />
          ),
          ol: ({ node, ...props }) => (
            <ol className="list-decimal list-inside my-2 space-y-1" {...props} />
          ),
          // 自定义图片
          img: ({ node, ...props }) => (
            <img className="max-w-full h-auto rounded-lg my-4" {...props} />
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
