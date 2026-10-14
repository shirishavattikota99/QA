# from typing import List
# from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_core.documents import Document
# import numpy as np
# import re

# class EmbeddingPipeline:
#     def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
#         self.model = HuggingFaceEmbeddings(model_name=model_name)
#         print(f"[INFO] Loaded embedding model: {model_name}")

#     # ---------------------------------
#     # Markdown semantic chunking
#     # ---------------------------------
#     def chunk_markdown(self, content: str, collection:str) -> List[Document]:
#         chunks: List[Document] = []

#         # Split by top-level or second-level headers
#         sections = re.split(r"\n(?=## )", content)

#         collection_name = collection

#         for section in sections:
#             section = section.strip()
#             if not section:
#                 continue

#             # Extract section title
#             header_match = re.match(r"## (.+)", section)
#             section_title = header_match.group(1) if header_match else "Overview"

#             # ---------------------------------
#             # Split field blocks inside section
#             # ---------------------------------
#             field_blocks = re.split(r"\n- \*\*(.+?)\*\*", section)

#             # If no fields → keep section as one chunk
#             if len(field_blocks) == 1:
#                 chunks.append(
#                     Document(
#                         page_content=section,
#                         metadata={
#                             "collection": collection_name,
#                             "section": section_title,
#                             "type": "section",
#                         },
#                     )
#                 )
#                 continue

#             # First block is section intro
#             section_intro = field_blocks[0].strip()
#             if section_intro:
#                 chunks.append(
#                     Document(
#                         page_content=section_intro,
#                         metadata={
#                             "collection": collection_name,
#                             "section": section_title,
#                             "type": "section_intro",
#                         },
#                     )
#                 )

#             # Remaining blocks are (field_name, content)
#             for i in range(1, len(field_blocks), 2):
#                 field_name = field_blocks[i].strip()
#                 field_text = field_blocks[i + 1].strip()

#                 text = (
#                     f"Collection: {collection_name}\n"
#                     f"Section: {section_title}\n"
#                     f"Field: {field_name}\n"
#                     f"{field_text}"
#                 )

#                 chunks.append(
#                     Document(
#                         page_content=text,
#                         metadata={
#                             "collection": collection_name,
#                             "section": section_title,
#                             "field": field_name,
#                             "type": "field",
#                         },
#                     )
#                 )

#         print(f"[INFO] Created {len(chunks)} semantic chunks")
#         return chunks

#     # ---------------------------------
#     # Embedding
#     # ---------------------------------
#     def embed_chunks(self, chunks: List[Document]) -> np.ndarray:
#         texts = [chunk.page_content for chunk in chunks]
#         print(f"[INFO] Generating embeddings for {len(texts)} chunks...")
#         embeddings = self.model.embed_documents(texts)
#         print(f"[INFO] Generated {len(embeddings)} embeddings")
#         return np.array(embeddings)






# from typing import List
# from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_core.documents import Document
# import numpy as np
# import re

# class EmbeddingPipeline:
#     def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
#         self.model = HuggingFaceEmbeddings(model_name=model_name)
#         print(f"[INFO] Loaded embedding model: {model_name}")

#     # ---------------------------------
#     # Markdown semantic chunking
#     # ---------------------------------
#     def chunk_markdown(self, content: str, collection: str) -> List[Document]:
#         chunks: List[Document] = []
#         collection_name = collection

#         # Split by top-level or second-level headers
#         sections = re.split(r"\n(?=## )", content)

#         for section in sections:
#             section = section.strip()
#             if not section:
#                 continue

#             # Extract section title
#             header_match = re.match(r"## (.+)", section)
#             section_title = header_match.group(1) if header_match else "Overview"

#             # Split by fields
#             field_blocks = re.split(r"\n- \*\*(.+?)\*\*", section)

#             # If no fields → treat as single section summary
#             if len(field_blocks) == 1:
#                 chunks.append(
#                     Document(
#                         page_content=section,
#                         metadata={
#                             "collection": collection_name,
#                             "section": section_title,
#                             "type": "section_summary",
#                         },
#                     )
#                 )
#                 continue

#             # Section intro
#             section_intro = field_blocks[0].strip()
#             if section_intro:
#                 chunks.append(
#                     Document(
#                         page_content=section_intro,
#                         metadata={
#                             "collection": collection_name,
#                             "section": section_title,
#                             "type": "section_intro",
#                         },
#                     )
#                 )

#             # Atomic field chunks
#             field_texts = []
#             for i in range(1, len(field_blocks), 2):
#                 field_name = field_blocks[i].strip()
#                 field_text = field_blocks[i + 1].strip()
#                 field_texts.append((field_name, field_text))

#                 text = f"{collection_name}.{field_name}\n{field_text}"

#                 chunks.append(
#                     Document(
#                         page_content=text,
#                         metadata={
#                             "collection": collection_name,
#                             "section": section_title,
#                             "field": field_name,
#                             "type": "field_atomic",
#                         },
#                     )
#                 )

