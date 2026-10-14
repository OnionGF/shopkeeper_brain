from typing import Tuple, List, Dict, Any, Union

from knowledge.processor.query_processor.base import BaseNode
from knowledge.processor.query_processor.exceptions import StateFieldError
from knowledge.processor.query_processor.state import QueryGraphState
from knowledge.utils.client.ai_clients import AIClients
from knowledge.utils.client.storage_clients import StorageClients
from knowledge.utils.embedding_util import generate_bge_m3_hybrid_vectors
from knowledge.utils.milvus_util import create_hybrid_search_requests, execute_hybrid_search_query, _item_names_filter


class HybridVectorSearchNode(BaseNode):

    name = 'hybrid_vector_search_node'

    def process(self, state: QueryGraphState) -> Union[QueryGraphState,Dict[str,Any]]:

        # 1、参数校验
        rewritten_query, item_names = self._validate_state(state)

        # 2、获取嵌入模型客户端
        try:
            bge_m3_client = AIClients.get_bge_m3_client()
        except ConnectionError as e:
            self.logger.error(f"bge_m3_client Connection error: {e}")
            return state

        # 3、获取Milvus客户端
        try:
            milvus_client = StorageClients.get_milvus_client()
        except ConnectionError as e:
            self.logger.error(f"milvus_client Connection error: {e}")
            return state

        # 4、嵌入、检索
        try:
            # 4.1 嵌入查询问题
            embedding_query_vector = generate_bge_m3_hybrid_vectors(model=bge_m3_client, embedding_documents=[rewritten_query])
        except Exception as e:
            self.logger.error(f"用户问题{rewritten_query}嵌入失败 error: {e}")
            return state


            # 4.2 创建混合检索请求 expr: 对检索的返回做过滤
        try:
            expr, expr_params = _item_names_filter(item_names)
            hybrid_search_req = create_hybrid_search_requests(dense_vector=embedding_query_vector['dense'][0],
                                          sparse_vector=embedding_query_vector['sparse'][0],
                                          expr=expr,
                                          limit=5,
                                          expr_params=expr_params,
                                          )

            # 4.3 执行混合检索请求
            hybrid_search_res = execute_hybrid_search_query(milvus_client=milvus_client,
                                        collection_name=self.config.chunks_collection,
                                        search_requests=hybrid_search_req,
                                        ranker_weights=[0.5, 0.5],
                                        norm_score=True,
                                        limit=5,
                                        output_fields=["chunk_id","content","item_name","title"]
                                        )
            if not hybrid_search_res or not hybrid_search_res[0]:
                return state

            # 4.4 更新state
            return {"embedding_chunks": hybrid_search_res[0]}

        except Exception as e:
            self.logger.error(f"用户问题{rewritten_query}嵌入失败 error: {e}")
            return state

    def _validate_state(self, state: QueryGraphState) -> Tuple[str, List[str]]:

        # 1、用户的问题（LLM重写后的）
        rewritten_query = state.get('rewritten_query')

        # 2、获取商品列表
        item_names = state.get('item_names')

        if not rewritten_query or not isinstance(rewritten_query, str):
            raise StateFieldError(node_name=self.name, field_name='rewritten_query', expected_type=str)

        if not item_names or not isinstance(item_names, list):
            raise StateFieldError(node_name=self.name, field_name='item_names', expected_type=list)

        return rewritten_query, item_names



if __name__ == '__main__':

    import json
    import os

    vector_search  = HybridVectorSearchNode()

    init_state = {
        "rewritten_query": "万用表如何测量电阻",
        # item_name 过滤是精确匹配，需与 Milvus 中入库的商品名一致
        "item_names": ["RS PRO RS-12 数字万用表"]
    }

    result = vector_search.process(init_state)

    chunks = result.get('embedding_chunks') or []
    if not chunks:
        print("未检索到切片结果（检查 item_names 是否与库中一致）")
    else:
        for res in chunks:
            print(json.dumps(res, ensure_ascii=False, indent=2))

    os._exit(0)

