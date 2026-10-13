from pprint import pprint
from typing import Optional
from chromadb import PersistentClient
from langchain_huggingface import HuggingFaceEmbeddings
import uuid
from langchain_core.documents import Document
from pathlib import Path
import os
from app.helpers.logger import logger


import tiktoken

from app.rag.embedding import EmbeddingPipeline

MARKDOWN_DIR = Path("app/rag/knowledge_base/collection_markdowns")
PERSIST_DIR = "./ciq_db"
COLLECTION_NAME = "ciq_db"
# MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_NAME = "sentence-transformers/multi-qa-mpnet-base-dot-v1"

class ChromaVectorStore:
    def __init__(self,persist_dir: str = PERSIST_DIR,collection_name: str = COLLECTION_NAME,model_name: str = MODEL_NAME):
        self.persist_dir = persist_dir
        os.makedirs(self.persist_dir, exist_ok=True)
        self.collection_name = collection_name

        # Load embedding model
        self.embeddings = HuggingFaceEmbeddings(model_name=model_name)

        # Initialize Chroma
        self.client = PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"Initialized Chroma collection: {collection_name}")

    def store_chunks(self, chunks, embeddings):
        logger.info(f"IStoring {len(chunks)} chunks to ChromaDB...")
        ids = [str(uuid.uuid4()) for _ in chunks]
        documents = [c.page_content for c in chunks]
        metadatas = [c.metadata for c in chunks]
        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        logger.info("Chunks stored successfully and persisted in Vector DB at path: {self.persist_dir}!")
    
    def clear_collection(self):
        logger.warning(f"Clearing collection: {self.collection_name}")
        self.client.delete_collection(name='ciq_db')
        logger.warning("Collection cleared successfully!")


    def get_collection_documents(self, limit: Optional[int] = None):
        result = self.collection.get(
            include=["documents", "metadatas"],
            limit=limit
        )
        return [
            Document(page_content=doc, metadata=meta)
            for doc, meta in zip(
                result.get("documents", []),
                result.get("metadatas", [])
            )
        ]

    def similarity_search(self, query: str, top_k: int = 5):
        query_emb = self.embeddings.embed_query(query)
        return self.collection.query(
            query_embeddings=[query_emb], n_results=top_k
        )
    
    def as_retriever(self, top_k=5):
        """Convert similarity search into a LangChain retriever."""
        def _retrieve(query: str):
            results = self.similarity_search(query, top_k)
            documents = []
            for doc_text, metadata in zip(results["documents"][0], results["metadatas"][0]):
                documents.append(Document(page_content=doc_text, metadata=metadata))

            return documents

        return _retrieve
    
    def count_openai_tokens(self, text: str) -> int:
        """
        Count tokens using OpenAI-compatible tokenizer (GPT-4 / GPT-4o / GPT-3.5)
        """
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))


if __name__ == "__main__":
    # Initialize pipeline & vector store
    # pipe = EmbeddingPipeline(model_name=MODEL_NAME)
    store = ChromaVectorStore(persist_dir=PERSIST_DIR, collection_name=COLLECTION_NAME, model_name=MODEL_NAME)

    # all_chunks = []

    # for md_file in MARKDOWN_DIR.glob("*.md"):
    #     logger.info(f"Processing file: {md_file.name}")
    #     content = md_file.read_text(encoding="utf-8")
    #     chunks = pipe.chunk_markdown(content, collection=md_file.stem)
    #     embeddings = pipe.embed_chunks(chunks)
    #     store.store_chunks(chunks, embeddings)
    #     all_chunks.extend(chunks)

    # logger.info(f"[INFO] Successfully processed {len(all_chunks)} chunks from {len(list(MARKDOWN_DIR.glob('*.md')))} files!")

    # Example similarity search
    query = "get the players who registered through the affiliates and what kind of channel did they come through"
    results = store.similarity_search(query,top_k=10)
    pprint(results)

