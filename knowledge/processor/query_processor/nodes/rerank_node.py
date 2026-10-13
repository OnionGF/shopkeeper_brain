import math
from typing import List, Dict, Any

from FlagEmbedding import FlagReranker

from knowledge.processor.query_processor.base import BaseNode
from knowledge.processor.query_processor.state import QueryGraphState
from knowledge.utils.client.ai_clients import AIClients



class RerankerNode(BaseNode):
    name = "reranker_node"

    @staticmethod
    def _sigmoid(score: float) -> float:
        """sigmoid归一化，将 (-∞, +∞) 映射到 (0, 1)"""
        return 1.0 / (1.0 + math.exp(-score))

    def process(self, state:QueryGraphState) -> QueryGraphState:
        """

        Args:
            state:

        Returns:

        """

        # 1、获取用户问题
        user_query = state.get('rewritten_query') or state.get('original_query')
        # 2、获取两路检索结果（本地 、远程）
        rerank_outputs :List[Dict[str, Any]] = self._collect_rerank_inputs(state)

        # 3、利用Reranker进行精排
        refine_docs:List[Dict[str, Any]]= self._refine_rank(user_query, rerank_outputs)
        

    def _collect_rerank_inputs(self, state: QueryGraphState) -> List[Dict[str, Any]]:
        """
        获取两路检索结果(本地检索结果、远程检索结果)
        Args:
            state:

        Returns:

        """
        final_docs = []
        # 1. 获取本地检索结果
        rrf_chunks = state.get('rrf_chunks') or []
        for chunk in rrf_chunks:
            # 1. 判断chunk
            if not chunk or not isinstance(chunk, dict):
                continue

            # 2. 获取chunk的信息
            # 2.1 获取chunk中content
            content = chunk.get('content', '')
            if not content:
                continue
            # 2.2 获取chunk中的title
            title = chunk.get('title', '')

            # 2.3 获取chunk中的chunk_id(一定有)
            chunk_id = chunk.get('chunk_id')

            # 3. 格式化文档(格式化本地)
            formated_local_doc = self._format_doc(content=content, chunk_id=chunk_id, title=title, source="local")

            final_docs.append(formated_local_doc)

        # 2. 获取远程检索结果
        web_search_docs = state.get('web_search_docs') or []
        for doc in web_search_docs:

            # 1. 判断doc
            if not doc or not isinstance(doc, dict):
                continue

            # 2. 获取content
            content = doc.get('snippet', '')
            # 2.3 获取title
            title = doc.get('title', '')
            # 2.4 获取url
            url = doc.get('url', '')

            # 3. 格式化文档(格式化远程)
            formated_web_doc = self._format_doc(content=content, title=title, url=url, source="web")
            final_docs.append(formated_web_doc)

        self.logger.info(f"获取Reranker阶段需要的搜索结果个数{len(final_docs)}")
        return final_docs

    def _format_doc(self, content: str, chunk_id: int = None, title: str = "", url: str = "", source: str = ""):
        """
        格式化本地以及远程检索到的文档
        Args:
            content:
            chunk_id:
            title:
            source:
            url:

        Returns:

        """
        return {
            "content": content,
            "chunk_id": chunk_id,
            "title": title,
            "url": url,
            "source": source
        }

    def _refine_rank(self, user_query: str, rerank_outputs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        reranker模型进行打分&排序【精排】
        Args:
            user_query:  用户的查询
            rerank_outputs: 本地和远程融合后的检索结果

        Returns:
            Dict[str,Any]:{"score","","other":"..."}

        """
        if not rerank_outputs:
            return []
        # 1. 获取重排序模型
        try:
            rerank_client: FlagReranker = AIClients.get_bge_m3_rerank_client()
        except ConnectionError as e:
            self.logger.error(f"获取BGE-M3重排序模型失败 原因:{str(e)}")
            return [{**d, "score": None} for d in rerank_outputs]

        # 2. 构建Q->D的pair对
        query_doc_pairs = [(user_query, d.get('content')) for d in rerank_outputs]

        try:
            # 3. 计算(注意：BGE-M3重排序模型计算出来的得分可以很大也可以很小(负无穷大,正无穷大))
            rerank_scores = rerank_client.compute_score(sentence_pairs=query_doc_pairs)

            # 4.组合最终结果
            doc_score = [{**d, "score": self._sigmoid(float(s))} for d, s in zip(rerank_outputs, rerank_scores)]

            # 5. 排序
            sorted_doc_score = sorted(doc_score, key=lambda x: x['score'], reverse=True)

            # 6. 返回
            return sorted_doc_score
        except Exception as e:
            self.logger.error(f"BGE-M3重排序模型计算分数失败 原因：{str(e)}")
            return [{**d, "score": None} for d in rerank_outputs]


if __name__ == "__main__":
    print("=" * 60)
    print("开始测试: 重排序节点 (RerankNode)")
    print("=" * 60)

    mock_state = {
        "rewritten_query": "怎么测这块主板的短路问题？",
        "rrf_chunks": [
            {"chunk_id": "local_1", "title": "主板维修手册",
             "content": "主板短路通常表现为通电后风扇转一下就停，可以使用万用表的蜂鸣档测量。"},
            {"chunk_id": "local_2", "title": "闲聊",
             "content": "今天中午去吃猪脚饭吧，这块主板外观很漂亮。"},
        ],
        "web_search_docs": [
            {"url": "https://example.com/repair", "title": "短路查修指南",
             "snippet": "主板通电前先打各主供电电感的对地阻值，阻值偏低就是短路。"},
            {"url": "https://example.com/news", "title": "科技新闻",
             "snippet": "苹果发布新款手机，A系列芯片性能提升20%。"},
        ],
    }

    print("【输入状态】:")
    print(f"  查询: {mock_state['rewritten_query']}")
    print(f"  本地文档: {len(mock_state['rrf_chunks'])} 篇")
    print(f"  网络文档: {len(mock_state['web_search_docs'])} 篇")
    print("-" * 60)

    node = RerankerNode()
    result = node.process(mock_state)
    print(result)