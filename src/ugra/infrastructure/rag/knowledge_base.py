"""RAG knowledge base with pgvector."""

from dataclasses import dataclass
from uuid import UUID, uuid4

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ugra.core.logging.setup import get_logger

logger = get_logger(__name__)


@dataclass
class KnowledgeChunk:
    id: UUID
    source: str
    title: str
    content: str
    score: float = 0.0


class EmbeddingService:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self._model_name = model_name
        self._model = None

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self._model_name)
        return self._model

    def embed(self, text: str) -> list[float]:
        model = self._load_model()
        return model.encode(text).tolist()


class KnowledgeBase:
    def __init__(self, session: AsyncSession, embedding_service: EmbeddingService):
        self._session = session
        self._embeddings = embedding_service

    async def add_document(self, source: str, title: str, content: str) -> UUID:
        from ugra.infrastructure.persistence.models import KnowledgeDocumentModel

        doc_id = uuid4()
        embedding = self._embeddings.embed(f"{title}\n{content}")

        doc = KnowledgeDocumentModel(
            id=doc_id,
            source=source,
            title=title,
            content=content,
            embedding=embedding,
        )
        self._session.add(doc)
        await self._session.flush()
        logger.info("knowledge_document_added", source=source, title=title)
        return doc_id

    async def search(self, query: str, limit: int = 5, source: str | None = None) -> list[KnowledgeChunk]:
        from ugra.infrastructure.persistence.models import KnowledgeDocumentModel

        query_embedding = self._embeddings.embed(query)
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        sql = f"""
            SELECT id, source, title, content,
                   1 - (embedding <=> '{embedding_str}'::vector) AS score
            FROM knowledge_documents
            {"WHERE source = :source" if source else ""}
            ORDER BY embedding <=> '{embedding_str}'::vector
            LIMIT :limit
        """
        params: dict = {"limit": limit}
        if source:
            params["source"] = source

        result = await self._session.execute(text(sql), params)
        rows = result.fetchall()

        return [
            KnowledgeChunk(
                id=row.id,
                source=row.source,
                title=row.title,
                content=row.content,
                score=float(row.score),
            )
            for row in rows
        ]

    async def ingest_sources(self, documents: list[tuple[str, str, str]]) -> int:
        count = 0
        for source, title, content in documents:
            await self.add_document(source, title, content)
            count += 1
        return count
