"""
RAG System for EDU-MIND using ChromaDB.

Handles document ingestion and retrieval for providing context to agents.
"""

import os
from typing import Optional

import chromadb
from chromadb.config import Settings
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

# ── Configuration ────────────────────────────────────────────────────────────
CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Fast, good quality embeddings
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
DEFAULT_K = 5  # Number of chunks to retrieve


# ── Singleton instances ──────────────────────────────────────────────────────
_client: Optional[chromadb.PersistentClient] = None
_embedder: Optional[SentenceTransformer] = None


def _get_client() -> chromadb.PersistentClient:
    """Get or create ChromaDB client."""
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIR,
            settings=Settings(anonymized_telemetry=False),
        )
    return _client


def _get_embedder() -> SentenceTransformer:
    """Get or create embedding model."""
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(EMBEDDING_MODEL)
    return _embedder


def _embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts using SentenceTransformer."""
    embedder = _get_embedder()
    embeddings = embedder.encode(texts, convert_to_numpy=True)
    return embeddings.tolist()


# ── Public Functions ─────────────────────────────────────────────────────────


def create_collection(session_id: str) -> chromadb.Collection:
    """
    Create or get a ChromaDB collection for a session.

    Args:
        session_id: Unique identifier for the session.

    Returns:
        ChromaDB collection object.
    """
    client = _get_client()
    collection_name = f"session_{session_id}"

    # Get or create collection
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"session_id": session_id},
    )

    return collection


def delete_collection(session_id: str) -> bool:
    """
    Delete a session's collection.

    Args:
        session_id: Unique identifier for the session.

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
    collection = create_collection(session_id)

    # Split text into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_text(text)

    if not chunks:
        return 0

    # Prepare data for ChromaDB
    ids = [f"{source}_{i}" for i in range(len(chunks))]
    embeddings = _embed_texts(chunks)
    metadatas = [
        {
            "source": source,
            "chunk_index": i,
            **(metadata or {}),
        }
        for i in range(len(chunks))
    ]

    # Add to collection
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas,
    )

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
    # Load PDF
    loader = PyPDFLoader(pdf_path)
    pages = loader.load()

    # Combine all pages into single text
    full_text = "\n\n".join(page.page_content for page in pages)
    source = os.path.basename(pdf_path)

    return ingest_text(
        session_id=session_id,
        text=full_text,
        source=source,
        metadata=metadata,
    )


def ingest_documents(
    session_id: str,
    documents: list[str],
    source: str = "documents",
) -> int:
    """
    Ingest a list of document strings into a session's collection.

    Args:
        session_id: Session identifier.
        documents: List of document strings.
        source: Source identifier.

    Returns:
        Number of chunks created.
    """
    combined_text = "\n\n".join(documents)
    return ingest_text(session_id, combined_text, source)


def get_context(
    session_id: str,
    query: str,
    k: int = DEFAULT_K,
) -> list[str]:
    """
    Retrieve relevant context chunks for a query.

    Args:
        session_id: Session identifier.
        query: User query to find relevant context for.
        k: Number of chunks to retrieve.

    Returns:
        List of relevant text chunks.
    """
    collection = create_collection(session_id)

    # Check if collection is empty
    if collection.count() == 0:
        return []

    # Embed query
    query_embedding = _embed_texts([query])[0]

    # Query collection
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(k, collection.count()),
        include=["documents"],
    )

    # Extract documents
    documents = results.get("documents", [[]])[0]
    return documents


def get_context_with_scores(
    session_id: str,
    query: str,
    k: int = DEFAULT_K,
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
