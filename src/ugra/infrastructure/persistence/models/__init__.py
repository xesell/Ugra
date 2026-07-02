"""SQLAlchemy ORM models."""

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ugra.infrastructure.persistence.database import Base
from ugra.infrastructure.persistence.models.memory import GoalModel, MemoryModel


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_id: Mapped[int | None] = mapped_column(Integer, unique=True, nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), default="")
    email: Mapped[str] = mapped_column(String(255), default="")
    skills: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    experience_years: Mapped[int] = mapped_column(Integer, default=0)
    preferred_level: Mapped[str] = mapped_column(String(50), default="middle")
    preferred_remote: Mapped[bool] = mapped_column(Boolean, default=True)
    preferred_countries: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    english_level: Mapped[str] = mapped_column(String(10), default="B1")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class JobModel(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id: Mapped[str] = mapped_column(String(255), index=True)
    source: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(500))
    company: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    url: Mapped[str] = mapped_column(String(1000), default="")
    salary_from: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_to: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="RUB")
    is_remote: Mapped[bool] = mapped_column(Boolean, default=False)
    country: Mapped[str] = mapped_column(String(100), default="")
    technologies: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    required_skills: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    preferred_skills: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    experience_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    requires_relocation: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_english: Mapped[bool] = mapped_column(Boolean, default=False)
    match_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    pros: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    cons: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ResumeModel(Base):
    __tablename__ = "resumes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text, default="")
    skills: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class KnowledgeDocumentModel(Base):
    __tablename__ = "knowledge_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(100), index=True)
    title: Mapped[str] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(384), nullable=True)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
