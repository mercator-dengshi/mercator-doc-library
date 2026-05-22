'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/lib/api-client';
import Link from 'next/link';

interface Document {
  id: string;
  title: string;
  slug: string;
  deleted_at: string;
  author: {
    name: string;
  };
}

export default function RecycleBin() {
  const queryClient = useQueryClient();
  const [confirmClear, setConfirmClear] = useState(false);

  const { data: trashedDocs, isLoading } = useQuery({
    queryKey: ['documents', 'trash'],
    queryFn: async () => {
      const response = await apiClient.get('/docs/trash');
      return response.data;
    },
  });

  const restoreMutation = useMutation({
    mutationFn: async (id: string) => {
      const response = await apiClient.post(`/docs/${id}/restore`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', 'trash'] });
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });

  const permanentDeleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/docs/${id}/permanent`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', 'trash'] });
    },
  });

  const clearTrashMutation = useMutation({
    mutationFn: async () => {
      await apiClient.post('/docs/trash/clear');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', 'trash'] });
      setConfirmClear(false);
    },
  });

  const handleRestore = (doc: Document) => {
    if (confirm(`恢复“${doc.title}”？`)) {
      restoreMutation.mutate(doc.id);
    }
  };

  const handlePermanentDelete = (doc: Document) => {
    if (confirm(`永久删除“${doc.title}”？此操作无法撤消！`)) {
      permanentDeleteMutation.mutate(doc.id);
    }
  };

  const handleClearAll = () => {
    if (confirm(`确定要永久删除回收站中的全部 ${trashedDocs?.length || 0} 个文档吗？此操作无法撤消！`)) {
      clearTrashMutation.mutate();
    }
  };

  if (isLoading) {
    return <div className="animate-pulse space-y-4"><div className="h-16 bg-gray-200 rounded"></div></div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold">回收站</h3>
          <p className="text-sm text-gray-500">{trashedDocs?.length || 0} 个已删除文档</p>
        </div>
        {trashedDocs && trashedDocs.length > 0 && (
          <div className="flex gap-2">
            {confirmClear ? (
              <div className="flex gap-2 items-center">
                <span className="text-sm text-red-600">这将永久删除所有项目！</span>
                <button
                  onClick={handleClearAll}
                  disabled={clearTrashMutation.isPending}
                  className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
                >
                  {clearTrashMutation.isPending ? '清空中...' : '确认'}
                </button>
                <button
                  onClick={() => setConfirmClear(false)}
                  className="px-3 py-1 text-sm border rounded hover:bg-gray-50"
                >
                  取消
                </button>
              </div>
            ) : (
              <button
                onClick={() => setConfirmClear(true)}
                className="px-3 py-1 text-sm text-red-600 border border-red-600 rounded hover:bg-red-50"
              >
                清空全部
              </button>
            )}
          </div>
        )}
      </div>

      <div className="space-y-2">
        {trashedDocs?.map((doc: Document) => (
          <div
            key={doc.id}
            className="flex items-center justify-between p-4 bg-white dark:bg-gray-800 border rounded hover:shadow-sm"
          >
            <div className="flex-1">
              <Link
                href={`/docs/${doc.slug}`}
                className="font-medium text-blue-600 hover:underline"
              >
                {doc.title}
              </Link>
              <div className="text-sm text-gray-500 mt-1">
                删除者 {doc.author?.name || '未知'} •{' '}
                {new Date(doc.deleted_at).toLocaleDateString()}
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => handleRestore(doc)}
                disabled={restoreMutation.isPending}
                className="px-3 py-1 text-sm text-green-600 border border-green-600 rounded hover:bg-green-50 disabled:opacity-50"
              >
                恢复
              </button>
              <button
                onClick={() => handlePermanentDelete(doc)}
                disabled={permanentDeleteMutation.isPending}
                className="px-3 py-1 text-sm text-red-600 border border-red-600 rounded hover:bg-red-50 disabled:opacity-50"
              >
                彻底删除
              </button>
            </div>
          </div>
        ))}
        {trashedDocs?.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            <div className="text-4xl mb-2">🗑️</div>
            <p>回收站为空</p>
          </div>
        )}
      </div>
    </div>
  );
}
