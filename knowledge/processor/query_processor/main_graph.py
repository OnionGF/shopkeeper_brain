"""查询流程主图

使用 LangGraph 构建知识库查询工作流（DAG 轨：纯知识库，不含联网）。
联网检索仅由 Agent 轨通过 MCP tool 调用。
"""

from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from dotenv import load_dotenv
from knowledge.processor.query_processor.state import QueryGraphState
from knowledge.processor.query_processor.nodes.item_name_confirmed_node import ItemNameConfirmedNode
from knowledge.processor.query_processor.nodes.hybrid_vector_search_node import HybridVectorSearchNode
from knowledge.processor.query_processor.nodes.hyde_vector_search_node import HydeVectorSearchNode
from knowledge.processor.query_processor.nodes.rrf_merge_node import RrfMergeNode
from knowledge.processor.query_processor.nodes.rerank_node import RerankerNode
from knowledge.processor.query_processor.nodes.answer_output_node import AnswerOutputNode

# 加载环境变量
load_dotenv()


def route_after_item_confirm(state: QueryGraphState) -> str:
    """商品名称确认后的路由。

    Returns:
        clarify: 已有澄清文案，直接输出
        product: 进入知识库双路检索
    """
    if state.get("answer"):
        return "clarify"
    return "product"


def create_query_graph() -> CompiledStateGraph:
    """创建查询流程图。

    Returns:
        编译后的 StateGraph 实例。

    流程结构::

        item_name_confirm
              │
              ├── clarify ──────────────────────────> answer_output
              │                                            │
              └── product                                  │
                   │                                       │
                   v                                       │
              multi_search                                 │
                   │                                       │
             ┌─────┴─────┐                                 │
             │           │                                 │
             v           v                                 │
        embedding      hyde                                │
             │           │                                 │
             └─────┬─────┘                                 │
                   │                                       │
                   v                                       │
                 join                                      │
                   │                                       │
                   v                                       │
                  rrf                                      │
                   │                                       │
                   v                                       │
                rerank                                     │
                   │                                       │
                   v                                       │
             answer_output <───────────────────────────────┘
                   │
                   v
                  END
    """

    # 1. 定义LangGraph工作流
    workflow = StateGraph(QueryGraphState)  # type:ignore

    # 2. 实例化节点（DAG 不含 web_mcp，联网留给 Agent）
    nodes = {
        "item_name_confirmed_node": ItemNameConfirmedNode(),
        "multi_search": lambda x: x,  # 虚拟节点
        "hybrid_vector_search_node": HybridVectorSearchNode(),
        "hyde_vector_search_node": HydeVectorSearchNode(),
        "join": lambda x: {},  # 多路搜索汇合（虚节点）
        "rrf_merge_node": RrfMergeNode(),
        "reranker_node": RerankerNode(),
        "answer_output_node": AnswerOutputNode(),
    }

    # 3. 添加节点
    for name, node in nodes.items():
        workflow.add_node(name, node)  # type:ignore

    # 4. 设置入口点
    workflow.set_entry_point("item_name_confirmed_node")

    # 5. 商品确认后：澄清 or 知识库
    workflow.add_conditional_edges(
        "item_name_confirmed_node",
        route_after_item_confirm,
        {
            "clarify": "answer_output_node",
            "product": "multi_search",
        },
    )

    # 6. 知识库双路并行
    workflow.add_edge("multi_search", "hybrid_vector_search_node")
    workflow.add_edge("multi_search", "hyde_vector_search_node")

    # 7. 汇合
    workflow.add_edge("hybrid_vector_search_node", "join")
    workflow.add_edge("hyde_vector_search_node", "join")

    # 8. 顺序边
    workflow.add_edge("join", "rrf_merge_node")
    workflow.add_edge("rrf_merge_node", "reranker_node")
    workflow.add_edge("reranker_node", "answer_output_node")
    workflow.add_edge("answer_output_node", END)

    # 9. 返回可运行的状态
    return workflow.compile()


# 创建全局图实例
query_app = create_query_graph()

if __name__ == "__main__":
    print("=" * 60)
    print("开始测试: 查询流程主图 (main_graph)")
    print("=" * 60)

    # ---- 测试场景 1：商品名明确，走完整 pipeline ----
    print("\n【场景 1】: 商品名明确，走完整 pipeline")
    print("-" * 60)

    mock_state_1 = {
        "original_query": "RS PRO RS-12 数字万用表如何测量直流电压？",
        "session_id": "test_session_main_graph",
        "task_id": "test_task_001",
        "is_stream": False,
    }

    result_1 = query_app.invoke(mock_state_1)

    print(f"\n  【结果】:")
    print(f"  商品名: {result_1.get('item_names')}")
    print(f"  重写查询: {result_1.get('rewritten_query')}")
    answer_1 = result_1.get("answer", "")
    print(f"  答案: {answer_1[:200]}..." if len(answer_1) > 200 else f"  答案: {answer_1}")
