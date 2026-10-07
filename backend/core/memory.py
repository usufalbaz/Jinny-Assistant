"""
Jinny Core - Persistent Cognitive Memory & Context Management
Engineered by Yousuf Albaz
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from config import settings

logger = logging.getLogger("Jinny.Memory")

Base = declarative_base()

class MemoryRecord(Base):
    __tablename__ = "cognitive_memory"
    
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), index=True)
    key = Column(String(100), index=True)
    value = Column(Text, nullable=False)
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PersistentMemoryStore:
    def __init__(self, db_url: str = settings.DATABASE_URL):
        self.engine = create_async_engine(db_url, echo=settings.DEBUG)
        self.async_session = async_sessionmaker(
            self.engine, expire_on_commit=False
        )

    async def initialize(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Cognitive Memory Subsystem initialized successfully.")

    async def remember(self, category: str, key: str, value: Any, confidence: float = 1.0):
        async with self.async_session() as session:
            serialized_val = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
            
            from sqlalchemy import select
            q = select(MemoryRecord).where(MemoryRecord.category == category, MemoryRecord.key == key)
            res = await session.execute(q)
            record = res.scalar_one_or_none()
            
            if record:
                record.value = serialized_val
                record.confidence = confidence
                record.updated_at = datetime.utcnow()
            else:
                record = MemoryRecord(
                    category=category,
                    key=key,
                    value=serialized_val,
                    confidence=confidence
                )
                session.add(record)
            
            await session.commit()
            logger.debug(f"Stored memory: [{category}] {key}")

    async def recall(self, category: str, key: Optional[str] = None) -> Any:
        async with self.async_session() as session:
            from sqlalchemy import select
            if key:
                q = select(MemoryRecord).where(MemoryRecord.category == category, MemoryRecord.key == key)
                res = await session.execute(q)
                rec = res.scalar_one_or_none()
                if rec:
                    try:
                        return json.loads(rec.value)
                    except:
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
                    except:
                        results[r.key] = r.value
                return results

    async def get_context_snapshot(self) -> str:
        async with self.async_session() as session:
            from sqlalchemy import select
            q = select(MemoryRecord).order_by(MemoryRecord.updated_at.desc()).limit(20)
            res = await session.execute(q)
            records = res.scalars().all()
            lines = []
            for r in records:
                lines.append(f"- [{r.category.upper()}] {r.key}: {r.value}")
            return "\n".join(lines)
