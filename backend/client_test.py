"""End-to-end check using a real MCP client against the clean /mcp URL."""
import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def main():
    async with streamablehttp_client("http://localhost:8077/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("TOOLS:", [t.name for t in tools.tools])
            result = await session.call_tool(
                "sample-pet-store__getPetById", {"petId": 1}
            )
            print("CALL RESULT (first 200 chars):")
            print(result.content[0].text[:200])


asyncio.run(main())
