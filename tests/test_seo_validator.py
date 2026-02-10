"""Tests for SEO Validator."""

import pytest
from app.services.seo_validator import SEOValidator
from app.models.schemas import (
    ArticleResponse,
    ArticleSection,
    SEOMetadata,
    KeywordAnalysis,
    LinkSuggestion,
    ExternalReference,
)


class TestSEOValidator:
    """Test SEO validation functionality."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return SEOValidator()

    @pytest.fixture
    def valid_article(self):
        """Create a valid article for testing."""
        return ArticleResponse(
            title="The Complete Guide to Productivity Tools for Remote Teams in 2025",
            sections=[
                ArticleSection(
                    heading="Introduction to Productivity Tools",
                    level=2,
                    content="In today's remote work environment, productivity tools have become essential for teams. The right productivity tools can transform how remote teams collaborate and achieve their goals. This guide explores the best options available." * 5,
                ),
                ArticleSection(
                    heading="Top Productivity Tools for Communication",
                    level=2,
                    content="Effective communication is the foundation of remote team success. These productivity tools excel at keeping teams connected across different time zones and locations." * 5,
                ),
                ArticleSection(
                    heading="Project Management Solutions",
                    level=2,
                    content="Managing projects remotely requires robust productivity tools that provide visibility and accountability. Here are the top choices for remote teams." * 5,
                ),
            ],
            full_content="This is the complete article content with productivity tools mentioned throughout. " * 50,
            word_count=1500,
            seo_metadata=SEOMetadata(
                title_tag="Best Productivity Tools for Remote Teams | 2025 Guide",
                meta_description="Discover the best productivity tools for remote teams. Our comprehensive guide covers top tools for communication, project management, and collaboration.",
                focus_keyword="productivity tools",
                secondary_keywords=["remote teams", "collaboration tools"],
            ),
            keyword_analysis=KeywordAnalysis(
                primary_keyword="productivity tools",
                primary_keyword_count=25,
                primary_keyword_density=1.67,
                secondary_keywords={"remote teams": 10, "collaboration": 8},
                lsi_keywords=["software", "communication", "project"],
            ),
            internal_links=[
                LinkSuggestion(
                    anchor_text="project management guide",
                    suggested_target_topic="project management",
                    context="When discussing project tools",
                    relevance_score=0.8,
                ),
                LinkSuggestion(
                    anchor_text="communication strategies",
                    suggested_target_topic="remote communication",
                    context="In communication section",
                    relevance_score=0.9,
                ),
                LinkSuggestion(
                    anchor_text="team collaboration tips",
                    suggested_target_topic="collaboration",
                    context="Throughout the article",
                    relevance_score=0.7,
                ),
            ],
            external_references=[
                ExternalReference(
                    source_name="Gartner Research",
                    source_type="industry report",
                    citation_context="When citing productivity statistics",
                    credibility_reason="Leading technology research firm",
                ),
                ExternalReference(
                    source_name="Harvard Business Review",
                    source_type="academic publication",
                    citation_context="For remote work best practices",
                    credibility_reason="Respected business publication",
                ),
            ],
        )

    def test_valid_article_passes(self, validator, valid_article):
        """Test that a well-formed article passes validation."""
        result = validator.validate(valid_article)

        assert result.is_valid is True
        assert result.score >= 70

    def test_word_count_validation(self, validator, valid_article):
        """Test word count validation."""
        # Too few words
        valid_article.word_count = 200
        result = validator.validate(valid_article)

        assert result.checks["word_count_adequate"] is False
        assert any("word count" in issue.lower() for issue in result.issues)

    def test_title_length_validation(self, validator, valid_article):
        """Test title tag length validation."""
        # Title too short
        valid_article.seo_metadata.title_tag = "Tools"
        result = validator.validate(valid_article)

        assert result.checks["title_tag_optimized"] is False

        # Title too long
        valid_article.seo_metadata.title_tag = "A" * 80
        result = validator.validate(valid_article)

        assert result.checks["title_tag_optimized"] is False

    def test_keyword_in_title_validation(self, validator, valid_article):
        """Test that keyword must be in title."""
        valid_article.seo_metadata.title_tag = "A Guide to Remote Work Software"
        result = validator.validate(valid_article)

        assert result.checks["title_tag_optimized"] is False
        assert any("keyword" in issue.lower() and "title" in issue.lower() for issue in result.issues)

    def test_meta_description_validation(self, validator, valid_article):
        """Test meta description validation."""
        # Too short
        valid_article.seo_metadata.meta_description = "Short description."
        result = validator.validate(valid_article)

        assert result.checks["meta_description_optimized"] is False

        # Too long
        valid_article.seo_metadata.meta_description = "A" * 200
        result = validator.validate(valid_article)

        assert result.checks["meta_description_optimized"] is False

    def test_keyword_density_validation(self, validator, valid_article):
        """Test keyword density validation."""
        # Too low
        valid_article.keyword_analysis.primary_keyword_density = 0.2
        result = validator.validate(valid_article)

        assert result.checks["keyword_density_optimal"] is False

        # Too high (keyword stuffing)
        valid_article.keyword_analysis.primary_keyword_density = 5.0
        result = validator.validate(valid_article)

        assert result.checks["keyword_density_optimal"] is False

    def test_heading_structure_validation(self, validator, valid_article):
        """Test heading structure validation."""
        # Remove H2 sections
        valid_article.sections = [
            ArticleSection(heading="Only Section", level=3, content="Content")
        ]
        result = validator.validate(valid_article)

        assert result.checks["heading_structure_valid"] is False

    def test_internal_links_validation(self, validator, valid_article):
        """Test internal links validation."""
        valid_article.internal_links = []
        result = validator.validate(valid_article)

        assert result.checks["internal_links_present"] is False

    def test_external_refs_validation(self, validator, valid_article):
        """Test external references validation."""
        valid_article.external_references = []
        result = validator.validate(valid_article)

        assert result.checks["external_refs_present"] is False

    def test_validation_returns_suggestions(self, validator, valid_article):
        """Test that validation returns helpful suggestions."""
        # Make article fail several checks
        valid_article.word_count = 200
        valid_article.internal_links = []

        result = validator.validate(valid_article)

        assert len(result.suggestions) > 0
        assert all(isinstance(s, str) for s in result.suggestions)


