import time
import json
from urllib.parse import urljoin, urlparse, quote_plus
from typing import Dict, List, Any, Optional

from .constants import BASE_URL, MINISTRY_BROWSE_PATH, MINISTRIES, SELECTORS, DEFAULT_MINISTRY_PARAMS
from src.db.acts_dao import insert_or_update_act
from .client import ScraperClient

client = ScraperClient()

def _build_ministry_url(value_param:str, rpp: int, offset: int) -> str:
    return(f"{MINISTRY_BROWSE_PATH}"
           f"?type=ministry&order=ASC&rpp={int(rpp)}&value={quote_plus(value_param)}&offset={int(offset)}"
           )

def _extract_handle_id(href: Optional[str]) -> Optional[str]:
    if not href:
        return None
    try:
        path = urlparse(href).path
        marker = "/handle/123456789/"
        if marker in path:
            tail = path.split(marker, 1)[1]
            return tail.split("/", 1)[0] 
        return None
    except Exception:
        return None

def scrape_ministry_data(client, ministry_name, ministry_slug, value_params, rpp =10000, max_pages = 1, sleep_s=0.2):

    total_rows = 0
    upserts = 0
    pages = 0
    offset = 0

    while pages < max_pages:
        path = _build_ministry_url(value_param=value_params, rpp=rpp, offset=offset)
        status, html, final_url = client.get(path)
        if status != 200 or not html:
            print(f"[{ministry_name}] Non-200 or empty HTML at offset {offset} --> Stopping")
            break

        soup = client.soup(html)

        table_sel = SELECTORS.get("listing_table", "table.panel.table.table-bordered.table-hover")
        table = soup.select_one(table_sel)

        if not table:
            print(f"[{ministry_name}] Listing table not found with selector '{table_sel}' → stopping.")
            break

        rows = table.select("tr")
        if not rows or len(rows) <= 1:
            print(f"[{ministry_name}] No data rows found → stopping.")
            break    

        # Let's Skip header from the first row 
        data_rows = rows[1:]
        page_rows = 0

        for tr in data_rows:
            tds = tr.find_all("td")
            if len(tds) < 4:
                continue

            enactment_date_raw  = tds[0].get_text(strip = True)
            act_number = tds[1].get_text(strip = True)
            act_title = tds[2].get_text(strip = True)
            link = tds[3].find("a")

            view_href = link.get("href") if link else None
            view_url = urljoin(BASE_URL, view_href) if view_href else None
            handle_id = _extract_handle_id(view_href)

            if not handle_id:
                continue

            raw_row = {
                "enactment_date_raw": enactment_date_raw,
                "act_number": act_number,
                "act_title": act_title,
                "view_href": view_href,
                "view_url": view_url,
            }

            act = {
                "source_portal": "indiacode.nic.in",
                "handle_id": handle_id,
                "ministry_slug": ministry_slug,
                "ministry_name": ministry_name,
                "act_title": act_title,
                "act_number": act_number,
                "enactment_date_raw": enactment_date_raw,
                "raw_row_json": raw_row,
            }

            insert_or_update_act(act)
            upserts += 1
            total_rows += 1
            page_rows += 1

        pages += 1

        if page_rows == 0:
            break

        if sleep_s:
            time.sleep(sleep_s)

    return{
        'ministry':ministry_name,
        'slug':ministry_slug,
        'rows_found': total_rows,
        'inserted_or_updated': upserts,
        "pages":pages
    }

if __name__ == "__main__":
    print("Running list_scraper main...")

    from src.scrapers.indiacode.client import ScraperClient

    client = ScraperClient()

    summary = scrape_ministry_data(
        client=client,
        ministry_name="Road Transport and Highways",
        ministry_slug="road-transport-highways",
        value_params="Road Transport and Highways",
        rpp=1000,
        max_pages=1,
    )

    print("SUMMARY:")
    print(summary)