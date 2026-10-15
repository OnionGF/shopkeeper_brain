/**
 * 将现有 DAG 节点进度映射为「工具调用」展示名（方案 C UI 契约）。
 * 后端 progress 已可能是中文名（task_util._to_cn），因此同时兼容节点英文名与中文名。
 */
const NODE_TO_TOOL: Record<string, { id: string; label: string }> = {
  // English node names (DAG)
  item_name_confirmed_node: { id: 'understand', label: '理解问题 · 识别产品' },
  hybrid_vector_search_node: { id: 'search_kb', label: 'search_kb · 知识库检索' },
  hyde_vector_search_node: { id: 'search_kb', label: 'search_kb · 假设性检索' },
  rrf_merge_node: { id: 'merge', label: 'merge · 结果融合' },
  reranker_node: { id: 'rerank', label: 'rerank · 重排序' },
  web_mcp_search_node: { id: 'web_search', label: 'web_search · 联网搜索' },
  answer_output_node: { id: 'generate', label: '生成回答' },

  // Agent tool names (openai-agents)
  confirm_item: { id: 'understand', label: '理解问题 · 识别产品' },
  search_kb: { id: 'search_kb', label: 'search_kb · 知识库检索' },
  search_hyde: { id: 'search_kb', label: 'search_kb · 假设性检索' },
  web_search: { id: 'web_search', label: 'web_search · 联网搜索' },
  merge_and_rerank: { id: 'merge', label: 'merge · 融合重排' },
  generate_answer: { id: 'generate', label: '生成回答' },

  // Chinese names already emitted by backend
  确认问题产品: { id: 'understand', label: '理解问题 · 识别产品' },
  切片搜索: { id: 'search_kb', label: 'search_kb · 知识库检索' },
  '切片搜索(假设性文档)': { id: 'search_kb', label: 'search_kb · 假设性检索' },
  倒排融合: { id: 'merge', label: 'merge · 结果融合' },
  重排序: { id: 'rerank', label: 'rerank · 重排序' },
  网络搜索: { id: 'web_search', label: 'web_search · 联网搜索' },
  生成答案: { id: 'generate', label: '生成回答' },
}

export function mapNodeToTool(nodeOrCn: string): { id: string; label: string } {
  const key = String(nodeOrCn || '').trim()
  if (!key) return { id: 'tool', label: '工具调用' }
  return NODE_TO_TOOL[key] ?? { id: key, label: key }
}
