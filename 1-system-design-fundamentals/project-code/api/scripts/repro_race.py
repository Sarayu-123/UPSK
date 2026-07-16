import asyncio
import httpx

URL = "http://127.0.0.1:8000/testcode123"  # Replace with your actual short code

async def make_request(client, request_num):
    try:
        response = await client.get(URL)
        print(
            f"Request {request_num}: "
            f"Status={response.status_code}"
        )
    except Exception as e:
        print(
            f"Request {request_num}: "
            f"Error={e}"
        )

async def main():
    async with httpx.AsyncClient() as client:

        for batch in range(1, 5):
            print(f"\n=== Batch {batch} ===")

            tasks = [
                make_request(client, i)
                for i in range(1, 51)
            ]

            await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())