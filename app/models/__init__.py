"""Data models package."""

from app.models.schemas import (
    ArticleRequest,
    ArticleResponse,
    KeywordAnalysis,
    LinkSuggestion,
    ExternalReference,
    SEOMetadata,
    ArticleSection,
    SERPResult,
    SERPAnalysis,
    ArticleOutline,
    JobStatus,
    JobResponse,
)
from app.models.database import Job, Base

__all__ = [
    "ArticleRequest",
    "ArticleResponse",
    "KeywordAnalysis",
    "LinkSuggestion",
    "ExternalReference",
    "SEOMetadata",
    "ArticleSection",
    "SERPResult",
    "SERPAnalysis",
    "ArticleOutline",
    "JobStatus",
    "JobResponse",
    "Job",
    "Base",
]


