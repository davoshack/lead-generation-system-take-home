import asyncio
import httpx
import json
import pandas as pd
from bs4 import BeautifulSoup
from dataclasses import dataclass, field

from typing import Callable, Iterable, Dict, List, Optional, Any

from utils.urls_utils import UrlParser
from db.crawler_db_actions import (
    store_data_responses,
    store_statistics,
    store_scraped_content,
)


@dataclass
class ScrapedContent:
    url: str
    title: Optional[str] = None
    meta_description: Optional[str] = None
    h1_text: Optional[str] = None
    text_content: Optional[str] = None
    images: List[str] = None
    links: List[str] = None
    address: Optional[Dict[str, Any]] = None
    structured_data: List[Dict[str, Any]] = field(default_factory=list)


class WebCrawler:
    def __init__(
        self,
        client: httpx.AsyncClient,
        urls_list: Iterable[str],
        filter_url: Callable[[str, str], str | None],
        workers: int = 3,
        max_depth: int = 25,
    ):
        self.client = client

        self.start_urls = set(urls_list)
        self.work_todo = asyncio.Queue()
        self.urls_seen = set()
        self.urls_done = set()

        self.filter_url = filter_url
        self.num_workers = workers
        self.limit = max_depth
        self.total = 0
        self.total_number_errors = 0
        self.total_number_urls_crawled_per_domain = {}
        self.total_number_urls_per_status_code = {}

    async def run(self):
        await self.on_found_links(self.start_urls)
        workers = [asyncio.create_task(self.worker()) for _ in range(self.num_workers)]
        await self.work_todo.join()

        for worker in workers:
            worker.cancel()

        await store_statistics(
            len(self.urls_done),
            self.total_number_errors,
            self.total_number_urls_crawled_per_domain,
            self.total_number_urls_per_status_code,
        )

    async def worker(self):
        while True:
            try:
                await self.process_one()
            except asyncio.CancelledError:
                return

    async def process_one(self):
        url = await self.work_todo.get()
        try:
            await self.crawl(url)
        except Exception as exc:
            self.total_number_errors += 1
            print(f"Error: {exc} for {url}")
        finally:
            self.work_todo.task_done()

    async def crawl(self, url: str):
        await asyncio.sleep(0.1)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        }

        response = await self.client.get(url, follow_redirects=False, headers=headers)

        self.get_total_number_urls_per_status_code(response)

        self.parser = await self.parse_links(
            base=str(response.url),
            text=response.text,
        )

        await store_data_responses(
            url, response.status_code, len(response.content), self.parser.page_title
        )

        if response.status_code == httpx.codes.OK:
            scraped_data = await self.scrape_page_content(url, response.text)
            await store_scraped_content(scraped_data)

        await self.on_found_links(self.parser.found_links)

        self.urls_done.add(url)

    def get_total_number_urls_per_status_code(self, response):
        if response.status_code == httpx.codes.OK:
            self.total_number_urls_per_status_code["200"] = (
                self.total_number_urls_per_status_code.get("200", 0) + 1
            )
        if response.status_code == httpx.codes.NOT_FOUND:
            self.total_number_urls_per_status_code["404"] = (
                self.total_number_urls_per_status_code.get("404", 0) + 1
            )
        if response.status_code == httpx.codes.FORBIDDEN:
            self.total_number_urls_per_status_code["403"] = (
                self.total_number_urls_per_status_code.get("403", 0) + 1
            )
        if response.status_code == httpx.codes.INTERNAL_SERVER_ERROR:
            self.total_number_urls_per_status_code["500"] = (
                self.total_number_urls_per_status_code.get("500", 0) + 1
            )

    async def parse_links(self, base: str, text: str) -> set[str]:
        parser = UrlParser(
            base, self.filter_url, self.total_number_urls_crawled_per_domain
        )
        parser.feed(text)
        return parser

    async def on_found_links(self, urls: set[str]):
        new = urls - self.urls_seen
        self.urls_seen.update(new)
        for url in new:
            await self.put_todo(url)

    async def put_todo(self, url: str):
        if self.total >= self.limit:
            return
        self.total += 1
        await self.work_todo.put(url)

    async def scrape_page_content(self, url: str, html_content: str) -> ScrapedContent:
        soup = BeautifulSoup(html_content, "html.parser")

        scraped = ScrapedContent(url=url, images=[], links=[])

        if soup.title:
            scraped.title = soup.title.text.strip()

        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            scraped.meta_description = meta_desc.get("content").strip()

        h1_tag = soup.find("h1")
        if h1_tag:
            scraped.h1_text = h1_tag.text.strip()

        main_content = []
        for paragraph in soup.find_all("p"):
            text = paragraph.text.strip()
            if text and len(text) > 20:
                main_content.append(text)

        scraped.text_content = "\n\n".join(main_content) if main_content else None

        json_ld_scripts = soup.find_all("script", type="application/ld+json")
        structured_data = []

        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                structured_data.append(data)

                if isinstance(data, dict):
                    if "address" in data:
                        scraped.address = data["address"]

                    elif (
                        "@type" in data
                        and data["@type"]
                        in ["Organization", "LocalBusiness", "Store", "Restaurant"]
                        and "address" in data
                    ):
                        scraped.address = data["address"]

                    elif (
                        "location" in data
                        and isinstance(data["location"], dict)
                        and "address" in data["location"]
                    ):
                        scraped.address = data["location"]["address"]

                    elif "@graph" in data and isinstance(data["@graph"], list):
                        for item in data["@graph"]:
                            if isinstance(item, dict) and "address" in item:
                                scraped.address = item["address"]
                                break
            except (json.JSONDecodeError, TypeError):
                continue

        scraped.structured_data = structured_data

        for img in soup.find_all("img"):
            src = img.get("src")
            if src:
                if src.startswith("/"):
                    base_domain = "/".join(url.split("/")[:3])
                    src = f"{base_domain}{src}"
                scraped.images.append(src)

        for link in soup.find_all("a"):
            href = link.get("href")
            if href and not href.startswith("#") and not href.startswith("javascript:"):
                if href.startswith("/"):
                    base_domain = "/".join(url.split("/")[:3])
                    href = f"{base_domain}{href}"
                scraped.links.append(href)

        return scraped
