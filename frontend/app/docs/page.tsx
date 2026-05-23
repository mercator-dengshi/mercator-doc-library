'use client';

import { useQuery } from '@tanstack/react-query';
import apiClient from '@/lib/api-client';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import CategorySidebar from '@/components/CategorySidebar';
import NewDocumentModal from '@/components/NewDocumentModal';
import { Suspense, useState } from 'react';
import { Plus, Search, X } from 'lucide-react';

interface Document {
  id: string;
  title: string;
  slug: string;
  excerpt: string;
  version: number;
  tags: any[];
  category: any;
  updated_at: string;
  author: {
    id: string;
    email: string;
    name: string;
    role: string;
    is_active: boolean;
    created_at: string;
  };
}

interface SearchResult {
  id: string;
  title: string;
  slug: string;
  excerpt?: string;
  content_preview?: string;
  score: number;
  match_type: string;
  category?: any;
  tags: string[];
  updated_at: string;
}

function DocsContent() {
  const searchParams = useSearchParams();
  const categorySlug = searchParams.get('category');
  const [showNewDocModal, setShowNewDocModal] = useState(false);
  
  // 搜索状态
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const { data, isLoading, error } = useQuery({
    queryKey: ['documents', categorySlug],
    queryFn: async () => {
      const url = categorySlug ? `/docs?category=${categorySlug}` : '/docs';
      const response = await apiClient.get(url);
      return response.data; // API returns array directly
    },
  });

  // 搜索处理函数
  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    setHasSearched(true);
    
    console.log('=== 搜索调试信息 ===');
    console.log('搜索关键词:', searchQuery.trim());
    console.log('API URL:', '/search/');
    
    try {
      const response = await apiClient.post('/search/', {
        query: searchQuery.trim(),
        limit: 20
      });
      
      console.log('API响应状态:', response.status);
      console.log('搜索结果数量:', response.data.results?.length || 0);
      setSearchResults(response.data.results || []);
    } catch (err) {
      console.error('搜索失败:', err);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  // 清除搜索
  const clearSearch = () => {
    setSearchQuery('');
    setSearchResults([]);
    setHasSearched(false);
  };

  if (isLoading) {
    return (
      <div className="flex-1 container mx-auto px-4 py-8">
        <div className="animate-pulse space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-24 bg-gray-200 dark:bg-gray-700 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 container mx-auto px-4 py-8">
        <div className="text-center text-red-600">
          <p className="text-lg font-semibold mb-2">加载文档失败</p>
          <p className="text-sm">{(error as Error).message}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 container mx-auto px-4 py-8">
      <div className="mb-8 flex justify-between items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold">文档中心</h1>
        </div>
        <button
          onClick={() => setShowNewDocModal(true)}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2 shadow-lg whitespace-nowrap flex-shrink-0"
        >
          <Plus className="w-5 h-5" />
          新建
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Sidebar */}
        <aside className="lg:col-span-1">
          <div className="sticky top-4">
            <CategorySidebar />
          </div>
        </aside>

        {/* Main Content */}
        <main className="lg:col-span-3">
          {/* Search Bar */}
          <form onSubmit={handleSearch} className="mb-8">
            <div className="flex gap-2">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="搜索文档... (支持自然语言查询)"
                className="flex-1 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800"
              />
              <button
                type="submit"
                disabled={isSearching || !searchQuery.trim()}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2 whitespace-nowrap flex-shrink-0"
              >
                {isSearching ? (
                  <>
                    <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    搜索中...
                  </>
                ) : (
                  <>
                    <Search className="w-5 h-5" />
                    搜索
                  </>
                )}
              </button>
              {hasSearched && (
                <button
                  type="button"
                  onClick={clearSearch}
                  className="px-4 py-3 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors whitespace-nowrap flex-shrink-0 flex items-center gap-2"
                >
                  <X className="w-4 h-4" />
                  清除
                </button>
              )}
            </div>
          </form>

          {/* Search Results or Document List */}
          {hasSearched ? (
            <>
              {/* Search Results */}
              <div className="mb-4">
                <h2 className="text-xl font-semibold mb-2">
                  搜索结果 {searchResults.length > 0 && `(${searchResults.length} 条)`}
                </h2>
              </div>
              
              {isSearching ? (
                <div className="text-center py-12">
                  <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-blue-600 border-t-transparent"></div>
                  <p className="mt-4 text-gray-600 dark:text-gray-400">AI正在理解搜索意图...</p>
                </div>
              ) : searchResults.length > 0 ? (
                <div className="grid gap-4">
                  {searchResults.map((result: SearchResult) => (
                    <Link
                      key={result.id}
                      href={`/docs/${result.slug}`}
                      className="block p-6 border border-gray-200 dark:border-gray-700 rounded-lg hover:shadow-md transition-shadow bg-white dark:bg-gray-800"
                    >
                      <div className="flex justify-between items-start mb-2">
                        <h2 className="text-xl font-semibold text-blue-600 dark:text-blue-400">
                          {result.title}
                        </h2>
                        <div className="flex items-center gap-2">
                          <span className="text-xs px-2 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 rounded">
                            {(result.score * 100).toFixed(0)}% 匹配
                          </span>
                        </div>
                      </div>
                      
                      {result.content_preview && (
                        <p className="text-gray-600 dark:text-gray-400 mb-3 text-sm">
                          {result.content_preview}
                        </p>
                      )}
                      
                      <div className="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
                        {result.category && (
                          <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded">
                            {result.category.name}
                          </span>
                        )}
                        {result.tags.length > 0 && (
                          <div className="flex gap-1">
                            {result.tags.slice(0, 3).map((tag, idx) => (
                              <span key={idx} className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded">
                                {tag}
                              </span>
                            ))}
                          </div>
                        )}
                        <span className="ml-auto">
                          {new Date(result.updated_at).toLocaleDateString('zh-CN')}
                        </span>
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <svg className="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p className="text-gray-600 dark:text-gray-400 text-lg mb-2">没有找到相关文档</p>
                  <p className="text-gray-500 dark:text-gray-500 text-sm">尝试使用不同的关键词或短语</p>
                </div>
              )}
            </>
          ) : (
            /* Document List */
            <div className="grid gap-4">
              {data?.map((doc: Document) => (
                <Link
                  key={doc.id}
                  href={`/docs/${doc.slug}`}
                  className="block p-6 border border-gray-200 dark:border-gray-700 rounded-lg hover:shadow-md transition-shadow bg-white dark:bg-gray-800"
                >
                  <div className="flex justify-between items-start mb-2">
                    <h2 className="text-xl font-semibold text-blue-600 dark:text-blue-400">
                      {doc.title}
                    </h2>
                    <span className="text-sm text-gray-500 dark:text-gray-400">
                      v{doc.version}
                    </span>
                  </div>
                  <p className="text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
                    {doc.excerpt}
                  </p>
                  <div className="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
                    {doc.category && (
                      <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded">
                        {doc.category.name}
                      </span>
                    )}
                    {doc.tags && doc.tags.map((tag: any) => (
                      <span
                        key={tag}
                        className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded"
                      >
                        {typeof tag === 'string' ? tag : tag.name}
                      </span>
                    ))}
                    <span className="ml-auto">
                      {new Date(doc.updated_at).toLocaleDateString()}
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </main>
      </div>

      {/* New Document Modal */}
      {showNewDocModal && (
        <NewDocumentModal onClose={() => setShowNewDocModal(false)} />
      )}
    </div>
  );
}

export default function DocsPage() {
  return (
    <Suspense fallback={<div className="flex-1 container mx-auto px-4 py-8"><div className="animate-pulse space-y-4"><div className="h-24 bg-gray-200 rounded"></div></div></div>}>
      <DocsContent />
    </Suspense>
  );
}
