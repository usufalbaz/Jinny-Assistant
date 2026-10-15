"""
Jinny Core - Persistent Cognitive & Semantic Vector Memory
Engineered by Eng. Yousuf Albaz (AI & Systems Engineer)

Features:
- Structured long-term storage using SQLite via SQLAlchemy (async).
- Semantic search powered by Vector Embeddings (Gemini text-embedding-004).
- In-memory Cosine Similarity ranking via NumPy for zero-dependency speed.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, select

from google import genai
from config import settings

logger = logging.getLogger("Jinny.Memory")

Base = declarative_base()


class MemoryRecord(Base):
    __tablename__ = "cognitive_memory"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), index=True, default="general")
    key = Column(String(100), index=True)
    value = Column(Text, nullable=False)
    embedding = Column(Text, nullable=True)  # Serialized float vector stored as JSON array
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PersistentMemoryStore:
    def __init__(self, db_url: str = settings.DATABASE_URL):
        self.engine = create_async_engine(db_url, echo=settings.DEBUG)
        self.async_session = async_sessionmaker(self.engine, expire_on_commit=False)
        self.client: Optional[genai.Client] = None

        if settings.GEMINI_API_KEY:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    async def initialize(self):
        """Initialize database tables on application startup."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Cognitive Semantic Memory Subsystem initialized successfully.")

    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate text embedding vector using Gemini text-embedding-004."""
        if not self.client:
            return None
        try:
            result = self.client.models.embed_content(
                model="text-embedding-004",
                contents=text
            )
            # Extract vector values representation
            if hasattr(result, "embedding") and result.embedding:
                return result.embedding.values
            if hasattr(result, "embeddings") and result.embeddings:
                return result.embeddings[0].values
            return None
        except Exception as e:
            logger.warning(f"Failed to generate embedding for memory: {e}")
            return None

    @staticmethod
    def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Calculate cosine similarity metric between two float vectors."""
        a = np.array(vec_a, dtype=np.float32)
        b = np.array(vec_b, dtype=np.float32)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    async def remember(self, category: str, key: str, value: Any, confidence: float = 1.0):
        """Store memory record with calculated semantic embedding vector."""
        async with self.async_session() as session:
            serialized_val = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value

            # Compute embedding for compound key-value text
            full_text = f"{key}: {serialized_val}"
            embedding_vector = self._generate_embedding(full_text)
            embedding_json = json.dumps(embedding_vector) if embedding_vector else None

            q = select(MemoryRecord).where(MemoryRecord.category == category, MemoryRecord.key == key)
            res = await session.execute(q)
            record = res.scalar_one_or_none()

            if record:
                record.value = serialized_val
                record.embedding = embedding_json
                record.confidence = confidence
                record.updated_at = datetime.utcnow()
            else:
                record = MemoryRecord(
                    category=category,
                    key=key,
                    value=serialized_val,
                    embedding=embedding_json,
                    confidence=confidence
                )
                session.add(record)

            await session.commit()
            logger.info(f"Stored cognitive memory with semantic embedding: [{category}] {key}")

    async def recall(self, category: str, key: Optional[str] = None) -> Any:
        """Retrieve memory by exact category and key."""
        async with self.async_session() as session:
            if key:
                q = select(MemoryRecord).where(MemoryRecord.category == category, MemoryRecord.key == key)
                res = await session.execute(q)
                rec = res.scalar_one_or_none()
                if rec:
                    try:
                        return json.loads(rec.value)
                    except Exception:
                        return rec.value
                return None
            else:
                q = select(MemoryRecord).where(MemoryRecord.category == category)
                res = await session.execute(q)
                records = res.scalars().all()
                results = {}
                for r in records:
                    try:
                        results[r.key] = json.loads(r.value)
                    except Exception:
                        results[r.key] = r.value
                return results

    async def semantic_search(self, query: str, limit: int = 5, score_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        Semantic search: retrieve memories ranked by cosine similarity against query vector.
        """
        query_vector = self._generate_embedding(query)
        if not query_vector:
            # Fallback if query embedding generation fails
            return []

        async with self.async_session() as session:
            q = select(MemoryRecord).where(MemoryRecord.embedding.isnot(None))
            res = await session.execute(q)
            records = res.scalars().all()

            ranked_results = []
            for r in records:
                try:
                    record_vector = json.loads(r.embedding)
                    similarity = self._cosine_similarity(query_vector, record_vector)
                    if similarity >= score_threshold:
                        ranked_results.append({
                            "key": r.key,
                            "value": r.value,
                            "category": r.category,
                            "similarity": round(similarity, 3)
                        })
                except Exception as e:
                    logger.warning(f"Error parsing embedding for memory id {r.id}: {e}")

            # Rank results by similarity score descending
            ranked_results.sort(key=lambda x: x["similarity"], reverse=True)
            return ranked_results[:limit]

    async def get_context_snapshot(self) -> str:
        """Build active memory snapshot for LLM system context injection."""
        async with self.async_session() as session:
            q = select(MemoryRecord).order_by(MemoryRecord.updated_at.desc()).limit(15)
            res = await session.execute(q)
            records = res.scalars().all()
            if not records:
                return "No long-term memories recorded yet."
            lines = []
            for r in records:
                lines.append(f"- [{r.category.upper()}] {r.key}: {r.value}")
            return "\n".join(lines)
