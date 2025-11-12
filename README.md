Repo Structure:

lawmate-india-rag/
├─ README.md
├─ LICENSE
├─ .gitignore
├─ .env.example
├─ Makefile
├─ docker-compose.yml
├─ pyproject.toml                 
├─ configs/
│  ├─ scraping.yaml                # portals, routes, throttle, retries
│  ├─ preprocess.yaml              # cleaning rules, section regex
│  ├─ chunking.yaml                # legal-aware chunk sizes, overlap
│  ├─ embed.yaml                   # embedding model, dim, batch size
│  ├─ vectordb.yaml                # Milvus/Qdrant host, index params
│  ├─ routing.yaml                 # jurisdiction/state routing priority
│  └─ eval.yaml                    # eval questions, metrics, acceptance gates
├─ data/
│  ├─ raw/                         # raw PDFs/HTML (by jurisdiction/state)
│  ├─ staging/                     # cleaned text JSONL per doc
│  ├─ chunks/                      # chunked JSONL with metadata
│  ├─ embeddings/                  # NPZ/Parquet
│  └─ cache/                       # HTTP/download cache
├─ schemas/
│  ├─ doc_schema.json              # canonical doc record
│  ├─ chunk_schema.json            # chunk record (RAG unit)
│  └─ citation_schema.json         # citation payload used by API/UI
├─ src/
│  ├─ scrapers/
│  │  ├─ base_scraper.py
│  │  ├─ india_code_central.py     # central acts
│  │  ├─ india_state_portal.py     # generic state adapter
│  │  └─ states/
│  │     ├─ maharashtra.py
│  │     ├─ karnataka.py
│  │     └─ delhi.py
│  ├─ pipelines/
│  │  ├─ preprocess.py             # PDF → text, normalize whitespace, headers
│  │  ├─ legal_sectionizer.py      # split by Part/Chapter/Section/Schedule
│  │  ├─ chunker.py                # legal-aware chunks + overlap
│  │  ├─ embedder.py               # sentence-transformers/bge-m3
│  │  ├─ indexer.py                # upsert to Milvus/Qdrant + metadata
│  │  └─ versioning.py             # checksum, dedupe, amendments
│  ├─ retrieval/
│  │  ├─ router.py                 # jurisdiction/state intent detection
│  │  ├─ hybrid_retriever.py       # semantic + BM25/fuzzy
│  │  ├─ rewriter.py               # optional query rewrite
│  │  └─ ranker.py                 # rerank (e.g., bge-reranker)
│  ├─ llm/
│  │  ├─ prompt_templates/
│  │  │  ├─ answer_with_citations.txt
│  │  │  └─ refusal_guardrails.txt
│  │  └─ answerer.py               # glue: context → answer + citations
│  ├─ api/
│  │  ├─ main.py                   # FastAPI: /ask, /health, /docs
│  │  └─ models.py                 # pydantic I/O contracts
│  └─ utils/
│     ├─ io.py                     # read/write JSONL, Parquet
│     ├─ text_cleaning.py
│     ├─ logging.py
│     └─ rate_limit.py
├─ notebooks/
│  ├─ 00_explore_india_code.ipynb
│  ├─ 10_scraping_smoketest.ipynb
│  ├─ 20_chunking_vis.ipynb
│  └─ 30_eval_rag.ipynb
├─ tests/
│  ├─ test_scrapers.py
│  ├─ test_sectionizer.py
│  ├─ test_router.py
│  └─ test_api.py
└─ deployment/
   ├─ k8s/
   │  ├─ api-deployment.yaml
   │  ├─ api-service.yaml
   │  └─ vectordb-statefulset.yaml
   └─ terraform/                   # (later) for managed vector DB/storage



   lawmate/
├─ scrapers/
│  ├─ indiacode/
│  │  ├─ __init__.py
│  │  ├─ constants.py          # base URLs, request headers, paths, CSS/XPath selectors
│  │  ├─ client.py             # HTTP client, retries, backoff, rate-limit, robots check
│  │  ├─ list_scraper.py       # paginated ministry listing → rows (date, act no, title, view URL)
│  │  ├─ act_scraper.py        # “View…” page → act metadata + PDF url(s)
│  │  ├─ pdf_downloader.py     # download pdfs, checksum, dedupe, resume
│  │  ├─ parse.py              # tiny helpers: date normalization, text cleanup, safe filenames
│  │  ├─ storage.py            # write NDJSON/CSV/Parquet; directory strategy; checkpoints
│  │  ├─ pipeline.py           # orchestrates: discover → parse → enrich → download → persist
│  │  ├─ cli.py                # click/argparse entrypoints for: one-ministry / multi-ministry / resume
│  ├─ tests/
│  │  ├─ test_list_scraper.py
│  │  ├─ test_act_scraper.py
│  │  ├─ test_storage.py
│  │  └─ fixtures/ (saved HTML samples for stable tests)
├─ data/
│  ├─ raw/
│  │  ├─ metadata/             # per-ministry NDJSON (one JSON per act)
│  │  └─ pdf/                  # pdf/Ministry_Slug/ACT_NO_YYYY_titlehash.pdf
│  └─ processed/
│     ├─ acts_all.ndjson
│     └─ acts_all.csv
├─ config/
│  ├─ scraper.yml              # ministries to run, rpp, timeouts, max_pages
│  └─ ministries.yml           # curated list of “value=” strings to cover
├─ .env.example                # SCRAPER_USER_AGENT, SCRAPER_DELAY_MS, SCRAPER_MAX_RETRIES, …
├─ Makefile                    # friendly commands (see below)
└─ README.md