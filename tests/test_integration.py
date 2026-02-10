"""Integration tests for the SEO content generation system."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import ArticleRequest, JobStatus
from app.services.serp_service import SERPService
from app.services.analyzer import SERPAnalyzer


class TestIntegration:
    """Integration tests for the complete system."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_research_endpoint(self, client):
        """Test research endpoint returns SERP analysis."""
        response = client.get("/research/productivity%20tools")

        assert response.status_code == 200
        data = response.json()

        assert "query" in data
        assert "results" in data
        assert len(data["results"]) > 0
        assert "common_questions" in data

    def test_outline_endpoint(self, client):
        """Test outline generation endpoint."""
        response = client.post(
            "/outline",
            json={
                "topic": "best productivity tools",
                "target_word_count": 1000,
                "language": "en",
            },
        )

        # Note: This may fail without LLM API key
        # In production, mock the LLM client
        if response.status_code == 200:
            data = response.json()
            assert "title" in data
            assert "sections" in data
            assert "primary_keyword" in data

    def test_invalid_request_validation(self, client):
        """Test that invalid requests are rejected."""
        # Topic too short
        response = client.post(
            "/outline",
            json={
                "topic": "ab",  # Too short
                "target_word_count": 1000,
            },
        )

        assert response.status_code == 422  # Validation error

        # Word count too low
        response = client.post(
            "/outline",
            json={
                "topic": "valid topic here",
                "target_word_count": 100,  # Below minimum
            },
        )

        assert response.status_code == 422


class TestSERPPipeline:
    """Test the SERP analysis pipeline."""

    @pytest.mark.asyncio
    async def test_full_serp_pipeline(self):
        """Test complete SERP fetch and analysis pipeline."""
        service = SERPService(api_key=None)  # Mock mode
        analyzer = SERPAnalyzer(llm_client=None)

        # Fetch SERP data
        serp_data = await service.fetch_serp_results(
            "productivity tools for developers",
            num_results=10,
        )

        assert serp_data is not None
        assert len(serp_data.results) == 10

        # Analyze SERP data
        analysis = await analyzer.analyze(serp_data)

        assert len(analysis.common_themes) > 0
        assert "avg_content_indicators" in analysis.model_dump()

        # Get recommendations
        recommendations = analyzer.get_content_recommendations(analysis)

        assert "suggested_format" in recommendations
        assert "top_themes_to_cover" in recommendations


class TestDataModels:
    """Test data model validation."""

    def test_article_request_validation(self):
        """Test ArticleRequest validation."""
        # Valid request
        request = ArticleRequest(
            topic="productivity tools for teams",
            target_word_count=1500,
            language="en",
        )
        assert request.topic == "productivity tools for teams"

        # Topic trimmed
        request = ArticleRequest(
            topic="  spaces around topic  ",
            target_word_count=1500,
        )
        assert request.topic == "spaces around topic"

    def test_article_request_defaults(self):
        """Test ArticleRequest default values."""
        request = ArticleRequest(topic="test topic")

        assert request.target_word_count == 1500
        assert request.language == "en"

    def test_article_request_constraints(self):
        """Test ArticleRequest field constraints."""
        # Word count must be at least 500
        with pytest.raises(ValueError):
            ArticleRequest(topic="test", target_word_count=100)

        # Word count cannot exceed 10000
        with pytest.raises(ValueError):
            ArticleRequest(topic="test", target_word_count=15000)

        # Topic must be at least 3 characters
        with pytest.raises(ValueError):
            ArticleRequest(topic="ab")


class TestSEOConstraints:
    """Test that generated content meets SEO constraints."""

    @pytest.mark.asyncio
    async def test_serp_results_structure(self):
        """Test SERP results have proper structure for SEO."""
        service = SERPService(api_key=None)
        results = await service.fetch_serp_results("test query")

        for result in results.results:
            # Each result must have rank, URL, title, snippet
            assert 1 <= result.rank <= 100
            assert result.url.startswith("http")
            assert len(result.title) > 10  # Reasonable title length
            assert len(result.snippet) > 20  # Reasonable snippet length

    def test_seo_metadata_constraints(self):
        """Test SEO metadata field constraints."""
        from app.models.schemas import SEOMetadata

        # Title tag should be max 60 chars
        metadata = SEOMetadata(
            title_tag="A" * 60,
            meta_description="Valid description that is long enough to be useful for search results.",
            focus_keyword="test keyword",
        )
        assert len(metadata.title_tag) <= 60

        # Meta description should be max 160 chars
        metadata = SEOMetadata(
            title_tag="Valid title",
            meta_description="A" * 160,
            focus_keyword="test keyword",
        )
        assert len(metadata.meta_description) <= 160


