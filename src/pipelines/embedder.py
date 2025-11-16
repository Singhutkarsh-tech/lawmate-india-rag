from __future__ import annotations

from typing import List
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

from .chunker import Chunk, chunk_sections
from .preprocessor import load_all_parsed_docs, ExtractedTextData
from .legal_sectionizer import LegalSection, sectionize_document

EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBED_BATCH_SIZE = 32

class EmbeddedChunk(BaseModel):
    doc_id:str
    section_id:str | None
    chunk_id:str
    chunk_index:int
    text:str

    part:str | None
    chapter:str|None
    section_heading:str|None
    page_start:int
    page_end:int

    embedding:List[float]

_model:SentenceTransformer|None = None

def get_model() ->SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL_NAME)
    return _model

def embed_chunk(chunks: List[Chunk])->List[EmbeddedChunk]:
    if not chunks:
        return []
    
    model = get_model()

    texts = [c.text for c in chunks]
    embedded_chunks:List[EmbeddedChunk] = []

    for i in range(0, len(texts), EMBED_BATCH_SIZE):
        end = i + EMBED_BATCH_SIZE
        batch_texts = texts[i:end]
        batch_chunks = chunks[i:end]

        embeddings = model.encode(batch_texts, show_progress_bar = True)

        for c, emb in zip(batch_chunks, embeddings):
            ec = EmbeddedChunk(
                doc_id= c.doc_id,
                section_id=c.section_id,
                chunk_id=c.chunk_id,
                chunk_index=c.chunk_index,
                text=c.text,
                part=c.part,
                chapter=c.chapter,
                section_heading=c.section_heading,
                page_start=c.page_start,
                page_end=c.page_end,
                embedding=emb.tolist(),
            )
            embedded_chunks.append(ec)
    
    return embedded_chunks

def embed_document(doc: ExtractedTextData) -> List[EmbeddedChunk]:
   
    sections = sectionize_document(doc)
    chunks = chunk_sections(sections)
    return embed_chunk(chunks)


if __name__ == "__main__":
    print("Loading parsed documents...")
    docs = load_all_parsed_docs()
    print(f"Found {len(docs)} documents")

    if not docs:
        print("No documents found under data/parsed")
    else:
        doc = docs[0]
        print(f"\nEmbedding doc_id={doc.doc_id} ...")

        sections = sectionize_document(doc)
        print(f"Sections: {len(sections)}")
        from .chunker import chunk_sections as _chunk_sections
        chunks = _chunk_sections(sections)
        print(f"Chunks: {len(chunks)}")

        embedded = embed_chunk(chunks)
        print(f"Embedded chunks: {len(embedded)}\n")

        # Show first 2 for inspection
        for i, ec in enumerate(embedded[:2]):
            print(f"--- Embedded Chunk {i+1} ---")
            print("chunk_id   :", ec.chunk_id)
            print("section_id :", ec.section_id)
            print("heading    :", ec.section_heading)
            print("pages      :", ec.page_start, "→", ec.page_end)
            print("embedding dim:", len(ec.embedding))
            print("text preview:")
            print(ec.text[:300], "...\n")