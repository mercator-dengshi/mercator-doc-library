'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/lib/api-client';

interface Category {
  id: string;
  name: string;
  slug: string;
  description?: string;
  document_count: number;
  icon?: string;
  sort_order: number;
  is_visible: boolean;
}

export default function CategoryManager() {
  const [showForm, setShowForm] = useState(false);
  const [editingCategory, setEditingCategory] = useState<Category | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    slug: '',
    description: '',
    icon: undefined as string | undefined,
  });

  const queryClient = useQueryClient();

  const { data: categories, isLoading } = useQuery({
    queryKey: ['categories'],
    queryFn: async () => {
      const response = await apiClient.get('/categories');
      return response.data;
    },
  });

  const createMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await apiClient.post('/categories', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] });
      setShowForm(false);
      setFormData({ name: '', slug: '', description: '', icon: undefined });
    },
  });

  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: any }) => {
      const response = await apiClient.put(`/categories/${id}`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] });
      setEditingCategory(null);
      setFormData({ name: '', slug: '', description: '', icon: undefined });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/categories/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // 清理空字符串，改为 undefined
    const cleanData = {
      ...formData,
      icon: formData.icon || undefined,
      description: formData.description || undefined,
    };
    
    if (editingCategory) {
      updateMutation.mutate({ id: editingCategory.id, data: cleanData });
    } else {
      createMutation.mutate(cleanData);
    }
  };

  const handleEdit = (category: Category) => {
    setEditingCategory(category);
    setFormData({
      name: category.name,
      slug: category.slug,
      description: category.description || '',
      icon: category.icon || undefined,
    });
    setShowForm(true);
  };

  const handleDelete = (category: Category) => {
    if (category.document_count > 0) {
      alert(`无法删除"${category.name}" - 该分类下有 ${category.document_count} 个文档。请先移动或删除这些文档。`);
      return;
    }
    if (confirm(`确定要删除"${category.name}"吗？`)) {
      deleteMutation.mutate(category.id);
    }
  };

  if (isLoading) {
    return <div className="animate-pulse space-y-2"><div className="h-8 bg-gray-200 rounded"></div></div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">分类管理</h3>
        <button
          onClick={() => {
            setEditingCategory(null);
            setFormData({ name: '', slug: '', description: '', icon: undefined });
            setShowForm(!showForm);
          }}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          {showForm ? '取消' : '+ 添加分类'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg space-y-3">
          <div>
            <label className="block text-sm font-medium mb-1">名称 *</label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border rounded dark:bg-gray-700 dark:border-gray-600"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">URL 标识符 *</label>
            <input
              type="text"
              required
              value={formData.slug}
              onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
              className="w-full px-3 py-2 border rounded dark:bg-gray-700 dark:border-gray-600"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">描述</label>
            <textarea
              value={formData.description || ''}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={2}
              className="w-full px-3 py-2 border rounded dark:bg-gray-700 dark:border-gray-600"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">图标（emoji）</label>
            <input
              type="text"
              value={formData.icon || ''}
              onChange={(e) => setFormData({ ...formData, icon: e.target.value })}
              className="w-full px-3 py-2 border rounded dark:bg-gray-700 dark:border-gray-600"
              placeholder="例如: 📁"
            />
          </div>
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={createMutation.isPending || updateMutation.isPending}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {createMutation.isPending || updateMutation.isPending
                ? '保存中...'
                : editingCategory
                ? '更新'
                : '创建'}
            </button>
          </div>
        </form>
      )}

      <div className="space-y-2">
        {categories?.map((category: Category) => (
          <div
            key={category.id}
            className="flex items-center justify-between p-3 bg-white dark:bg-gray-800 border rounded hover:shadow-sm"
          >
            <div className="flex items-center gap-3">
              {category.icon && <span className="text-xl">{category.icon}</span>}
              <div>
                <div className="font-medium">{category.name}</div>
                <div className="text-sm text-gray-500">{category.document_count} 个文档</div>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => handleEdit(category)}
                className="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded"
              >
                编辑
              </button>
              <button
                onClick={() => handleDelete(category)}
                className="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded"
              >
                删除
              </button>
            </div>
          </div>
        ))}
        {categories?.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            暂无分类，创建一个开始吧！
          </div>
        )}
      </div>
    </div>
  );
}
