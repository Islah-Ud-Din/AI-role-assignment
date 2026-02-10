"""Tests for SERP Analyzer."""

import pytest
from app.services.analyzer import SERPAnalyzer
from app.models.schemas import SERPResult, SERPAnalysis


class TestSERPAnalyzer:
    """Test SERP analysis functionality."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer without LLM client for testing."""
        return SERPAnalyzer(llm_client=None)

    @pytest.fixture
    def sample_serp_data(self):
        """Create sample SERP data for testing."""
        return SERPAnalysis(
            query="productivity tools",
            total_results=5,
            results=[
                SERPResult(
                    rank=1,
                    url="https://example.com/tools",
                    title="10 Best Productivity Tools for Teams in 2025",
                    snippet="Discover the top productivity tools that boost efficiency...",
                    domain="example.com",
                ),
                SERPResult(
                    rank=2,
                    url="https://blog.com/productivity",
                    title="How to Improve Team Productivity with the Right Tools",
                    snippet="Learn how productivity tools can transform your workflow...",
                    domain="blog.com",
                ),
                SERPResult(
                    rank=3,
                    url="https://reviews.com/tools",
                    title="Productivity Tools Compared: Which is Best?",
                    snippet="We compare the top productivity tools to help you choose...",
                    domain="reviews.com",
                ),
            ],
            common_questions=[],
        )

    @pytest.mark.asyncio
    async def test_analyze_extracts_themes(self, analyzer, sample_serp_data):
        """Test that analyzer extracts themes from results."""
        analysis = await analyzer.analyze(sample_serp_data)

        assert len(analysis.common_themes) > 0
        theme_names = [t.theme for t in analysis.common_themes]

        # "productivity" and "tools" should be common themes
        assert any("productiv" in t for t in theme_names)
        assert any("tool" in t for t in theme_names)

    @pytest.mark.asyncio
    async def test_analyze_calculates_content_patterns(self, analyzer, sample_serp_data):
        """Test that analyzer detects content patterns."""
        analysis = await analyzer.analyze(sample_serp_data)

        assert "listicles" in analysis.avg_content_indicators
        assert "how_to" in analysis.avg_content_indicators
        assert "comparison" in analysis.avg_content_indicators

        # First result is a listicle (10 Best...)
        assert analysis.avg_content_indicators["listicles"] >= 1

    @pytest.mark.asyncio
    async def test_analyze_detects_year_in_titles(self, analyzer, sample_serp_data):
        """Test that analyzer detects year-specific content."""
        analysis = await analyzer.analyze(sample_serp_data)

        # First result contains "2025"
        assert analysis.avg_content_indicators["year_specific"] >= 1

    def test_get_content_recommendations(self, analyzer, sample_serp_data):
        """Test content recommendations based on analysis."""
        # Manually add some themes for testing
        sample_serp_data.avg_content_indicators = {
            "listicles": 5,
            "how_to": 2,
            "comparison": 1,
            "year_specific": 3,
        }

        recommendations = analyzer.get_content_recommendations(sample_serp_data)

        assert "suggested_format" in recommendations
        assert "include_list_format" in recommendations
        assert recommendations["suggested_format"] == "listicle"  # Most common
        assert recommendations["include_list_format"] is True

    @pytest.mark.asyncio
    async def test_theme_frequency_tracking(self, analyzer, sample_serp_data):
        """Test that theme frequencies are tracked correctly."""
        analysis = await analyzer.analyze(sample_serp_data)

        for theme in analysis.common_themes:
            assert theme.frequency >= 1
            assert isinstance(theme.related_keywords, list)
            assert isinstance(theme.example_headings, list)


