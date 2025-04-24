import asyncio
import httpx
import time

from crawl import WebCrawler
from utils.urls_utils import UrlFilterer


async def main():
    filterer = UrlFilterer(
        domains={"bhcoe.org", "www.bhcoe.org"},
        blacklist={".jpg", ".css", ".js", ".svg", ".jpeg", ".pdf"},
    )

    start = time.perf_counter()
    async with httpx.AsyncClient() as client:
        crawler = WebCrawler(
            client=client,
            urls_list=[
                "https://www.bhcoe.org/aba-therapy-directory/",
            ],
            filter_url=filterer.filter_url,
            workers=5,
            max_depth=100,
        )
        await crawler.run()
    end = time.perf_counter()

    seen = sorted(crawler.urls_seen)
    print(f"Done: {len(crawler.urls_done)} URLs")
    print(f"Found: {len(seen)} URLs")
    print(f"Done in {end - start:.2f}s")


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
