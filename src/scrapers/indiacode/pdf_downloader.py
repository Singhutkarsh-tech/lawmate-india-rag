import os
import time
import hashlib
import random
from typing import Dict, List, Any

import requests

from src.db.database import get_conn
from src.scrapers.indiacode.client import logger
from src.scrapers.indiacode.constants import BASE_URL, USER_AGENTS

OUTPUT_DIR = "data/raw/pdf"
BATCH_SIZE = 10
DOWNLOAD_SLEEP_S = 0.2


def _compute_sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def fetch_pending_assets(limit: int = BATCH_SIZE) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
              a.id,
              a.act_id,
              a.pdf_url,
              a.view_url,
              COALESCE(a.version_label, '') AS version_label,
              acts.ministry_slug,
              acts.ministry_name
            FROM assets a
            JOIN acts ON a.act_id = acts.id
            WHERE a.pdf_url IS NOT NULL
              AND (a.pdf_sha256 IS NULL OR a.pdf_sha256 = '')
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


def update_asset_download(
    asset_id: str,
    sha256: str,
    size_bytes: int,
    status: str,
    notes: str = "",
) -> None:
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE assets
            SET pdf_sha256 = ?,
                pdf_bytes = ?,
                parse_status = ?,
                notes = COALESCE(notes, '') || ?
                    || CASE WHEN ? = '' THEN '' ELSE '\n' END,
                fetched_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                sha256,
                size_bytes,
                status,
                (("\n" if notes else "") + notes) if notes else "",
                notes or "",
                asset_id,
            ),
        )
        conn.commit()


def _ensure_output_dir(ministry_slug: str) -> str:
    path = os.path.join(OUTPUT_DIR, ministry_slug)
    os.makedirs(path, exist_ok=True)
    return path


def _find_asset_by_sha256(sha256: str) -> Dict[str, Any] | None:
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, pdf_sha256
            FROM assets
            WHERE pdf_sha256 = ?
            LIMIT 1
            """,
            (sha256,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def _download_single(asset: Dict[str, Any]) -> None:
    pdf_url = asset["pdf_url"] or ""
    if not pdf_url:
        logger.warning("Asset %s has empty pdf_url", asset["id"])
        update_asset_download(asset["id"], "", 0, "FAILED", "Empty pdf_url")
        return

    if not pdf_url.lower().startswith("http"):
        if BASE_URL.endswith("/") and pdf_url.startswith("/"):
            pdf_url = BASE_URL[:-1] + pdf_url
        else:
            pdf_url = BASE_URL + pdf_url

    headers = {"User-Agent": random.choice(USER_AGENTS)}
    try:
        resp = requests.get(pdf_url, headers=headers, timeout=30)
    except requests.RequestException as e:
        logger.error("Download error for %s: %s", pdf_url, e)
        update_asset_download(asset["id"], "", 0, "FAILED", f"RequestException: {e}")
        return

    if resp.status_code != 200:
        logger.error("Non-200 for %s: %s", pdf_url, resp.status_code)
        update_asset_download(
            asset["id"],
            "",
            0,
            "FAILED",
            f"HTTP {resp.status_code} for {pdf_url}",
        )
        return

    data = resp.content or b""
    size = len(data)
    if size == 0:
        update_asset_download(asset["id"], "", 0, "FAILED", "Empty response body")
        return

    sha256 = _compute_sha256_bytes(data)
    existing = _find_asset_by_sha256(sha256)
    if existing:
        note = f"duplicate_of={existing['id']}"
        update_asset_download(asset["id"], sha256, size, "DUPLICATE", note)
        logger.info(
            "Duplicate PDF for asset %s (sha=%s) matches %s",
            asset["id"],
            sha256,
            existing["id"],
        )
        return

    ministry_slug = asset.get("ministry_slug") or "unknown"
    out_dir = _ensure_output_dir(ministry_slug)
    filename_part = (asset.get("pdf_url") or "").split("/")[-1] or "doc.pdf"
    safe_name = f"{asset['id']}_{filename_part}"
    out_path = os.path.join(out_dir, safe_name)

    try:
        with open(out_path, "wb") as f:
            f.write(data)
    except OSError as e:
        logger.error("File write error for %s: %s", out_path, e)
        update_asset_download(asset["id"], "", 0, "FAILED", f"File error: {e}")
        return

    note = f"path={out_path}"
    update_asset_download(asset["id"], sha256, size, "DOWNLOADED", note)
    logger.info(
        "Downloaded %s bytes for asset %s → %s",
        size,
        asset["id"],
        out_path,
    )


def run_batch(limit: int = BATCH_SIZE) -> int:
    assets = fetch_pending_assets(limit=limit)
    if not assets:
        logger.info("No pending assets to download.")
        return 0

    logger.info("Found %d pending assets to download", len(assets))
    for asset in assets:
        _download_single(asset)
        if DOWNLOAD_SLEEP_S:
            time.sleep(DOWNLOAD_SLEEP_S)
    return len(assets)


if __name__ == "__main__":
    count = run_batch(limit=BATCH_SIZE)
    print(f"Downloaded batch, assets handled: {count}")