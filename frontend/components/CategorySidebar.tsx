'use client';

import { useQuery } from '@tanstack/react-query';
import apiClient from '@/lib/api-client';
import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense } from 'react';

interface Category {
  id: string;
  name: string;
  slug: string;
  description?: string;
  parent_id?: string;
}

function CategoryContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const currentCategory = searchParams.get('category');

  const { data: categories, isLoading, error } = useQuery({
    queryKey: ['categories'],
    queryFn: async () => {
      const response = await apiClient.get('/categories');
      return response.data;
    },
  });

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-2">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-8 bg-gray-200 dark:bg-gray-700 rounded"></div>
        ))}
      </div>
    );
  }

  if (error) {
    return <p className="text-sm text-red-500">加载分类失败</p>;
  }

  const handleCategoryClick = (slug: string | null) => {
    if (slug) {
      router.push(`/docs?category=${slug}`);
    } else {
      router.push('/docs');
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold mb-3">分类</h3>
        <ul className="space-y-1">
          <li>
            <button
              onClick={() => handleCategoryClick(null)}
              className={`w-full text-left px-3 py-2 rounded transition-colors ${
                !currentCategory
                  ? 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200'
                  : 'hover:bg-gray-100 dark:hover:bg-gray-800'
              }`}
            >
              全部文档
            </button>
          </li>
          {categories?.map((category: Category) => (
            <li key={category.id}>
              <button
                onClick={() => handleCategoryClick(category.slug)}
                className={`w-full text-left px-3 py-2 rounded transition-colors ${
                  currentCategory === category.slug
                    ? 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200'
                    : 'hover:bg-gray-100 dark:hover:bg-gray-800'
                }`}
              >
                {category.name}
              </button>
            </li>
          ))}
        </ul>
      </div>

      {categories && categories.length === 0 && (
        <p className="text-sm text-gray-500">暂无分类</p>
      )}
    </div>
  );
}

export default function CategorySidebar() {
  return (
    <Suspense fallback={<div className="animate-pulse space-y-2"><div className="h-8 bg-gray-200 rounded"></div></div>}>
      <CategoryContent />
    </Suspense>
  );
}
