'use client';

import { useState } from 'react';
import { Code, Copy, CheckCircle, ExternalLink, Key } from 'lucide-react';

export default function APIDocs() {
  const [copiedExample, setCopiedExample] = useState<string | null>(null);

  const copyToClipboard = (text: string, exampleId: string) => {
    navigator.clipboard.writeText(text);
    setCopiedExample(exampleId);
    setTimeout(() => setCopiedExample(null), 2000);
  };

  const apiBaseUrl = typeof window !== 'undefined' 
    ? `${window.location.protocol}//${window.location.host}/api/v1`
    : 'http://localhost:8000/api/v1';

  const examples = [
    {
      id: 'create-doc',
      title: '创建文档',
      method: 'POST',
      endpoint: '/documents/',
      description: '使用API密钥创建新文档',
      code: `curl -X POST ${apiBaseUrl}/docs/ \\
  -H "X-API-Key: YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "title": "我的新文档",
    "slug": "my-new-document",
    "content": "# 文档标题\n\n这里是文档内容...",
    "is_public": true,
    "ai_editable": false
  }'`,
      response: `{
  "id": "doc-uuid",
  "title": "我的新文档",
  "slug": "my-new-document",
  "version": 1,
  "status": "published",
  "author": {
    "name": "用户名"
  },
  "created_at": "2026-05-23T03:52:06Z"
}`
    },
    {
      id: 'update-doc',
      title: '更新文档',
      method: 'PUT',
      endpoint: '/documents/{doc_id}',
      description: '更新现有文档的内容和元数据',
      code: `curl -X PUT ${apiBaseUrl}/docs/doc-uuid \\
  -H "X-API-Key: YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "title": "更新后的标题",
    "content": "更新后的内容...",
    "version": 1
  }'`,
      response: `{
  "id": "doc-uuid",
  "title": "更新后的标题",
  "version": 2,
  "updated_at": "2026-05-23T03:54:45Z"
}`
    },
    {
      id: 'get-doc',
      title: '获取文档列表',
      method: 'GET',
      endpoint: '/documents/',
      description: '查询文档列表,支持分页和分类过滤',
      code: `# 获取所有文档(分页)
curl -X GET "${apiBaseUrl}/docs/?skip=0&limit=20" \\
  -H "X-API-Key: YOUR_API_KEY"

# 按分类筛选
curl -X GET "${apiBaseUrl}/docs/?category=project-docs" \\
  -H "X-API-Key: YOUR_API_KEY"`,
      response: `[
  {
    "id": "doc-uuid",
    "title": "文档标题",
    "slug": "doc-slug",
    "excerpt": "文档摘要...",
    "version": 1,
    "category": {"name": "技术"}
  }
]`
    },
    {
      id: 'get-single-doc',
      title: '获取单个文档',
      method: 'GET',
      endpoint: '/documents/{slug}',
      description: '通过slug获取文档详情',
      code: `curl -X GET ${apiBaseUrl}/docs/my-new-document \\
  -H "X-API-Key: YOUR_API_KEY"`,
      response: `{
  "id": "doc-uuid",
  "title": "AI写作最佳实践",
  "content": "# 完整内容...",
  "version": 1,
  "author": {"name": "作者名"},
  "category": {"name": "技术"}
}`
    },
    {
      id: 'delete-doc',
      title: '删除文档(软删除)',
      method: 'DELETE',
      endpoint: '/docs/{doc_id}',
      description: '将文档移入回收站(可恢复)',
      code: `curl -X DELETE ${apiBaseUrl}/docs/doc-uuid \\
  -H "X-API-Key: YOUR_API_KEY"`,
      response: `HTTP 204 No Content`
    },
    {
      id: 'restore-doc',
      title: '恢复文档',
      method: 'POST',
      endpoint: '/docs/{doc_id}/restore',
      description: '从回收站恢复已删除的文档',
      code: `curl -X POST ${apiBaseUrl}/docs/doc-uuid/restore \\
  -H "X-API-Key: YOUR_API_KEY"`,
      response: `{
  "id": "doc-uuid",
  "title": "已恢复的文档",
  "deleted_at": null
}`
    }
  ];

  const pythonExample = `import requests

API_BASE_URL = "${apiBaseUrl}"
API_KEY = "YOUR_API_KEY"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# 创建文档
response = requests.post(
    f"{API_BASE_URL}/docs/",
    headers=headers,
    json={
        "title": "我的文档",
        "slug": "my-document",
        "content": "# 内容",
        "is_public": true
    }
)
print(f"创建成功: {response.json()['id']}")

# 更新文档
doc_id = response.json()['id']
requests.put(
    f"{API_BASE_URL}/docs/{doc_id}",
    headers=headers,
    json={"title": "更新后的标题", "version": 1}
)

# 获取文档列表
response = requests.get(
    f"{API_BASE_URL}/docs/?limit=10",
    headers=headers
)
docs = response.json()
print(f"共{len(docs)}个文档")

# 删除文档
requests.delete(
    f"{API_BASE_URL}/docs/{doc_id}",
    headers=headers
)`;

  const javascriptExample = `const API_BASE_URL = "${apiBaseUrl}";
const API_KEY = "YOUR_API_KEY";

const headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
};

// 创建文档
async function createDocument() {
    const response = await fetch(\`\${API_BASE_URL}/documents/\`, {
        method: "POST",
        headers: headers,
        body: JSON.stringify({
            title: "我的文档",
            slug: "my-document",
            content: "# 内容",
            category_id: "uuid-here"
        })
    });
    const doc = await response.json();
    console.log("创建成功:", doc.id);
    return doc;
}

// 更新文档
async function updateDocument(docId) {
    await fetch(\`\${API_BASE_URL}/documents/\${docId}\`, {
        method: "PUT",
        headers: headers,
        body: JSON.stringify({
            title: "更新后的标题"
        })
    });
}

// 获取文档列表
async function listDocuments() {
    const response = await fetch(
        \`\${API_BASE_URL}/documents/?limit=10\`,
        { headers }
    );
    const docs = await response.json();
    console.log(\`共\${docs.length}个文档\`);
    return docs;
}

// 删除文档
async function deleteDocument(docId) {
    await fetch(\`\${API_BASE_URL}/documents/\${docId}\`, {
        method: "DELETE",
        headers: headers
    });
}`;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          文档CRUD API使用指南
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          外部工具(如OpenClaw、Cursor等)可通过API密钥调用以下接口操作文档
        </p>
      </div>

      {/* Authentication Notice */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Key className="text-blue-600 dark:text-blue-400 flex-shrink-0 mt-1" size={20} />
          <div>
            <h3 className="font-semibold text-blue-900 dark:text-blue-300 mb-2">
              认证方式
            </h3>
            <p className="text-sm text-blue-800 dark:text-blue-400 mb-2">
              所有API请求必须在Header中包含 <code className="bg-blue-100 dark:bg-blue-800 px-2 py-1 rounded">X-API-Key: YOUR_API_KEY</code>
            </p>
            <div className="text-xs text-blue-700 dark:text-blue-500 space-y-1">
              <p>💡 提示: 在上方“API密钥”标签页中创建API密钥</p>
              <p>✅ 已测试: 创建、查询、更新、删除文档功能全部正常</p>
              <p>📝 端点路径: /api/v1/docs/ (不是 /documents/)</p>
            </div>
          </div>
        </div>
      </div>

      {/* API Examples */}
      <div className="space-y-6">
        {examples.map((example) => (
          <div key={example.id} className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
            {/* Example Header */}
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className={`px-3 py-1 rounded text-xs font-bold ${
                    example.method === 'GET' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
                    example.method === 'POST' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400' :
                    example.method === 'PUT' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400' :
                    'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                  }`}>
                    {example.method}
                  </span>
                  <code className="text-sm font-mono text-gray-700 dark:text-gray-300">
                    {example.endpoint}
                  </code>
                </div>
                <button
                  onClick={() => copyToClipboard(example.code, example.id)}
                  className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
                >
                  {copiedExample === example.id ? (
                    <>
                      <CheckCircle size={16} className="text-green-600" />
                      <span className="text-green-600">已复制</span>
                    </>
                  ) : (
                    <>
                      <Copy size={16} />
                      <span>复制</span>
                    </>
                  )}
                </button>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                {example.description}
              </p>
            </div>

            {/* Code Block */}
            <div className="p-6">
              <div className="mb-4">
                <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">
                  请求示例
                </h4>
                <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm font-mono">
                  <code>{example.code}</code>
                </pre>
              </div>

              {example.response && (
                <div>
                  <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">
                    响应示例
                  </h4>
                  <pre className="bg-gray-50 dark:bg-gray-900 text-gray-800 dark:text-gray-200 p-4 rounded-lg overflow-x-auto text-sm font-mono border border-gray-200 dark:border-gray-700">
                    <code>{example.response}</code>
                  </pre>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Programming Language Examples */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Python Example */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Code size={20} className="text-blue-600" />
              <h3 className="font-semibold text-gray-900 dark:text-white">Python 示例</h3>
            </div>
            <button
              onClick={() => copyToClipboard(pythonExample, 'python')}
              className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
            >
              {copiedExample === 'python' ? (
                <>
                  <CheckCircle size={16} className="text-green-600" />
                  <span className="text-green-600">已复制</span>
                </>
              ) : (
                <>
                  <Copy size={16} />
                  <span>复制</span>
                </>
              )}
            </button>
          </div>
          <div className="p-6">
            <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm font-mono">
              <code>{pythonExample}</code>
            </pre>
          </div>
        </div>

        {/* JavaScript Example */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Code size={20} className="text-yellow-600" />
              <h3 className="font-semibold text-gray-900 dark:text-white">JavaScript 示例</h3>
            </div>
            <button
              onClick={() => copyToClipboard(javascriptExample, 'javascript')}
              className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
            >
              {copiedExample === 'javascript' ? (
                <>
                  <CheckCircle size={16} className="text-green-600" />
                  <span className="text-green-600">已复制</span>
                </>
              ) : (
                <>
                  <Copy size={16} />
                  <span>复制</span>
                </>
              )}
            </button>
          </div>
          <div className="p-6">
            <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm font-mono">
              <code>{javascriptExample}</code>
            </pre>
          </div>
        </div>
      </div>

      {/* Permissions Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50">
          <h3 className="font-semibold text-gray-900 dark:text-white">权限说明</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-900/50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">操作</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">人类用户(JWT)</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">AI智能体(API Key)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              <tr>
                <td className="px-6 py-4 text-sm text-gray-900 dark:text-white">创建文档</td>
                <td className="px-6 py-4 text-sm"><span className="text-green-600">✅</span></td>
                <td className="px-6 py-4 text-sm"><span className="text-green-600">✅</span></td>
              </tr>
              <tr>
                <td className="px-6 py-4 text-sm text-gray-900 dark:text-white">更新文档</td>
                <td className="px-6 py-4 text-sm"><span className="text-green-600">✅</span></td>
                <td className="px-6 py-4 text-sm"><span className="text-green-600">✅</span></td>
              </tr>
              <tr>
                <td className="px-6 py-4 text-sm text-gray-900 dark:text-white">删除文档(软删除)</td>
                <td className="px-6 py-4 text-sm"><span className="text-green-600">✅</span></td>
                <td className="px-6 py-4 text-sm"><span className="text-green-600">✅</span></td>
              </tr>
              <tr>
                <td className="px-6 py-4 text-sm text-gray-900 dark:text-white">恢复文档</td>
                <td className="px-6 py-4 text-sm"><span className="text-green-600">✅</span></td>
                <td className="px-6 py-4 text-sm"><span className="text-green-600">✅</span></td>
              </tr>
              <tr>
                <td className="px-6 py-4 text-sm text-gray-900 dark:text-white">清空回收站</td>
                <td className="px-6 py-4 text-sm"><span className="text-green-600">✅ 仅管理员</span></td>
                <td className="px-6 py-4 text-sm"><span className="text-red-600">❌ 禁止</span></td>
              </tr>
              <tr>
                <td className="px-6 py-4 text-sm text-gray-900 dark:text-white">永久删除</td>
                <td className="px-6 py-4 text-sm"><span className="text-green-600">✅ 仅管理员</span></td>
                <td className="px-6 py-4 text-sm"><span className="text-red-600">❌ 禁止</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
