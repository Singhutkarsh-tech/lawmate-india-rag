import os
import time
import fitz
import re
from typing import Optional, Dict, Any, List

from src.db.database import get_conn
from src.scrapers.indiacode.constants import BASE_URL
from src.scrapers.indiacode.client import logger

OUTPUT_DIR = 'data/parsed'
BATCH_SIZE = 10
PARSE_SLEEP_S = 0.2

def _clean_text(text:str)->str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def fetch_pending_parse(limit:int = BATCH_SIZE)-> List[Dict[str, Any]]:
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                a.id,
                a.act_id,
                a.pdf_url,
                a.pdf_sha256,
                a.parse_status,
                a.text_path,
                a.notes, 
                a.pdf_bytes,
                acts.ministry_slug,
                acts.ministry_name
            FROM assets a
            JOIN acts ON a.act_id = acts.id
            WHERE a.pdf_sha256 IS NOT NULL
              AND a.pdf_sha256 != ''
              AND (a.parse_status IS NULL OR a.parse_status = '' OR a.parse_status = 'PENDING' OR a.parse_status = 'DOWNLOADED')
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    
def update_parse(
        asset_id:str,
        text_path:str,
        status:str,
        notes:str
    ) -> None:
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE assets
            SET text_path = ?,
                parse_status = ?,
                notes = COALESCE(notes, '') || ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (text_path, status, ("\n" + notes) if notes else "", asset_id),
        )
        conn.commit()

def _ensure_output_dir(ministry_slug: str) -> str:
    out_dir = os.path.join(OUTPUT_DIR, ministry_slug)
    os.makedirs(out_dir, exist_ok=True)
    return out_dir

def _parse_single(asset: Dict[str, Any]) -> None:
    asset_id = asset["id"]
    ministry_slug = asset.get("ministry_slug") or ""
    pdf_path = None

    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT notes FROM assets WHERE id = ?", (asset_id,))
        row = cursor.fetchone()
        if row and row["notes"]:
            for part in row["notes"].split("\n"):
                part = part.strip()
                if part.startswith("path="):
                    pdf_path = part.replace("path=", "").strip()

    if not pdf_path or not os.path.exists(pdf_path):
        update_parse(asset_id, "", "FAILED", "PDF missing on disk")
        return

    out_dir = _ensure_output_dir(ministry_slug)
    out_path = os.path.join(out_dir, f"{asset_id}.txt")

    try:
        doc = fitz.open(pdf_path)
        pages = []
        for page in doc:
            txt = page.get_text("text")
            pages.append(txt)
        doc.close()
        full_text = "\n\n===== PAGE BREAK =====\n\n".join(pages)
        cleaned = _clean_text(full_text)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(cleaned)
    except Exception as e:
        logger.error(f"Error in Parsing asset {asset_id} : {e}")
        update_parse(asset_id, "", "FAILED", f"Parsing Failed: {e}")
        return

    update_parse(asset_id, out_path, "PARSED", "Parsing Complete")


def run_parse_batch(limit:int = BATCH_SIZE)  -> int:
    assets = fetch_pending_parse(limit)
    if not assets:
        logger.info("No New Document to Parse")
        return 0
    else:
        logger.info(f"Found {len(assets)} assets to Parse")
        for asset in assets:
            _parse_single(asset)
            if PARSE_SLEEP_S:
                time.sleep(PARSE_SLEEP_S)

        return(len(assets))
    

if __name__ == '__main__':
    count = run_parse_batch(limit=BATCH_SIZE)
    print(f"Parsed {count} new documents")