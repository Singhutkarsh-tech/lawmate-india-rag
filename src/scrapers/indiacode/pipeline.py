import time
from typing import List, Dict, Any, Optional

from .client import ScraperClient, logger
from .list_scraper import scrape_ministry_data
from .act_scraper import scrape_act_page
from .pdf_downloader import run_batch as run_download_batch
from .parse import run_parse_batch
from .constants import MINISTRIES, BASE_URL
from src.db.database import get_conn
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

def fetch_acts_without_assets(limit: int = 50) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT a.id,
                   a.handle_id,
                   a.ministry_slug,
                   a.ministry_name
            FROM acts a
            LEFT JOIN assets s ON s.act_id = a.id
            WHERE s.id IS NULL
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


def run_listings(client: Optional[ScraperClient] = None, rpp: int = 1000, max_pages: int = 1) -> List[Dict[str, Any]]:
    if client is None:
        client = ScraperClient()
    summaries = []
    for ministry_name in MINISTRIES:
        slug = ministry_name.lower().replace(" ", "-")
        value_param = ministry_name

        logger.info("Scraping listing for ministry=%s", ministry_name)

        summary = scrape_ministry_data(
            client=client,
            ministry_name=ministry_name,
            ministry_slug=slug,
            value_params=value_param,
            rpp=rpp,
            max_pages=max_pages,
        )

        summaries.append(summary)


def run_act_pages(client: Optional[ScraperClient] = None, batch_limit: int = 50, sleep_s: float = 0.1) -> int:
    if client is None:
        client = ScraperClient()
    acts = fetch_acts_without_assets(limit=batch_limit)
    if not acts:
        logger.info("No acts without assets found.")
        return 0
    logger.info("Found %d acts without assets", len(acts))
    for act in acts:
        handle_id = act["handle_id"]
        ministry_name = act["ministry_name"]
        ministry_slug = act["ministry_slug"]
        handle_url = f"{BASE_URL}/handle/123456789/{handle_id}?view_type=browse"
        logger.info("Scraping act page handle_id=%s url=%s", handle_id, handle_url)
        scrape_act_page(
            client=client,
            handle_url=handle_url,
            handle_id=handle_id,
            ministry_name=ministry_name,
            ministry_slug=ministry_slug,
        )
        if sleep_s:
            time.sleep(sleep_s)
    return len(acts)


def run_full_pipeline(
    listing_rpp: int = 1000,
    listing_max_pages: int = 1,
    acts_batch_limit: int = 50,
    download_batch_limit: int = 10,
    parse_batch_limit: int = 10,
) -> None:
    client = ScraperClient()

    logger.info("Starting listings for all ministries")
    run_listings(client=client, rpp=listing_rpp, max_pages=listing_max_pages)

    logger.info("Starting act-page scraping")
    while True:
        count = run_act_pages(client=client, batch_limit=acts_batch_limit)
        if count == 0:
            break

    logger.info("Starting PDF download batches")
    while True:
        count = run_download_batch(limit=download_batch_limit)
        if count == 0:
            break

    logger.info("Starting parse batches")
    while True:
        count = run_parse_batch(limit=parse_batch_limit)
        if count == 0:
            break

    logger.info("Full pipeline finished.")

if __name__ == "__main__":

    run_full_pipeline(
        listing_rpp=1000,
        listing_max_pages=5,     
        acts_batch_limit=50,
        download_batch_limit=10,
        parse_batch_limit=10,
    )