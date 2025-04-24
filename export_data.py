import asyncio
from db.crawler_db_actions import export_scraped_content_to_csv


async def main():
    await export_scraped_content_to_csv("exports/scraped_content.csv")


if __name__ == "__main__":
    asyncio.run(main())
