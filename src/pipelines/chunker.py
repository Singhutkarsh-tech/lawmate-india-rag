from __future__ import annotations
import re
from typing import Optional, List, Dict
from pydantic import BaseModel

from .preprocessor import ExtractedTextData, load_all_parsed_docs
from .legal_sectionizer import LegalSection, sectionize_document

MAX_CHARS_PER_CHUNK = 1200
OVERLAP_CHARS = 200


class Chunk(BaseModel):
    # Smallest Retrivable RAG unit
    doc_id:str
    section_id:Optional[str]
    chunk_id:str
    chunk_index:int
    text:str

    part:Optional[str]
    section_heading:Optional[str]
    chapter:Optional[str]

    page_start:int
    page_end:int


_SENT_SPLIT_RE = re.compile(r"(?<=[.?!])\s+")

def _split_to_sentences(body:str)->List[str]:
    
    body=body.strip()
    if not body:
        return []

    parts = _SENT_SPLIT_RE.split(body)
    sentences = [s.strip() for s in parts if s.strip()]
    return sentences



def _chunk_sections(section:LegalSection) -> List[Chunk]:
    body = section.body
    sentences = _split_to_sentences(body)
    chunks:List[Chunk]=[]

    if not sentences:
        return chunks

    doc_id = section.act_id
    sec_id = section.section_id or "PREAMBLE"

    current_sentences:List[str] = []
    current_length = 0
    chunk_index = 0
    
    def _flush_chunk(sent_list:List[str], idx:int):
        if not sent_list:
            return None
        chunk_text = " ".join(sent_list).strip()
        if not chunk_text:
            return None
        
        chunk = Chunk(
            doc_id = doc_id,
            section_id = section.section_id,
            chunk_id = f"{doc_id}-{sec_id}-{idx}",
            chunk_index=idx,
            text=chunk_text,
            part=section.part,
            chapter=section.chapter,
            section_heading=section.heading,
            page_start=section.page_start,
            page_end=section.page_end
        )

        return chunk
        
    for sent in sentences:
        sent_len = len(sent) + 1

        # If current sentence will cause the total Chars per chunk to go over limit, we flush here and start new window with required overlap
        if current_sentences and current_length + sent_len > MAX_CHARS_PER_CHUNK:
            chunk = _flush_chunk(current_sentences, chunk_index)
            if chunk:
                chunks.append(chunk)
                chunk_index += 1

            overlap_text = " ".join(current_sentences)[-OVERLAP_CHARS:]
            if overlap_text:
                current_sentences = [overlap_text, sent]
                current_length = len(overlap_text) + 1 + sent_len

            else:
                current_sentences = [sent]
                current_length = sent_len

        else:
            current_sentences.append(sent)
            current_length += sent_len

    final_chunk = _flush_chunk(current_sentences, chunk_index)
    if final_chunk:
        chunks.append(final_chunk)

    return chunks



def chunk_sections(section:List[LegalSection])->List[Chunk]:
    all_chunks:List[Chunk] = []
    for s in section:
        sec_chunks = _chunk_sections(s)
        all_chunks.extend(sec_chunks)
    return all_chunks
    


def chunk_all_documents(docs:List[ExtractedTextData])->Dict[str, List[Chunk]]:
    result: Dict[str, List[Chunk]]
    for doc in docs:
        section = sectionize_document(doc)
        chunk = chunk_sections(section)
        result[doc.doc_id] = chunk
    return result


if __name__ == "__main__":
    print("Loading parsed documents...")
    docs = load_all_parsed_docs()
    print(f"Found {len(docs)} documents")

    if not docs:
        print("No documents found under data/parsed")
    else:
        doc = docs[0]
        print(f"\nSectionizing + chunking doc_id={doc.doc_id} ...")
        sections = sectionize_document(doc)
        print(f"Sections: {len(sections)}")

        chunks = chunk_sections(sections)
        print(f"Chunks: {len(chunks)}\n")

        for i, c in enumerate(chunks[:5]):
            print(f"--- Chunk {i+1} ---")
            print("chunk_id   :", c.chunk_id)
            print("section_id :", c.section_id)
            print("heading    :", c.section_heading)
            print("pages      :", c.page_start, "→", c.page_end)
            print("text preview:")
            print(c.text[:400], "...\n")