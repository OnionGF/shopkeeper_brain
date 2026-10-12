import asyncio
import os

from dotenv import load_dotenv
from agents.mcp import MCPServerStreamableHttp

load_dotenv()


async def test_mcp_connect():
    base_url = os.getenv("MCP_DASHSCOPE_BASE_URL")
    api_key = os.getenv("OPENAI_API_KEY")

    if not base_url or not api_key:
        print("连接失败：请先在 .env 中配置 MCP_DASHSCOPE_BASE_URL 和 OPENAI_API_KEY")
        return

    try:
        async with MCPServerStreamableHttp(
                name="联网搜索",
                params={
                    "url": base_url,
                    "headers": {
                        "Authorization": f"Bearer {api_key}",
                    },
                    "timeout": 30,
                },
                cache_tools_list=True,
                max_retry_attempts=3,
        ) as client:
            tools = await client.list_tools()
            print("连接成功，可用工具：", [t.name for t in tools])
    except Exception as e:
        print(f"连接失败：{type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(test_mcp_connect())
