import hashlib
import json
from datetime import datetime
from .database import get_conn

def md5_hash(value:str) -> str:
    return hashlib.md5(value.encode('utf-8')).hexdigest()

def insert_or_update_act(act):
    act_id = md5_hash(f'{act["source_portal"]}_{act["handle_id"]}')
    act["id"] = act_id
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO acts (
                id, source_portal, handle_id, ministry_slug, ministry_name,
                act_title, act_number, enactment_date_raw, raw_row_json, inserted_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(source_portal, handle_id)
            DO UPDATE SET
                ministry_slug=excluded.ministry_slug,
                ministry_name=excluded.ministry_name,
                act_title=excluded.act_title,
                act_number=excluded.act_number,
                enactment_date_raw=excluded.enactment_date_raw,
                raw_row_json=excluded.raw_row_json,
                updated_at=CURRENT_TIMESTAMP;
            """,
            (
                act["id"],
                act["source_portal"],
                act["handle_id"],
                act["ministry_slug"],
                act["ministry_name"],
                act["act_title"],
                act["act_number"],
                act["enactment_date_raw"],
                json.dumps(act.get("raw_row_json", {}))
            )
        )
        conn.commit()
    return act_id