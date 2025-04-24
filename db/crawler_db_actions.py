import aiosqlite
import json
import csv
import os
from typing import List, Dict, Any


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
                address TEXT
            )
        """
        )

        address_json = (
            json.dumps(scraped_content.address) if scraped_content.address else None
        )

        await db.execute(
            """
            INSERT OR REPLACE INTO scraped_content 
            (url, title, meta_description, h1_text, address)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                scraped_content.url,
                scraped_content.title,
                scraped_content.meta_description,
                scraped_content.h1_text,
                address_json,
            ),
        )

        await db.commit()


async def export_scraped_content_to_csv(output_file: str = "scraped_content.csv"):
    async with aiosqlite.connect("db/crawler_data.db") as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(
            """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='scraped_content'
        """
        )
        if not await cursor.fetchone():
            print("No scraped content table found in the database")
            return

        cursor = await db.execute(
            "SELECT * FROM scraped_content WHERE address IS NOT NULL"
        )
        rows = await cursor.fetchall()

        if not rows:
            print("No scraped content found in the database")
            return

        os.makedirs(
            os.path.dirname(output_file) if os.path.dirname(output_file) else ".",
            exist_ok=True,
        )

        with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = rows[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in rows:
                row_dict = dict(row)

                for field in [
                    "address",
                ]:
                    if row_dict[field] and row_dict[field] != "null":
                        try:
                            parsed = json.loads(row_dict[field])
                            row_dict[field] = json.dumps(parsed, ensure_ascii=False)
                        except json.JSONDecodeError:
                            pass

                writer.writerow(row_dict)

        print(f"Successfully exported {len(rows)} records to {output_file}")
