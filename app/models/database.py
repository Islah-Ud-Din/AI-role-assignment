"""SQLAlchemy database models for job persistence."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Enum, Float, String, Text, Boolean
from sqlalchemy.orm import declarative_base

from app.models.schemas import JobStatus

Base = declarative_base()


class Job(Base):
    """Job model for tracking article generation tasks."""

    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, index=True)
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False)
    progress = Column(Float, default=0.0)
    current_step = Column(String(100), nullable=True)

    # Request data
    topic = Column(String(500), nullable=False)
    target_word_count = Column(Float, default=1500)
    language = Column(String(10), default="en")

    # Intermediate data (JSON serialized)
    serp_data = Column(Text, nullable=True)
    outline_data = Column(Text, nullable=True)
    draft_content = Column(Text, nullable=True)

    # Flags for resumability
    serp_collected = Column(Boolean, default=False)
    outline_generated = Column(Boolean, default=False)
    content_generated = Column(Boolean, default=False)

    # Final result (JSON serialized)
    result = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<Job(id={self.id}, status={self.status}, topic={self.topic[:30]}...)>"


