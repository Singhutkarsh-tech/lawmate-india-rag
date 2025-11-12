CREATE TABLE acts (
  id                CHAR(32) PRIMARY KEY,
  source_portal     TEXT NOT NULL,
  handle_id         TEXT NOT NULL,
  ministry_slug     TEXT NOT NULL,
  ministry_name     TEXT NOT NULL,
  act_title         TEXT NOT NULL,
  act_number        TEXT,
  enactment_date_raw TEXT,
  raw_row_json      TEXT,
  inserted_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (source_portal, handle_id)
);


CREATE TABLE assets (
  id                CHAR(32) PRIMARY KEY,
  act_id            CHAR(32) NOT NULL REFERENCES acts(id) ON DELETE CASCADE,
  version_label     TEXT,
  view_url          TEXT,
  pdf_url           TEXT,
  pdf_sha256        TEXT,
  pdf_bytes         INTEGER,
  fetched_at        TIMESTAMP,
  parse_status      TEXT DEFAULT 'PENDING',
  text_path         TEXT,
  notes             TEXT,
  inserted_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (act_id, pdf_url)
);