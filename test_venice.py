"""Quick Venice API connectivity test."""
import asyncio
import os
from dotenv import load_dotenv
import httpx

load_dotenv()

async def test():
    key = os.getenv("VENICE_API_KEY")
    print(f"Key loaded: {key[:30]}...")
    async with httpx.AsyncClient() as c:
        r = await c.post(
            "https://api.venice.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": "llama-3.3-70b", "messages": [{"role": "user", "content": "Say ALIVE"}], "max_tokens": 10},
            timeout=15,
        )
        print("Status:", r.status_code)
        print("Body:", r.text[:300])

asyncio.run(test())
