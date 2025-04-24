import aiosqlite
import json


async def store_data_responses(
    url: str, status_code: int, content_size: int, page_title: str
):
    async with aiosqlite.connect("db/crawler_data.db") as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS data_responses(
            url TEXT PRIMARY KEY,
            status_code INTEGER,
            content_size INTEGER,
            page_title TEXT
            )
        """
        )
        await db.execute(
            """
            INSERT OR REPLACE INTO data_responses (url, status_code, content_size, page_title)
            VALUES (?, ?, ?, ?)
        """,
            (url, status_code, content_size, page_title),
        )
        await db.commit()
        await db.close()


async def store_statistics(
    total_number_urls_crawled: int,
    total_number_errors_crawling: int,
    total_number_urls_crawled_per_domain: dict[str, int],
    total_number_urls_per_status_code: dict[str, int],
):
    async with aiosqlite.connect("db/crawler_data.db") as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS statistics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total_number_urls_crawled INTEGER,
            total_number_errors_crawling INTEGER,
            total_number_urls_crawled_per_domain TEXT,
            total_number_urls_per_status_code TEXT
            )
        """
        )
        total_number_urls_crawled_per_domain_json = json.dumps(
            total_number_urls_crawled_per_domain
        )
        total_number_urls_per_status_code_json = json.dumps(
            total_number_urls_per_status_code
        )
        await db.execute(
            """
            INSERT OR REPLACE INTO statistics (total_number_urls_crawled, total_number_errors_crawling, total_number_urls_crawled_per_domain, total_number_urls_per_status_code)
            VALUES (?, ?, ?, ?)
        """,
            (
                total_number_urls_crawled,
                total_number_errors_crawling,
                total_number_urls_crawled_per_domain_json,
                total_number_urls_per_status_code_json,
            ),
        )
        await db.commit()
        await db.close()


async def store_scraped_content(scraped_content):
    async with aiosqlite.connect("db/crawler_data.db") as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS scraped_content (
                url TEXT PRIMARY KEY,
                title TEXT,
                meta_description TEXT,
                h1_text TEXT,
                text_content TEXT,
                images TEXT,
                links TEXT,
                address TEXT,
                structured_data TEXT
            )
        """
        )

        images_json = (
            json.dumps(scraped_content.images) if scraped_content.images else None
        )
        links_json = (
            json.dumps(scraped_content.links) if scraped_content.links else None
        )
        address_json = (
            json.dumps(scraped_content.address) if scraped_content.address else None
        )
        structured_data_json = (
            json.dumps(scraped_content.structured_data)
            if scraped_content.structured_data
            else None
        )

        await db.execute(
            """
            INSERT OR REPLACE INTO scraped_content 
            (url, title, meta_description, h1_text, text_content, images, links, address, structured_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                scraped_content.url,
                scraped_content.title,
                scraped_content.meta_description,
                scraped_content.h1_text,
                scraped_content.text_content,
                images_json,
                links_json,
                address_json,
                structured_data_json,
            ),
        )

        await db.commit()
