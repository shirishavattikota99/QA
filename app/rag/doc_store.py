"""Search company documents (policies, FAQs, product guides) stored in ChromaDB.

Put files (.md, .txt, .pdf) in  app/rag/documents/  and run:

    python -m app.rag.doc_store                    # (re)build the index
    python -m app.rag.doc_store "your question"    # test a search and see distances

Uses a separate Chroma collection ("ciq_docs"), so your existing database-schema
collection ("ciq_db") is untouched.
"""
import os
import re
import sys
from pathlib import Path
from typing import Iterable, Optional

from app.helpers.logger import logger

DOCS_DIR = Path(os.getenv("DOCS_DIR", "app/rag/knowledge_base/collection_markdowns"))
PERSIST_DIR = os.getenv("CHROMA_DIR", "./ciq_db")
COLLECTION = "ciq_docs"
# same embedding model your existing vector store uses
MODEL_NAME = os.getenv("DOCS_EMBEDDING_MODEL", "sentence-transformers/multi-qa-mpnet-base-dot-v1")
# cosine distance: lower = more similar. Chunks farther than this are ignored.
MAX_DISTANCE = float(os.getenv("DOC_MAX_DISTANCE", "0.65"))
TOP_K = int(os.getenv("DOC_TOP_K", "3"))
SUPPORTED = {".md", ".txt", ".pdf"}


# ---------------------------------------------------------------------------
# Reading + chunking
# ---------------------------------------------------------------------------
def read_file(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError:
            logger.warning("Skipping %s: run `pip install pypdf` to read PDFs", path.name)
            return ""
        return "\n\n".join((page.extract_text() or "") for page in PdfReader(str(path)).pages)
    return path.read_text(encoding="utf-8", errors="replace")


def chunk_text(text: str, max_chars: int = 1000, overlap: int = 150) -> list[str]:
    """Split by markdown headings, then into ~1000-character windows with overlap.

    Each chunk keeps its section heading so it still makes sense on its own.
    """
    chunks: list[str] = []
    for section in re.split(r"\n(?=#{1,3} )", text.replace("\r\n", "\n")):
        section = section.strip()
        if not section:
            continue
        heading = section.split("\n", 1)[0] if section.startswith("#") else ""
        start = 0
        while start < len(section):
            end = min(start + max_chars, len(section))
            if end < len(section):  # prefer to cut at a paragraph/line/space boundary
                cut = max(section.rfind("\n\n", start, end), section.rfind("\n", start, end), section.rfind(" ", start, end))
                if cut > start + max_chars // 2:
                    end = cut
            piece = section[start:end].strip()
            if piece:
                chunks.append(piece if (start == 0 or not heading) else f"{heading}\n{piece}")
            if end >= len(section):
                break
            start = max(end - overlap, start + 1)
    return chunks


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------
class DocumentStore:
    def __init__(self, persist_dir: str = PERSIST_DIR, embeddings=None):
        from chromadb import PersistentClient

        os.makedirs(persist_dir, exist_ok=True)
        self._client = PersistentClient(path=persist_dir)
        self._embeddings = embeddings  # loaded lazily: the model is large
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION, metadata={"hnsw:space": "cosine"}
        )

    @property
    def embeddings(self):
        if self._embeddings is None:
            from langchain_huggingface import HuggingFaceEmbeddings

            logger.info("Loading embedding model %s (first use only)", MODEL_NAME)
            self._embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME)
        return self._embeddings

    def count(self) -> int:
        return self._collection.count()

    def search(self, query: str, top_k: int = TOP_K, max_distance: float = MAX_DISTANCE) -> list[dict]:
        """Return the closest chunks: [{"text", "source", "distance"}], nearest first."""
        if self.count() == 0:  # nothing indexed: don't even load the embedding model
            return []
        res = self._collection.query(
            query_embeddings=[self.embeddings.embed_query(query)],
            n_results=min(top_k, self.count()),
            include=["documents", "metadatas", "distances"],
        )
        hits = [
            {"text": doc, "source": (meta or {}).get("source", "document"), "distance": dist}
            for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0])
        ]
        return [h for h in hits if h["distance"] <= max_distance]

    def rebuild(self, items: Iterable[tuple[str, str]]) -> int:
        """Replace the whole index. items = (source_name, chunk_text) pairs."""
        items = list(items)
        try:
            self._client.delete_collection(COLLECTION)
        except Exception:
            pass
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION, metadata={"hnsw:space": "cosine"}
        )
        for i in range(0, len(items), 64):
            batch = items[i : i + 64]
            texts = [t for _, t in batch]
            self._collection.add(
                ids=[f"doc-{i + j}" for j in range(len(batch))],
                documents=texts,
                embeddings=self.embeddings.embed_documents(texts),
                metadatas=[{"source": s} for s, _ in batch],
            )
        return len(items)


