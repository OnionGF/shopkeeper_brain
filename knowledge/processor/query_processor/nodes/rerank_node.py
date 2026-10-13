from typing import List, Dict, Any

from knowledge.processor.query_processor.base import BaseNode
from knowledge.processor.query_processor.state import QueryGraphState


class RerankerNode(BaseNode):
    name = "reranker_node"
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

    def _collect_rerank_inputs(self, state):
        pass
