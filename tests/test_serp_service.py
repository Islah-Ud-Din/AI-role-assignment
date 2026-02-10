"""Tests for SERP Service."""

import pytest
from app.services.serp_service import SERPService


class TestSERPService:
    """Test SERP data fetching and mocking."""

    @pytest.mark.asyncio
    async def test_mock_serp_results_returned(self):
        """Test that mock results are returned when no API key is provided."""
        service = SERPService(api_key=None)  # Force mock mode

        results = await service.fetch_serp_results(
            "productivity tools", num_results=10
        )

        assert results is not None
        assert results.query == "productivity tools"
        assert len(results.results) == 10
        assert results.total_results == 10

    @pytest.mark.asyncio
    async def test_mock_results_have_required_fields(self):
        """Test that mock results have all required SERP fields."""
        service = SERPService(api_key=None)

        results = await service.fetch_serp_results("test query", num_results=5)

        for result in results.results:
            assert result.rank >= 1
            assert result.url.startswith("https://")
            assert len(result.title) > 0
            assert len(result.snippet) > 0
            assert result.domain is not None

    @pytest.mark.asyncio
    async def test_mock_results_deterministic(self):
        """Test that same query produces same mock results."""
        service = SERPService(api_key=None)

        results1 = await service.fetch_serp_results("specific query")
        results2 = await service.fetch_serp_results("specific query")

        assert results1.results[0].title == results2.results[0].title
        assert results1.results[0].url == results2.results[0].url

    @pytest.mark.asyncio
    async def test_mock_results_include_questions(self):
        """Test that mock results include common questions."""
        service = SERPService(api_key=None)

        results = await service.fetch_serp_results("best tools for teams")

        assert len(results.common_questions) > 0
        assert all("?" in q for q in results.common_questions)

    @pytest.mark.asyncio
    async def test_mock_different_queries_different_results(self):
        """Test that different queries produce different results."""
        service = SERPService(api_key=None)

        results1 = await service.fetch_serp_results("productivity tools")
        results2 = await service.fetch_serp_results("cooking recipes")

        # Different queries should have different URLs
        assert results1.results[0].url != results2.results[0].url


