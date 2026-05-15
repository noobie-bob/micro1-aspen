import asyncio
from fastmcp import FastMCP, Client

mcp = FastMCP("test")
@mcp.tool()
def raise_err(token: str) -> str:
    raise Exception("Unauthorized")

async def main():
    async with Client(mcp) as client:
        res = await client.call_tool("raise_err", {"token": "bad"})
        print(f"isError: {res.isError}")
        print(f"content: {res.content[0].text}")

if __name__ == "__main__":
    asyncio.run(main())
