import time
from urllib.parse import urljoin
from typing import Dict, List, Any

from .client import ScraperClient
from src.db.acts_dao import md5_hash
from src.db.assests_dao import insert_or_update_assests
from .constants import BASE_URL


def extract_long_title(soup):
    p = soup.select_one("p#short_title")
    if p:
        return p.get_text(strip=True)
    return None


def extract_pdf_links(soup, base_url: str = BASE_URL) -> List[str]:
    links = set()

    p = soup.select_one("p#short_title")
    if p:
        a = p.find_parent("a")
        if a:
            href = a.get("href", "")
            if href and href.lower().endswith(".pdf"):
                filename = href.split("/")[-1]
                links.add(urljoin(base_url, href))

    for a in soup.find_all("a"):
        href = a.get("href", "")
        if href and href.lower().endswith(".pdf"):
            filename = href.split("/")[-1]
            links.add(urljoin(base_url, href))

    return list(links)


def scrape_act_page(
    client: ScraperClient,
    handle_url: str,
    handle_id: str,
    ministry_name: str,
    ministry_slug: str,
    sleep_s: float = 0.1,
) -> Dict[str, Any]:
    status, html, final_url = client.get(handle_url)
    if status != 200 or not html:
        return {}

    soup = client.soup(html)

    long_title = extract_long_title(soup)
    pdf_urls = extract_pdf_links(soup)
    act_id = md5_hash(f"indiacode.nic.in_{handle_id}")

    for pdf_url in pdf_urls:
        insert_or_update_assests(
            {
                "act_id": act_id,
                "pdf_url": pdf_url,
                "view_url": final_url,
                "version_label": None
            }
        )

    if sleep_s:
        time.sleep(sleep_s)

    return {
        "handle_id": handle_id,
        "ministry_name": ministry_name,
        "ministry_slug": ministry_slug,
        "long_title": long_title,
        "pdf_count": len(pdf_urls),
    }


if __name__ == "__main__":
    print("Running act_scraper test…")
    client = ScraperClient()
    test_url = "https://www.indiacode.nic.in/handle/123456789/2028?view_type=browse"
    result = scrape_act_page(
        client=client,
        handle_url=test_url,
        handle_id="1798",
        ministry_name="Road Transport and Highways",
        ministry_slug="road-transport-highways",
    )
    print("Result:", result)