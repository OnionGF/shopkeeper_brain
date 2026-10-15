import asyncio
import concurrent.futures
import json
import os
from json import JSONDecodeError
from typing import Tuple, List, Dict, Any, Union, Coroutine, TypeVar

from agents.mcp import MCPServerStreamableHttp

from knowledge.processor.query_processor.base import BaseNode
from knowledge.processor.query_processor.exceptions import StateFieldError
from knowledge.processor.query_processor.state import QueryGraphState

T = TypeVar("T")


def _run_coro(coro: Coroutine[Any, Any, T]) -> T:
    """在同步节点中跑协程；Agent 轨已有事件循环时不能再用 asyncio.run。"""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


class WebMcpSearchNode(BaseNode):

    name = "web_mcp_search_node"

    def process(self, state: QueryGraphState) -> Union[QueryGraphState, Dict[str, Any]]:
        # 1、 参数校验
        rewritten_query, item_names = self._validate_state(state)

        # 2、定义并且执行 mcp 的调用
        try:
            web_search_results = _run_coro(self._execute_mcp_server(rewritten_query))
        except Exception as e:
            self.logger.error("MCP 联网搜索失败: %s", e, exc_info=True)
            return state

        # 3、判断
        if not web_search_results:
            self.logger.warning("MCP 联网搜索无结果 query=%s", rewritten_query)
            return state

        # 4. 返回
        return {"web_search_docs": web_search_results}

    def _validate_state(self, state: QueryGraphState) -> Tuple[str, List[str]]:

        # 1. 用户的问题（LLM重写后的；闲聊可回退到原问）
        rewritten_query = state.get('rewritten_query') or state.get('original_query')

        # 2. 获取商品名列表（闲聊可为空）
        item_names = state.get('item_names') or []

        # 3. 校验：联网搜索只强制需要查询文本
        if not rewritten_query or not isinstance(rewritten_query, str):
            raise StateFieldError(node_name=self.name, field_name='rewritten_query', expected_type=str)

        if not isinstance(item_names, list):
            raise StateFieldError(node_name=self.name, field_name='item_names', expected_type=list)

        return rewritten_query, item_names

    async def _execute_mcp_server(self, rewritten_query: str) -> List[Dict[str, Any]]:
        """
        执行MCP服务
        注意：一个MCP服务下可能有多个工具（工具:就是函数）
        Args:
            rewritten_query:

        Returns:

        """

        # 运行时读环境变量，避免配置单例在 load_dotenv 之前被冻结为空
        mcp_url = (os.getenv("MCP_DASHSCOPE_BASE_URL") or self.config.mcp_dashscope_base_url or "").strip()
        api_key = (os.getenv("OPENAI_API_KEY") or self.config.openai_api_key or "").strip()
        if not mcp_url or not api_key:
            raise RuntimeError("MCP 未配置：需要 MCP_DASHSCOPE_BASE_URL 与 OPENAI_API_KEY")

        # 1. 定义MCP客户端(StreamableHttp方式)
        async with MCPServerStreamableHttp(
                name="联网搜索",  # MCP客户端名字，自定义
                params={  # 提供MCP服务的第三方平台的api_key和base_url
                    "url": mcp_url,
                    "headers": {"Authorization": f"Bearer {api_key}"},
                    "timeout": 60,  # 超时时间
                },
                cache_tools_list=True,  # 缓存MCP服务下的工具列表的,加速
                max_retry_attempts=3,  # 重试次数
        ) as mcp_client:
            # 2. 调用工具
            web_search_result = await mcp_client.call_tool(tool_name="bailian_web_search",
                                                           arguments={"query": rewritten_query, "count": 3})
            # 3. 解析数据
            # 3.1 获取文本内容块对象
            if not web_search_result.content:
                return []

            text_content = web_search_result.content[0]
            if not text_content:
                return []

            # 3.2 获取文本内容块对象的内容
            text_content_text = text_content.text
            if not text_content_text:
                return []

            # 3.3 反序列化
            try:
                text_content_obj: Dict[str, Any] = json.loads(text_content_text)
                return self._parse_mcp_payload(text_content_obj)
            except JSONDecodeError as e:
                self.logger.error(f"web_search检索失败 失败信息：{e.msg} 失败的内容:{e.doc} 失败的位置：{e.pos}")
                return []

    def _parse_mcp_payload(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """解析 bailian_web_search 返回：pages + tools（天气等结构化结果）。"""
        web_search_results: List[Dict[str, Any]] = []

        # 结构化工具结果优先（如 weather）
        for tool in payload.get("tools") or []:
            if not isinstance(tool, dict):
                continue
            result_text = str(tool.get("result") or "").strip()
            if not result_text:
                continue
            tool_type = str(tool.get("type") or "tool").strip() or "tool"
            web_search_results.append({
                "snippet": result_text,
                "title": f"结构化结果 · {tool_type}",
                "url": "",
            })

        for page in payload.get("pages") or []:
            if not isinstance(page, dict):
                continue
            snippet = (page.get("snippet") or "").strip()
            if not snippet:
                continue
            web_search_results.append({
                "snippet": snippet,
                "title": (page.get("title") or "").strip(),
                "url": (page.get("url") or "").strip(),
            })

        return web_search_results


if __name__ == "__main__":

    web_search_node = WebMcpSearchNode()

    mock_state = {
        "rewritten_query": "今天天气咋样",
        "item_names": [],
        "original_query": "今天天气咋样",
    }

    result = web_search_node.process(mock_state)
    print(result)
