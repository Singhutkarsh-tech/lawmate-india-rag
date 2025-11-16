import os
import re
from pathlib import Path
from typing import Optional, Dict, List

from pydantic import BaseModel

PAGE_BREAK_MARKER = "\n\n===== PAGE BREAK =====\n\n"

class ExtractedTextData(BaseModel):
    doc_id:str
    text_by_page: Dict[int, str]
    full_text : str
    source_path:str
    errors:Optional[Dict[str, str]] = None

MULTISPACE_RE = re.compile(r"[ \t]+")
MULTINEWLINE_RE = re.compile(r"\n{3,}")
ISOLATED_PUNCT_RE = re.compile(r"(?m)^[^\w\s]{1,3}$")

def clean_text(text: str) -> str:

    text = text.replace("\x00", " ")
    text = MULTISPACE_RE.sub(" ", text)
    text = MULTINEWLINE_RE.sub("\n\n", text)
    text = ISOLATED_PUNCT_RE.sub("", text)
    return text.strip()

def load_parsed_txt(path : Path, doc_id :Optional[str] = None) ->ExtractedTextData:
    raw = path.read_text(encoding='utf-8')

    raw_pages: List[str] = raw.split(PAGE_BREAK_MARKER)
    text_by_page: Dict[int,str] = {}

    for idx, raw_page in enumerate(raw_pages):
        cleaned = clean_text(raw_page)
        if cleaned:
            text_by_page[idx] = cleaned

    full_text = "\n\n".join(text_by_page[p] for p in sorted(text_by_page))

    return ExtractedTextData(
        doc_id = doc_id or path.stem,
        text_by_page = text_by_page,
        full_text = full_text,
        source_path = str(path),
        errors = None
    )

def iter_parsed_files(root: str = "data/parsed") -> List[Path]:
    root_path = Path(root)
    return list(root_path.rglob("*.txt"))

def load_all_parsed_docs(root: str = "data/parsed") -> List[ExtractedTextData]:
    docs = []
    seen = set()

    for p in iter_parsed_files(root):
        doc_id = p.stem  
        if doc_id in seen:
            continue 

        seen.add(doc_id)
        etd = load_parsed_txt(p, doc_id=doc_id)
        docs.append(etd)

    return docs


if __name__ == "__main__":
    
    docs = load_all_parsed_docs()
    print(f"Loaded {len(docs)} documents")

    
    if docs:
        d = docs[0]
        print("Doc ID:", d.doc_id)
        print("Pages:", len(d.text_by_page))
        print("Preview page 0:")
        print(d.text_by_page.get(0, "")[:500]) 