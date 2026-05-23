'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import Link from 'next/link';
import { useState } from 'react';
import { useAuthStore } from '@/stores/auth-store';
import dynamic from 'next/dynamic';

// Dynamically import MarkdownRenderer to avoid SSR issues
const MarkdownRenderer = dynamic(() => import('@/components/MarkdownRenderer'), {
  loading: () => <div className="animate-pulse space-y-4"><div className="h-4 bg-gray-200 rounded"></div></div>,
  ssr: false,
});

interface DocumentDetail {
  id: string;
  title: string;
  slug: string;
  content: string;
  excerpt: string;
  version: number;
  tags: any[];
  category: any;
  is_public: boolean;
  ai_editable: boolean;
  status: string;
  updated_at: string;
  created_at: string;
  author: {
    id: string;
    email: string;
    name: string;
    role: string;
  };
  last_editor?: {
    id: string;
    name: string;
  };
}

export default function DocumentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const slug = params.slug as string;
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState('');
  const { user } = useAuthStore();

  const { data: doc, isLoading, error } = useQuery({
    queryKey: ['document', slug],
    queryFn: async () => {
      const response = await apiClient.get(`/docs/${slug}`);
      return response.data;
    },
  });

  // Move all mutations to top level (before any early returns)
  const deleteMutation = useMutation({
    mutationFn: async () => {
      await apiClient.delete(`/docs/${doc?.id}`);
    },
    onSuccess: () => {
      alert('文档已移动到回收站');
      router.push('/docs');
    },
    onError: (err: any) => {
      alert(err.response?.data?.detail || '删除文档失败');
    },
  });

  if (isLoading) {
    return (
      <div className="flex-1 container mx-auto px-4 py-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
          <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded"></div>
        </div>
      </div>
    );
  }

  if (error || !doc) {
    return (
      <div className="flex-1 container mx-auto px-4 py-8">
        <div className="text-center">
          <p className="text-red-600 text-lg mb-4">文档不存在</p>
          <Link href="/docs" className="text-blue-600 hover:underline">
            ← 返回文档列表
          </Link>
        </div>
      </div>
    );
  }

  const handleSave = async () => {
    try {
      await apiClient.put(`/docs/${doc.id}`, {
        content: editContent,
        version: doc.version,
      });
      setIsEditing(false);
      // Refetch to get updated data
      window.location.reload();
    } catch (err) {
      console.error('Failed to save:', err);
      alert('保存文档失败');
    }
  };

  const handleDelete = () => {
    if (confirm('确定要删除此文档吗？文档将被移动到回收站。')) {
      deleteMutation.mutate();
    }
  };

  return (
    <div className="flex-1 container mx-auto px-4 py-8">
      {/* Breadcrumb */}
      <div className="mb-6">
        <Link href="/docs" className="text-blue-600 hover:underline">
          ← 返回文档列表
        </Link>
      </div>

      {/* Header */}
      <div className="mb-8 border-b pb-6">
        <div className="flex justify-between items-start mb-4">
          <h1 className="text-4xl font-bold">{doc.title}</h1>
          <div className="flex gap-2">
            {!isEditing ? (
              <>
                <button
                  onClick={() => {
                    setEditContent(doc.content);
                    setIsEditing(true);
                  }}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  编辑
                </button>
                {(user?.role === 'admin' || (user?.role === 'editor' && doc.author?.id === user?.id)) && (
                  <button
                    onClick={handleDelete}
                    disabled={deleteMutation.isPending}
                    className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
                  >
                    {deleteMutation.isPending ? '删除中...' : '删除'}
                  </button>
                )}
              </>
            ) : (
              <>
                <button
                  onClick={handleSave}
                  className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                >
                  保存
                </button>
                <button
                  onClick={() => setIsEditing(false)}
                  className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
                >
                  取消
                </button>
              </>
            )}
          </div>
        </div>

        <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
          <span>版本 {doc.version}</span>
          <span>•</span>
          <span>作者 {doc.author?.name || '未知'}</span>
          <span>•</span>
          <span>{new Date(doc.updated_at).toLocaleDateString()}</span>
          {doc.last_editor && (
            <>
              <span>•</span>
              <span>最后编辑者 {doc.last_editor.name}</span>
            </>
          )}
        </div>

        <div className="flex gap-2 mt-4">
          {doc.category && (
            <span className="px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full text-sm">
              {doc.category.name}
            </span>
          )}
          {doc.tags && doc.tags.map((tag: any) => (
            <span
              key={tag}
              className="px-3 py-1 bg-gray-100 dark:bg-gray-700 rounded-full text-sm"
            >
              {typeof tag === 'string' ? tag : tag.name}
            </span>
          ))}
        </div>
      </div>

      {/* Content */}
      {isEditing ? (
        <textarea
          value={editContent}
          onChange={(e) => setEditContent(e.target.value)}
          className="w-full h-96 p-4 border rounded font-mono text-sm"
        />
      ) : (
        <MarkdownRenderer content={doc.content} />
      )}

      {/* Footer */}
      <div className="mt-12 pt-6 border-t text-sm text-gray-500">
        <p>状态: {doc.status === 'published' ? '已发布' : doc.status === 'draft' ? '草稿' : '已归档'}</p>
        <p>公开: {doc.is_public ? '是' : '否'}</p>
        <p>AI可编辑: {doc.ai_editable ? '是' : '否'}</p>
      </div>
    </div>
  );
}
