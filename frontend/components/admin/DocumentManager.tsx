'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/lib/api-client';
import { FileText, Eye, Edit, Trash2 } from 'lucide-react';
import Link from 'next/link';

export default function DocumentManager() {
  const queryClient = useQueryClient();
  
  const { data: documents, isLoading } = useQuery({
    queryKey: ['admin-documents'],
    queryFn: async () => {
      const response = await apiClient.get('/docs/?limit=100');
      return response.data;
    }
  });

  const deleteDocumentMutation = useMutation({
    mutationFn: async (docId: string) => {
      await apiClient.delete(`/docs/${docId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-documents'] });
      alert('文档已删除');
    },
    onError: (err: any) => {
      alert(err.response?.data?.detail || '删除文档失败');
    },
  });

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <div className="animate-pulse space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-16 bg-gray-200 dark:bg-gray-700 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <FileText className="text-blue-600 dark:text-blue-400" size={24} />
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            文档管理
          </h2>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          共 {documents?.length || 0} 个文档
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200 dark:border-gray-700">
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-700 dark:text-gray-300">标题</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-700 dark:text-gray-300">状态</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-700 dark:text-gray-300">公开</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-700 dark:text-gray-300">更新时间</th>
              <th className="text-right py-3 px-4 text-sm font-medium text-gray-700 dark:text-gray-300">操作</th>
            </tr>
          </thead>
          <tbody>
            {documents?.map((doc: any) => (
              <tr key={doc.id} className="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                <td className="py-3 px-4">
                  <div className="font-medium text-gray-900 dark:text-white">{doc.title}</div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">{doc.slug}</div>
                </td>
                <td className="py-3 px-4">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    doc.status === 'published' 
                      ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                      : doc.status === 'draft'
                      ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400'
                      : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-400'
                  }`}>
                    {doc.status === 'published' ? '已发布' : doc.status === 'draft' ? '草稿' : '已归档'}
                  </span>
                </td>
                <td className="py-3 px-4">
                  <span className={`text-xs ${doc.is_public ? 'text-green-600 dark:text-green-400' : 'text-gray-500 dark:text-gray-400'}`}>
                    {doc.is_public ? '是' : '否'}
                  </span>
                </td>
                <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400">
                  {new Date(doc.updated_at).toLocaleDateString('zh-CN')}
                </td>
                <td className="py-3 px-4 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <Link
                      href={`/docs/${doc.slug}`}
                      className="p-2 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded transition-colors"
                      title="查看"
                    >
                      <Eye size={16} />
                    </Link>
                    <Link
                      href={`/docs/${doc.slug}`}
                      className="p-2 text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 rounded transition-colors"
                      title="编辑（在详情页）"
                    >
                      <Edit size={16} />
                    </Link>
                    <button
                      onClick={() => {
                        if (confirm(`确定要删除文档 "${doc.title}" 吗？此操作将把文档移至回收站。`)) {
                          deleteDocumentMutation.mutate(doc.id);
                        }
                      }}
                      disabled={deleteDocumentMutation.isPending}
                      className="p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors disabled:opacity-50"
                      title="删除"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {(!documents || documents.length === 0) && (
        <div className="text-center py-12 text-gray-500 dark:text-gray-400">
          <FileText size={48} className="mx-auto mb-4 opacity-50" />
          <p>暂无文档</p>
        </div>
      )}
    </div>
  );
}
