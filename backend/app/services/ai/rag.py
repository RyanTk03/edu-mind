"""
RAG System for EDU-MIND.

Handles document ingestion and semantic retrieval using ChromaDB.
"""

import logging
import os
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

from .config import ai_settings

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON INSTANCES
# ═══════════════════════════════════════════════════════════════════════════════

_client: Optional[chromadb.PersistentClient] = None
_embedder: Optional[SentenceTransformer] = None


def _get_client() -> chromadb.PersistentClient:
    """Get or create ChromaDB client."""
    global _client
    if _client is None:
        # Ensure directory exists
        persist_dir = ai_settings.chroma_persist_dir
        logger.info(f"Initializing ChromaDB client at: {persist_dir}")
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        logger.info("ChromaDB client initialized successfully")
    return _client


def _get_embedder() -> SentenceTransformer:
    """Get or create embedding model."""
    global _embedder
    if _embedder is None:
        logger.info(f"Loading embedding model: {ai_settings.embedding_model}")
        _embedder = SentenceTransformer(ai_settings.embedding_model)
        logger.info("Embedding model loaded successfully")
    return _embedder


def _embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts."""
    embedder = _get_embedder()
    embeddings = embedder.encode(texts, convert_to_numpy=True)
    return embeddings.tolist()


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════


def create_collection(session_id: str) -> chromadb.Collection:
    """
    Create or get a ChromaDB collection for a session.

    Args:
        session_id: Unique session identifier.

    Returns:
        ChromaDB collection object.
    """
    client = _get_client()
    collection_name = f"session_{session_id}"
    logger.info(f"Getting/creating collection: {collection_name}")

    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"session_id": session_id},
    )
    logger.info(f"Collection {collection_name} ready, current count: {collection.count()}")
    return collection


def delete_collection(session_id: str) -> bool:
    """
    Delete a session's collection.

    Args:
        session_id: Unique session identifier.

    Returns:
        True if deleted, False if not found.
    """
    client = _get_client()
    collection_name = f"session_{session_id}"

    try:
        client.delete_collection(collection_name)
        return True
    except ValueError:
        return False


def ingest_text(
    session_id: str,
    text: str,
    source: str = "unknown",
    metadata: Optional[dict] = None,
) -> int:
    """
    Ingest raw text into a session's collection.

    Args:
        session_id: Session identifier.
        text: Raw text content to ingest.
        source: Source identifier (e.g., filename).
        metadata: Additional metadata for chunks.

    Returns:
        Number of chunks created.
    """
    logger.info(f"Ingesting text for session {session_id}, source: {source}, length: {len(text)}")
    collection = create_collection(session_id)

    # Split text into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=ai_settings.chunk_size,
        chunk_overlap=ai_settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_text(text)
    logger.info(f"Split text into {len(chunks)} chunks")

    if not chunks:
        logger.warning("No chunks created from text")
        return 0

    # Prepare data for ChromaDB
    ids = [f"{source}_{i}" for i in range(len(chunks))]
    logger.info("Generating embeddings...")
    embeddings = _embed_texts(chunks)
    logger.info(f"Generated {len(embeddings)} embeddings")

    metadatas = [
        {
            "source": source,
            "chunk_index": i,
            **(metadata or {}),
        }
        for i in range(len(chunks))
    ]

    # Add to collection
    logger.info(f"Adding {len(chunks)} chunks to collection {collection.name}")
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas,
    )
    logger.info(f"Successfully added chunks. Collection now has {collection.count()} documents")

    return len(chunks)


def ingest_pdf(
    session_id: str,
    pdf_path: str,
    metadata: Optional[dict] = None,
) -> int:
    """
    Ingest a PDF file into a session's collection.

    Args:
        session_id: Session identifier.
        pdf_path: Path to PDF file.
        metadata: Additional metadata for chunks.

    Returns:
        Number of chunks created.
    """
    logger.info(f"Loading PDF: {pdf_path}")
    loader = PyPDFLoader(pdf_path)
    pages = loader.load()
    logger.info(f"Loaded {len(pages)} pages from PDF")

    full_text = "\n\n".join(page.page_content for page in pages)
    logger.info(f"Extracted {len(full_text)} characters from PDF")
    source = os.path.basename(pdf_path)

    return ingest_text(
        session_id=session_id,
        text=full_text,
        source=source,
        metadata=metadata,
    )


def get_context(
    session_id: str,
    query: str,
    k: Optional[int] = None,
) -> list[str]:
    """
    Retrieve relevant context chunks for a query.

    Args:
        session_id: Session identifier.
        query: User query to find relevant context for.
        k: Number of chunks to retrieve (default from settings).

    Returns:
        List of relevant text chunks.
    """
    if k is None:
        k = ai_settings.default_k

    logger.info(f"Getting context for session {session_id}, query: {query[:50]}...")
    collection = create_collection(session_id)

    # Check if collection is empty
    count = collection.count()
    logger.info(f"Collection {collection.name} has {count} documents")
    if count == 0:
        logger.warning(f"Collection {collection.name} is empty, no context available")
        return []

    # Embed query
    query_embedding = _embed_texts([query])[0]

    # Query collection
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(k, count),
        include=["documents"],
    )

    documents = results.get("documents", [[]])[0]
    logger.info(f"Retrieved {len(documents)} context chunks")
    return documents


def get_context_with_scores(
    session_id: str,
    query: str,
    k: Optional[int] = None,
) -> list[tuple[str, float]]:
    """
    Retrieve relevant context chunks with similarity scores.

    Args:
        session_id: Session identifier.
        query: User query to find relevant context for.
        k: Number of chunks to retrieve.

    Returns:
        List of (chunk, distance) tuples. Lower distance = more similar.
    """
    if k is None:
        k = ai_settings.default_k

    collection = create_collection(session_id)

    if collection.count() == 0:
        return []

    query_embedding = _embed_texts([query])[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(k, collection.count()),
        include=["documents", "distances"],
    )

    documents = results.get("documents", [[]])[0]
    distances = results.get("distances", [[]])[0]

    return list(zip(documents, distances))


def get_collection_stats(session_id: str) -> dict:
    """
    Get statistics about a session's collection.

    Args:
        session_id: Session identifier.

    Returns:
        Dictionary with collection stats.
    """
    collection = create_collection(session_id)

    return {
        "session_id": session_id,
        "collection_name": collection.name,
        "chunk_count": collection.count(),
    }