#             # Optional: create small group chunks with overlapping fields (semantic overlap)
#             # Example: 3–4 fields per group, 1 field overlap
#             group_size = 3
#             overlap = 1
#             for j in range(0, len(field_texts), group_size - overlap):
#                 group_fields = field_texts[j:j + group_size]
#                 if not group_fields:
#                     continue
#                 group_text = "\n".join([f"{name}: {text}" for name, text in group_fields])
#                 group_field_names = ", ".join([name for name, _ in group_fields])
#                 chunks.append(
#                     Document(
#                         page_content=f"{collection_name}.{section_title} (Fields: {group_field_names})\n{group_text}",
#                         metadata={
#                             "collection": collection_name,
#                             "section": section_title,
#                             "fields": [name for name, _ in group_fields],
#                             "type": "field_group",
#                         },
#                     )
#                 )

#         print(f"[INFO] Created {len(chunks)} semantic chunks")
#         return chunks

#     # ---------------------------------
#     # Embedding
#     # ---------------------------------
#     def embed_chunks(self, chunks: List[Document]) -> np.ndarray:
#         texts = [chunk.page_content for chunk in chunks]
#         print(f"[INFO] Generating embeddings for {len(texts)} chunks...")
#         embeddings = self.model.embed_documents(texts)
#         print(f"[INFO] Generated {len(embeddings)} embeddings")
#         return np.array(embeddings)








from typing import List
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
import numpy as np
import re
import tiktoken

class EmbeddingPipeline:
    def __init__(self, model_name: str ):
        self.model = HuggingFaceEmbeddings(model_name=model_name)
        print(f"[INFO] Loaded embedding model: {model_name}")
        # Tokenizer for token-based chunking
        self.encoding = tiktoken.get_encoding("cl100k_base")

    # ---------------------------------
    # Token-based Markdown chunking with overlap
    # ---------------------------------
    def chunk_markdown(self, content: str, collection: str, 
                       max_tokens: int = 200, overlap_tokens: int = 50) -> List[Document]:
        """
        Chunk a markdown file into smaller token-based chunks with overlap.
        Preserves section and field metadata.
        """
        chunks: List[Document] = []
        collection_name = collection

        # Split by top-level or second-level headers
        sections = re.split(r"\n(?=## )", content)

        for section in sections:
            section = section.strip()
            if not section:
                continue

            # Extract section title
            header_match = re.match(r"## (.+)", section)
            section_title = header_match.group(1) if header_match else "Overview"

            # Split by fields
            field_blocks = re.split(r"\n- \*\*(.+?)\*\*", section)

            # If no fields → treat as section summary
            if len(field_blocks) == 1:
                self._token_chunk_add(chunks, section, collection_name, section_title, chunk_type="section_summary", max_tokens=max_tokens, overlap_tokens=overlap_tokens)
                continue

            # Section intro
            section_intro = field_blocks[0].strip()
            if section_intro:
                self._token_chunk_add(chunks, section_intro, collection_name, section_title, chunk_type="section_intro", max_tokens=max_tokens, overlap_tokens=overlap_tokens)

            # Individual field chunks
            field_texts = []
            for i in range(1, len(field_blocks), 2):
                field_name = field_blocks[i].strip()
                field_text = field_blocks[i + 1].strip()
                text = f"{collection_name}.{field_name}\n{field_text}"
                metadata = {
                    "collection": collection_name,
                    "section": section_title,
                    "field": field_name,
                    "type": "field_atomic"
                }
                self._token_chunk_add(chunks, text, collection_name, section_title, metadata=metadata, max_tokens=max_tokens, overlap_tokens=overlap_tokens)
                field_texts.append((field_name, field_text))

            # Optional grouped field chunks for extra context
            group_size = 3
            overlap = 1
            for j in range(0, len(field_texts), group_size - overlap):
                group_fields = field_texts[j:j + group_size]
                if not group_fields:
                    continue
                group_text = "\n".join([f"{name}: {text}" for name, text in group_fields])
                group_field_names = ", ".join([name for name, _ in group_fields])
                metadata = {
                    "collection": collection_name,
                    "section": section_title,
                    "fields": [name for name, _ in group_fields],
                    "type": "field_group"
                }
                self._token_chunk_add(chunks, f"{collection_name}.{section_title} (Fields: {group_field_names})\n{group_text}", collection_name, section_title, metadata=metadata, max_tokens=max_tokens, overlap_tokens=overlap_tokens)

        print(f"[INFO] Created {len(chunks)} semantic chunks")
        return chunks

    # ---------------------------------
    # Helper function: token-based chunking with overlap
    # ---------------------------------
    def _token_chunk_add(self, chunks: List[Document], text: str, collection_name: str,
                         section_title: str, metadata: dict = None,
                         chunk_type: str = None, max_tokens: int = 200, overlap_tokens: int = 50):
        tokens = self.encoding.encode(text)
        start = 0
        while start < len(tokens):
            end = min(start + max_tokens, len(tokens))
            chunk_tokens = tokens[start:end]
            chunk_text = self.encoding.decode(chunk_tokens)
            chunk_metadata = metadata or {
                "collection": collection_name,
                "section": section_title,
                "type": chunk_type
            }
            chunks.append(Document(page_content=chunk_text, metadata=chunk_metadata))
            start += max_tokens - overlap_tokens

    # ---------------------------------
    # Embedding
    # ---------------------------------
    def embed_chunks(self, chunks: List[Document]) -> np.ndarray:
        texts = [chunk.page_content for chunk in chunks]
        print(f"[INFO] Generating embeddings for {len(texts)} chunks...")
        embeddings = self.model.embed_documents(texts)
        print(f"[INFO] Generated {len(embeddings)} embeddings")
        return np.array(embeddings)
