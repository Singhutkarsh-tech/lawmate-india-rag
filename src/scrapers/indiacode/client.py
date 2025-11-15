from __future__ import annotations
import time
import logging
import random
from typing import Dict, Optional, Tuple, Any
from urllib.parse import urljoin, urlparse
from http import HTTPStatus
from urllib import robotparser

import requests
from requests import Response
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup


from src.scrapers.indiacode.constants import BASE_URL, USER_AGENTS, MAX_RETRIES, BACKOFF_FACTOR, STATUS_FORCELIST, RESPECT_ROBOTS, REQUEST_DELAY_S, TIMEOUT_S

logger = logging.getLogger('src/scrapers/indiacode/client.py')
logger.setLevel(logging.INFO)

class ScraperClient():
    def __init__( self,
        base_url: str = BASE_URL,
        headers: Optional[Dict[str, str]] = None,
        timeout_s: int = TIMEOUT_S,
        max_retries: int = MAX_RETRIES,
        backoff_factor: float = BACKOFF_FACTOR,
        status_forcelist: Tuple[int, ...] = STATUS_FORCELIST,
        request_delay_s: float = REQUEST_DELAY_S,
        respect_robots: bool = RESPECT_ROBOTS,
        ) -> None:
        

        self.base_url = base_url.rstrip("/") + "/"
        self.timeout_s = timeout_s
        self.request_delay_s = request_delay_s
        self.respect_robots = respect_robots

        default_headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-IN,en;q=0.9",
            "Connection": "keep-alive",
        }

        if headers:
            default_headers.update(headers)

        self.session = requests.Session()
        self.session.headers.update(default_headers)

        retry = Retry(
            total = max_retries,
            backoff_factor = backoff_factor,
            status_forcelist = status_forcelist,
            allowed_methods = ("GET","HEAD"),    #We only retry on Valid idempotent methods Get and Head and not on put/post
            raise_on_status = False,
            raise_on_redirect = False,
            respect_retry_after_header=True
        )

        adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=50)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        self._robots = None
        if self.respect_robots:
            self._init_robots()


    def get(self, 
            url : str, 
            params : Optional[Dict[str,Any]] = None, 
            allow_redirects : bool = True,
            ) -> Tuple[int,str,str] : #returns (status_code, text, final_url)
        
        abs_url = self.abs_url(url)
        self._polite_wait()

        if self.respect_robots and not self._allowed_by_robots(abs_url):
            logger.warning("Blocked by robots.txt: %s", abs_url)
            return HTTPStatus.FORBIDDEN, "", abs_url
        

        try:
            resp : Response = self.session.get(
                abs_url,
                params =params,
                timeout=self.timeout_s,
                allow_redirects=allow_redirects
            )

        except requests.RequestException as e:
            logger.error(f"Request Error for {abs_url}: {e}")
            return(0, "", abs_url)
    
        content_type = resp.headers.get("Content-Type", "").lower()
        if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
            logger.debug("Non-HTML content-type for %s: %s", abs_url, content_type)

        text = resp.text or ""
        final_url = str(resp.url)

        if resp.status_code >= 400:
            logger.warning("HTTP %s for %s", resp.status_code, final_url)
        return resp.status_code, text, final_url

    def soup(self, html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "lxml")

    def abs_url(self, relative_or_abs: str) -> str:
        return urljoin(self.base_url, relative_or_abs)

    def _polite_wait(self) -> None:
        if self.request_delay_s and self.request_delay_s > 0:
            time.sleep(self.request_delay_s)
    
    def _init_robots(self) -> None:
        try:
            robots_url = urljoin(self.base_url, "/robots.txt")
            rp = robotparser.RobotFileParser(robots_url)
            rp.set_url(robots_url)

            self._polite_wait()
            resp = self.session.get(robots_url, timeout=min(10, self.timeout_s))

            if resp.status_code == 200:
                rp.parse(resp.text.splitlines())
                self._robots = rp
                logger.info("robots.txt loaded from %s", robots_url)
            else:
                logger.info("robots.txt not found or not 200 (%s). Proceeding.", resp.status_code)
                self._robots = None
        except requests.RequestException:
            logger.info("robots.txt fetch failed. Proceeding without robots.")
            self._robots = None

    def _allowed_by_robots(self, url: str) -> bool:
        if self._robots is None:
            return True
        path = urlparse(url).path or "/"
        return self._robots.can_fetch(random.choice(USER_AGENTS), path)

if __name__ == "__main__":
    c = ScraperClient()
    status, html, url = c.get(
        "/handle/123456789/1362/browse?type=ministry&order=ASC&rpp=1000&value=Road+Transport+and+Highways"
    )
    print(status, url)
    if status == 200:
        s = c.soup(html)
        print("Title:", (s.title.text if s.title else "N/A"))