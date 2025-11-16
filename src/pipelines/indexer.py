from __future__ import annotations
import os
from typing import List, Optional, Dict
from pydantic import BaseModel

from .preprocessor import ExtractedTextData, load_all_parsed_docs
from .chunker import Chunk, chunk_sections
from .legal_sectionizer import LegalSection, sectionize_document
from .embedder import EmbeddedChunk, embed_chunk

from pymilvus import FieldSchema, Collection, CollectionSchema, DataType, connections, utility

MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")
MILVUS_ALIAS = "default"
COLLECTION_NAME = os.getenv("LAW_MATE_COLLECTION", "lawmate_india_acts")
EMBED_DIM = int(os.getenv("LAW_MATE_EMBED_DIM", "384"))

INDEX_PARAMS: Dict = {
    "metric_type": "COSINE",      
    "index_type": "IVF_FLAT",
    "params": {"nlist": 1024},
}

def connect_milvus()->None:
    if not connections.has_connection(MILVUS_ALIAS):
        connections.connect(
            alias = MILVUS_ALIAS,
            host = MILVUS_HOST,
            port = MILVUS_PORT
    )
        

def get_or_create_collection() -> Collection:
    
    connect_milvus()
    existing = utility.list_collections(using=MILVUS_ALIAS)
    if COLLECTION_NAME in existing:
        coll = Collection(name = COLLECTION_NAME, using = MILVUS_ALIAS)
        coll.load()
        return coll
    
    fields = [
        FieldSchema(
            name = 'chunk_id',
            dtype = DataType.VARCHAR,
            is_primary = True,
            auto_id = False,
            max_length = 128
        ),
        FieldSchema(
            name="doc_id",
            dtype = DataType.VARCHAR,
            max_length = 64          
        ),
          FieldSchema(
            name="section_id",
            dtype=DataType.VARCHAR,
            max_length=32,
        ),
        FieldSchema(
            name="section_heading",
            dtype=DataType.VARCHAR,
            max_length=512,
        ),
        FieldSchema(
            name="part",
            dtype=DataType.VARCHAR,
            max_length=64,
        ),
        FieldSchema(
            name="chapter",
            dtype=DataType.VARCHAR,
            max_length=64,
        ),
        FieldSchema(
            name="page_start",
            dtype=DataType.INT32,
        ),
        FieldSchema(
            name="page_end",
            dtype=DataType.INT32,
        ),
        FieldSchema(
            name="text",
            dtype=DataType.VARCHAR,
            max_length=8192,  #can be changed according tot the size of the chunk
        ),
        FieldSchema(
            name="embedding",
            dtype=DataType.FLOAT_VECTOR,
            dim=EMBED_DIM,
        ),
    ]
    
    schema = CollectionSchema(
        fields = fields,
        description =  "LawMate India - legal act chunks"
    )

    coll = Collection(
        name = COLLECTION_NAME,
        schema = schema,
        using = MILVUS_ALIAS,
        shards_num = 2
    )

    coll.create_index(
        field_name = "embedding",
        index_params = INDEX_PARAMS
    )

    utility.index_building_progress(COLLECTION_NAME, using = MILVUS_ALIAS)
    coll.flush()
    coll.load()
    return coll


def delete_doc_chunks(doc_id: str) -> int:
    coll = get_or_create_collection()
    expr = f"doc_id == '{doc_id}'"
    res = coll.delete(expr)
    coll.flush()

    try:
        return res.delete_count
    except AttributeError:
        return 0

def index_chunks(embedded_chunks: List[EmbeddedChunk]) ->int:
    if not embedded_chunks:
        return 0

    coll: Collection = get_or_create_collection()

    rows = []
    for ec in embedded_chunks:
        rows.append(
            {
                "chunk_id": ec.chunk_id,
                "doc_id": ec.doc_id,
                "section_id": ec.section_id or "",
                "section_heading": ec.section_heading or "",
                "part": ec.part or "",
                "chapter": ec.chapter or "",
                "page_start": ec.page_start,
                "page_end": ec.page_end,
                "text": ec.text,
                "embedding": ec.embedding,  # this is a List[float]
            }
        )

    insert_result = coll.insert(rows)
    coll.flush()

    try:
        return len(insert_result.primary_keys)
    except AttributeError:
        return len(rows)
    
def index_document(doc: ExtractedTextData, *, reindex: bool = True) -> int:
    if reindex:
        deleted = delete_doc_chunks(doc.doc_id)
        if deleted:
            print(f"Deleted {deleted} chunks for Document {doc.doc_id} from Milvus Database")

    sections = sectionize_document(doc)
    chunks = chunk_sections(sections)
    embedded = embed_chunk(chunks)
    inserted = index_chunks(embedded)

    print(
        f"[indexer] doc_id={doc.doc_id}: sections={len(sections)}, "
        f"chunks={len(chunks)}, inserted={inserted}"
    )
    return inserted


def index_all_documents(max_docs: int | None = None, *, reindex: bool = True) -> None:
    print("Loading parsed documents...")
    docs = load_all_parsed_docs()
    print(f"Found {len(docs)} documents")

    if max_docs is not None:
        docs = docs[:max_docs]

    total_inserted = 0
    for i, doc in enumerate(docs, start=1):
        print(f"\n[{i}/{len(docs)}] Indexing doc_id={doc.doc_id} ...")
        inserted = index_document(doc, reindex=reindex)
        total_inserted += inserted

    print(f"\n[indexer] Total inserted chunks across docs: {total_inserted}")


if __name__ == "__main__":
    # Simple CLI behaviour:
    # - index all docs
    # - you can later swap this to only index one doc for testing
    print("Starting to index all document")
    index_all_documents(max_docs=None, reindex=True)
    print("Indexing Complete")