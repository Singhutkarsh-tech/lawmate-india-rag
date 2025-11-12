import hashlib
import json
from datetime import datetime
from .database import get_conn
from .acts_dao import md5_hash

def insert_or_update_assests(asset):
    asset_id = md5_hash(f"{asset["act_id"]}_{asset['pdf_url']}")
    asset['id'] = asset_id
    
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO act_assets (
                id, act_id, pdf_url, file_path, checksum, downloaded, inserted_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(id)
            DO UPDATE SET
                file_path=excluded.file_path,
                checksum=excluded.checksum,
                downloaded=excluded.downloaded,
                updated_at=CURRENT_TIMESTAMP;
            """,
            (
                asset["id"],
                asset["act_id"],
                asset["pdf_url"],
                asset["file_path"],
                asset.get("checksum"),
                int(asset.get("downloaded", False))
            )
        )
        conn.commit()
    return asset_id