_store: Optional[DocumentStore] = None


def get_store() -> DocumentStore:
    global _store
    if _store is None:
        _store = DocumentStore()
    return _store


def search_documents(query: str) -> list[dict]:
    """Never raises: if documents are unavailable the chat falls back to the database."""
    try:
        return get_store().search(query)
    except Exception as e:
        logger.error("Document search failed: %s", e)
        return []


# ---------------------------------------------------------------------------
# Existing schema knowledge ("ciq_db" collection built from collection_markdowns).
# Used as a FAST way to find which MongoDB collections a question needs, so the
# graph can skip one Gemini call. Local search only (~tens of ms after warm-up).
# ---------------------------------------------------------------------------
KB_COLLECTION = os.getenv("KB_COLLECTION", "ciq_db")
KB_MAX_DISTANCE = float(os.getenv("KB_MAX_DISTANCE", "0.6"))
KB_TOP_K = int(os.getenv("KB_TOP_K", "6"))
_kb = None


def search_knowledge(query: str, max_distance: float = KB_MAX_DISTANCE) -> list[dict]:
    """[{"collection": "transactions", "distance": 0.41}, ...] best match first, one per collection.

    Never raises: on any problem returns [] and the graph falls back to the LLM.
    """
    global _kb
    try:
        if _kb is None:
            from chromadb import PersistentClient

            _kb = PersistentClient(path=PERSIST_DIR).get_collection(KB_COLLECTION)
        if _kb.count() == 0:
            return []
        res = _kb.query(
            query_embeddings=[get_store().embeddings.embed_query(query)],
            n_results=min(KB_TOP_K, _kb.count()),
            include=["metadatas", "distances"],
        )
        best: dict[str, float] = {}
        for meta, dist in zip(res["metadatas"][0], res["distances"][0]):
            name = (meta or {}).get("collection") or (meta or {}).get("source") or ""
            name = Path(str(name)).stem  # tolerate "transactions.md"
            if name and dist <= max_distance and name not in best:
                best[name] = dist
        return [{"collection": n, "distance": d} for n, d in best.items()]
    except Exception as e:
        logger.error("Knowledge search failed: %s", e)
        return []


def ingest(docs_dir: Path = DOCS_DIR, store: Optional[DocumentStore] = None) -> tuple[int, int]:
    """Read every supported file under docs_dir and rebuild the index. Returns (files, chunks)."""
    store = store or get_store()
    items, files = [], 0
    for path in sorted(Path(docs_dir).rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED:
            chunks = chunk_text(read_file(path))
            if chunks:
                files += 1
                items += [(path.relative_to(docs_dir).as_posix(), c) for c in chunks]
    return files, store.rebuild(items)


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--kb":  # test collection lookup
        q = " ".join(sys.argv[2:])
        found = search_knowledge(q, max_distance=10)
        for h in found:
            flag = "USED   " if h["distance"] <= KB_MAX_DISTANCE else "ignored"
            print(f"{flag} distance={h['distance']:.3f}  collection={h['collection']}")
        print(f"\n(collections at or below KB_MAX_DISTANCE={KB_MAX_DISTANCE} skip the Gemini selection step)")
    elif len(sys.argv) > 1:  # test a search
        q = " ".join(sys.argv[1:])
        hits = get_store().search(q, top_k=5, max_distance=10)
        for h in hits:
            flag = "USED   " if h["distance"] <= MAX_DISTANCE else "ignored"
            print(f"{flag} distance={h['distance']:.3f}  [{h['source']}]  {h['text'][:90]!r}")
        print(f"\n(chunks at or below DOC_MAX_DISTANCE={MAX_DISTANCE} are used)")
    else:
        n_files, n_chunks = ingest()
        print(f"Indexed {n_files} file(s) into {n_chunks} chunk(s) from {DOCS_DIR}")