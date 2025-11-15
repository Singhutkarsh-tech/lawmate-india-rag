from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
RAW_HTML_DIR = DATA_DIR / "raw_html"
PDF_DIR = DATA_DIR / "pdf"
META_DIR = DATA_DIR / "meta"
LOGS_DIR = REPO_ROOT / "logs"

DEFAULT_DIRS = [DATA_DIR, RAW_HTML_DIR, PDF_DIR, META_DIR, LOGS_DIR]

ACTS_META_CSV = META_DIR / "acts_metadata.csv"         
SCRAPE_AUDIT_CSV = META_DIR / "scrape_audit_log.csv"

# BASE URLS:

BASE_URL = "https://www.indiacode.nic.in"
MINISTRY_BROWSE_PATH = "/handle/123456789/1362/browse"


DEFAULT_MINISTRY_PARAMS = {
    "type":'ministry',
    "order":"ASC",
    "rpp": 1000
}

MINISTRIES = {
    "Road Transport and Highways",
    "Electronics and Information Technology",
    "Personnel, Public Grievances and Pensions",
    "Social Justice and Empowerment",
    "Housing and Urban Affairs",
    "Consumer Affairs, Food and Public Distribution",
}

SELECTORS = {
  "rows": "table.table.table-bordered.table-hover > tbody > tr:not(:first-child)",
  "date": "td:nth-child(1)",
  "act_number": "td:nth-child(2)",
  "short_title": "td:nth-child(3)",
  "view_link": "td:nth-child(4) a",
  "result_banner": ".panel-heading1, .panel-footer",
  "pdf_link_generic": 'a[href$=".pdf"], a[href*=".pdf?"]',
  "base_url": "https://www.indiacode.nic.in",
}

DATE_FORMATS = [
    "%d-%b-%Y",  # e.g. 01-Mar-1950
    "%d-%B-%Y",  # e.g. 01-March-1950
]


DEFAULT_TIMEOUT = (5, 25)  # (connect, read) seconds
TIMEOUT_S = 20
MAX_RETRIES = 5
BACKOFF_FACTOR = 0.6
REQUEST_DELAY_S = 0.8
STATUS_FORCELIST = {429, 500, 502, 503, 504}
REQUESTS_PER_MINUTE = 20        # crude client-side rate limiter
CONCURRENT_DOWNLOADS = 4        # for PDFs (tune per bandwidth)

USER_AGENTS = [
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
]

DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache"
}

PDF_MAX_SIZE_MB = 40  
PDF_ALLOWED_MIME = {"application/pdf"}  #content-type gate


LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
LOG_FILE = LOGS_DIR / "scraper.log"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200

MILVUS = {
    "host": "localhost",
    "port": "19530",
    "db_name": "lawmate_db",
    "collection": "acts_chunks",
    "dim": 384,
    "metric_type": "L2",  
    "index": {
        "index_type": "IVF_FLAT",
        "params": {"nlist": 1024},
    },
    "search_params": {"params": {"nprobe": 20}},
}


RESPECT_ROBOTS = True  
PAUSE_JITTER = (0.2, 0.8) 

ENCODING = "utf-8"
CSV_DIALECT = "excel"