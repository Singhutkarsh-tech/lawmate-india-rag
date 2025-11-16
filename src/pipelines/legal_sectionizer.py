from __future__ import annotations
import re
from typing import Optional, Dict, List, Literal, Tuple
from pydantic import BaseModel
from .preprocessor import load_all_parsed_docs, ExtractedTextData

class LegalSection(BaseModel):
    act_id:str
    section_id:Optional[str] = None
    heading:Optional[str]
    body:str
    part:Optional[str]
    chapter:Optional[str]
    page_start:int
    page_end:int
    section_type: Literal["SECTION", "SCHEDULE", "OTHER"] = "SECTION"


PART_RE = re.compile(r"^(PART\s+[IVXLC]+(?:\s*[-–]\s*.+)?)\s*$", re.IGNORECASE)
CHAPTER_RE = re.compile(r"^(CHAPTER\s+[IVXLC]+(?:\s*[-–]\s*.+)?)\s*$", re.IGNORECASE)

SECTION_NUM_TITLE_RE = re.compile(
    r"^(\d+[A-Z]?(?:\(\d+[A-Z]?\))?)\s*\.\s*(.+)$"
)

# Example: "Section 2. Short title..."
SECTION_WORD_NUM_TITLE_RE = re.compile(
    r"^Section\s+(\d+[A-Z]?(?:\(\d+[A-Z]?\))?)\s*\.\s*(.+)$",
    re.IGNORECASE,
)

SCHEDULE_RE = re.compile(
    r"^(SCHEDULE\s+[A-Z0-9]+|FIRST SCHEDULE|SECOND SCHEDULE|THIRD SCHEDULE)\b.*$",
    re.IGNORECASE,
)

def _normalize_line(line:str) ->str:
    return line.strip()

def _is_part(line:str)->Optional[str]:
    p = PART_RE.match(line)
    return p.group(1).strip() if p else None

def _is_chapter(line:str)->Optional[str]:
    c = CHAPTER_RE.match(line)
    return c.group(1).strip() if c else None

def _is_schedule(line: str) -> Optional[str]:
    s = SCHEDULE_RE.match(line)
    return s.group(1).strip() if s else None

def _is_section_header(line: str) -> Optional[str]:
    line = line.strip()

    m = SECTION_WORD_NUM_TITLE_RE.match(line)
    if m:
        sec_id, heading = m.group(1), m.group(2)
        return sec_id.strip(), heading.strip()

    m = SECTION_NUM_TITLE_RE.match(line)
    if m:
        sec_id, heading = m.group(1), m.group(2)
        return sec_id.strip(), heading.strip()

    return None

def _lines_with_page_info(doc:ExtractedTextData) -> List[Tuple[int, str]]:
    result:List[Tuple[int, str]] = []
    for page_idx in sorted(doc.text_by_page.keys()):
        page_text = doc.text_by_page[page_idx]
        for line in page_text.splitlines():
            norm_line = _normalize_line(line)
            result.append((page_idx, norm_line))
    return result

def sectionize_document(doc: ExtractedTextData) -> List[LegalSection]:
    
    lines_with_pages = _lines_with_page_info(doc)


    sections: List[LegalSection] = []

    current_part: Optional[str] = None
    current_chapter: Optional[str] = None

    current_section_id: Optional[str] = None
    current_section_heading: Optional[str] = None
    current_section_type: Literal["SECTION", "SCHEDULE", "OTHER"] = "SECTION"
    current_body_lines: List[str] = []
    current_start_page: Optional[int] = None
    current_end_page: Optional[int] = None


    def _flush_current_section():
        nonlocal current_section_id, current_section_heading, current_body_lines
        nonlocal current_start_page, current_end_page, current_section_type

        if not current_body_lines and not current_section_heading:
            return
        
        sections.append(
            LegalSection(
                act_id = doc.doc_id,
                section_id = current_section_id,
                heading = current_section_heading,
                body = "\n".join(current_body_lines),
                part = current_part ,
                chapter = current_chapter,
                page_start = current_start_page if current_start_page is not None else 0,
                page_end = current_end_page if current_end_page is not None else (
                    current_start_page if current_start_page is not None else 0
                ),
                section_type = current_section_type
            )
        )

        current_section_id = None
        current_section_heading = None
        current_section_type = "SECTION"
        current_body_lines = []
        current_start_page = None
        current_end_page = None
        

    for page_idx, raw_line in lines_with_pages:
        line = raw_line.strip()

        if line is None:
            if current_section_id is not None or current_body_lines:
                current_body_lines.append("")
                current_end_page = page_idx
            continue

        maybe_part = _is_part(line)
        if maybe_part:
            current_part = maybe_part
            continue

        maybe_chapter = _is_chapter(line)
        if maybe_chapter:
            current_chapter = maybe_chapter
            continue

        maybe_schedule = _is_schedule(line)
        if maybe_schedule:
            _flush_current_section()

            current_section_id = maybe_schedule  # e.g. "SCHEDULE I"
            current_section_heading = None
            current_section_type = "SCHEDULE"
            current_body_lines = []
            current_start_page = page_idx
            current_end_page = page_idx
            continue

        sec_header = _is_section_header(line)
        if sec_header:
            _flush_current_section()

            sec_id, heading = sec_header
            current_section_id = sec_id
            current_section_heading = heading
            current_section_type = "SECTION"
            current_body_lines = []
            current_start_page = page_idx
            current_end_page = page_idx
            continue

        if current_section_id is None and not current_body_lines:
            current_section_id = None
            current_section_heading = "PREAMBLE"
            current_section_type = "OTHER"
            current_start_page = page_idx
            current_end_page = page_idx

        current_body_lines.append(line)
        current_end_page = page_idx

    _flush_current_section()

    return sections


def sectionize_all_documents(docs: List[ExtractedTextData]) -> Dict[str, List[LegalSection]]:
    result:Dict[str, List[LegalSection]] = {}

    for doc in docs:
        result[doc.doc_id] = sectionize_document(doc)
    return result

if __name__ == "__main__":
    print("Loading parsed documents...")
    docs = load_all_parsed_docs()
    print(f"Found {len(docs)} documents")

    if not docs:
        print("No documents found under data/parsed")
    else:
        doc = docs[0]
        print(f"\nSectionizing doc_id={doc.doc_id} ...")
        sections = sectionize_document(doc)
        print(f"Found {len(sections)} sections\n")

        # Show first 3 sections for inspection
        for i, s in enumerate(sections[:3]):
            print(f"--- Section {i+1} ---")
            print("Type     :", s.section_type)
            print("Part     :", s.part)
            print("Chapter  :", s.chapter)
            print("Sec ID   :", s.section_id)
            print("Heading  :", s.heading)
            print("Pages    :", s.page_start, "→", s.page_end)
            print("Body preview:")
            print(s.body[:500], "...\n")