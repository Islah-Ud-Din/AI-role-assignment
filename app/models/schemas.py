"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class JobStatus(str, Enum):
    """Job status enumeration."""

    PENDING = "pending"
    RESEARCHING = "researching"
    ANALYZING = "analyzing"
    OUTLINING = "outlining"
    GENERATING = "generating"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"


# ============== Input Models ==============


class ArticleRequest(BaseModel):
    """Request model for article generation."""

    topic: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="The topic or primary keyword for the article",
        examples=["best productivity tools for remote teams"],
    )
    target_word_count: int = Field(
        default=1500,
        ge=500,
        le=10000,
        description="Target word count for the article",
    )
    language: str = Field(
        default="en",
        min_length=2,
        max_length=10,
        description="Language code for the article (e.g., 'en', 'es', 'fr')",
    )

    @field_validator("topic")
    @classmethod
    def validate_topic(cls, v: str) -> str:
        """Clean and validate the topic."""
        return v.strip()


# ============== SERP Models ==============


class SERPResult(BaseModel):
    """Single search engine result."""

    rank: int = Field(..., ge=1, le=100)
    url: str
    title: str
    snippet: str
    domain: Optional[str] = None


class ThemeAnalysis(BaseModel):
    """Analysis of a common theme across SERP results."""

    theme: str
    frequency: int = Field(..., description="Number of results covering this theme")
    related_keywords: list[str] = Field(default_factory=list)
    example_headings: list[str] = Field(default_factory=list)


class SERPAnalysis(BaseModel):
    """Comprehensive analysis of SERP data."""

    query: str
    total_results: int
    results: list[SERPResult]
    common_themes: list[ThemeAnalysis] = Field(default_factory=list)
    common_questions: list[str] = Field(default_factory=list)
    avg_title_length: float = 0
    avg_content_indicators: dict[str, int] = Field(default_factory=dict)
    top_domains: list[str] = Field(default_factory=list)


# ============== Outline Models ==============


class OutlineSection(BaseModel):
    """A section in the article outline."""

    heading: str
    level: int = Field(..., ge=1, le=3, description="Heading level (1=H1, 2=H2, 3=H3)")
    key_points: list[str] = Field(default_factory=list)
    target_word_count: int = Field(default=200)
    keywords_to_include: list[str] = Field(default_factory=list)


class ArticleOutline(BaseModel):
    """Complete article outline."""

    title: str
    meta_description: str = Field(..., max_length=160)
    primary_keyword: str
    secondary_keywords: list[str] = Field(default_factory=list)
    sections: list[OutlineSection]
    estimated_word_count: int
    target_audience: str = ""
    content_angle: str = ""


# ============== Article Content Models ==============


class ArticleSection(BaseModel):
    """A section of the generated article."""

    heading: str
    level: int = Field(..., ge=1, le=3)
    content: str
    word_count: int = 0

    def model_post_init(self, __context) -> None:
        """Calculate word count after initialization."""
        if not self.word_count:
            self.word_count = len(self.content.split())


class KeywordAnalysis(BaseModel):
    """Analysis of keyword usage in the article."""

    primary_keyword: str
    primary_keyword_count: int
    primary_keyword_density: float = Field(
        ..., description="Percentage of total words"
    )
    secondary_keywords: dict[str, int] = Field(
        default_factory=dict, description="Secondary keyword counts"
    )
    lsi_keywords: list[str] = Field(
        default_factory=list, description="Latent Semantic Indexing keywords found"
    )


class LinkSuggestion(BaseModel):
    """Internal linking suggestion."""

    anchor_text: str
    suggested_target_topic: str
    context: str = Field(..., description="Where in the article this link should appear")
    relevance_score: float = Field(..., ge=0, le=1)


class ExternalReference(BaseModel):
    """External reference/citation suggestion."""

    source_name: str
    source_type: str = Field(
        ..., description="e.g., 'industry report', 'academic study', 'news article'"
    )
    url: Optional[str] = None
    citation_context: str = Field(
        ..., description="How/where to cite this in the article"
    )
    credibility_reason: str


class SEOMetadata(BaseModel):
    """SEO metadata for the article."""

    title_tag: str = Field(..., max_length=60)
    meta_description: str = Field(..., max_length=160)
    og_title: Optional[str] = None
    og_description: Optional[str] = None
    canonical_url_suggestion: Optional[str] = None
    focus_keyword: str
    secondary_keywords: list[str] = Field(default_factory=list)


class FAQItem(BaseModel):
    """A single FAQ item."""

    question: str
    answer: str


class SEOValidationResult(BaseModel):
    """Results of SEO validation."""

    is_valid: bool
    score: float = Field(..., ge=0, le=100)
    checks: dict[str, bool] = Field(default_factory=dict)
    issues: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class QualityScore(BaseModel):
    """Content quality assessment."""

    overall_score: float = Field(..., ge=0, le=100)
    readability_score: float = Field(..., ge=0, le=100)
    seo_score: float = Field(..., ge=0, le=100)
    uniqueness_indicators: dict[str, float] = Field(default_factory=dict)
    improvement_suggestions: list[str] = Field(default_factory=list)
    needs_revision: bool = False


# ============== Output Models ==============


class ArticleResponse(BaseModel):
    """Complete article response with all SEO data."""

    # Core content
    title: str
    sections: list[ArticleSection]
    full_content: str = Field(..., description="Complete article as formatted text")
    word_count: int

    # SEO Data
    seo_metadata: SEOMetadata
    keyword_analysis: KeywordAnalysis

    # Linking
    internal_links: list[LinkSuggestion] = Field(default_factory=list)
    external_references: list[ExternalReference] = Field(default_factory=list)

    # Bonus features
    faq_section: list[FAQItem] = Field(default_factory=list)
    quality_score: Optional[QualityScore] = None
    seo_validation: Optional[SEOValidationResult] = None

    # Metadata
    generation_time_seconds: float = 0
    serp_analysis_summary: Optional[dict] = None


# ============== Job Models ==============


class JobResponse(BaseModel):
    """Job status response."""

    job_id: str
    status: JobStatus
    progress: float = Field(default=0, ge=0, le=100)
    current_step: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result: Optional[ArticleResponse] = None

    # Intermediate data for resumability
    serp_data_collected: bool = False
    outline_generated: bool = False


class JobCreateResponse(BaseModel):
    """Response when creating a new job."""

    job_id: str
    status: JobStatus
    message: str


