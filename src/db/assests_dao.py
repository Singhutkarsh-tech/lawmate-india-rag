import hashlib
from datetime import datetime
from .database import get_conn
from .acts_dao import md5_hash


def insert_or_update_assests(asset):
    asset_id = md5_hash(f"{asset['act_id']}_{asset['pdf_url']}")
    asset["id"] = asset_id

    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO assets (
                id, act_id, version_label, view_url, pdf_url,
                pdf_sha256, pdf_bytes, fetched_at, parse_status,
                text_path, notes, inserted_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(act_id, pdf_url)
            DO UPDATE SET
                version_label = excluded.version_label,
                view_url = excluded.view_url,
                updated_at = CURRENT_TIMESTAMP;
            """,
            (
                asset["id"],
                asset["act_id"],
                asset.get("version_label"),
                asset.get("view_url"),
                asset["pdf_url"],
                None,
                None,
                None,
                "PENDING",
                None,
                None,
            )
        )
        conn.commit()

    return asset_id