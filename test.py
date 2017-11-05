import asyncio, aiohttp

async def main():
    async with aiohttp.ClientSession(headers={"Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6IjY1NzQxNzA1LTEyYzItNDdhNy04OTFiLTA3NDQyZjg4Njk4MCIsImlhdCI6MTUwOTg3NzQzMywic3ViIjoiZGV2ZWxvcGVyLzA5M2IzOThiLTQzNmYtM2Q2ZC0xOTFmLTE0NTRjNWI2Mzg1NSIsInNjb3BlcyI6WyJjbGFzaCJdLCJsaW1pdHMiOlt7InRpZXIiOiJkZXZlbG9wZXIvc2lsdmVyIiwidHlwZSI6InRocm90dGxpbmcifSx7ImNpZHJzIjpbIjIyMS4xMjQuMTIzLjI1MiJdLCJ0eXBlIjoiY2xpZW50In1dfQ.2mXMSOVPUv0y8LjnVqmfKH6cTLrGUIr1B-ArHwCzRFr9bBTX1m5bRrQv8-ezXR4n_AM8vF9dBiUW8PtjVKb60w"}) as session:
        async with session.get("https://api.clashofclans.com/v1/clans/%23Y8CL2GL/members") as resp:
            data = await resp.json()
            print(data)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()