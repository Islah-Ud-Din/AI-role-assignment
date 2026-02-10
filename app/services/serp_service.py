"""SERP (Search Engine Results Page) data service.

Supports both real API calls (SerpAPI) and realistic mock data.
"""

import hashlib
import random
from typing import Optional

import httpx
import structlog

from app.config import get_settings
from app.models.schemas import SERPResult, SERPAnalysis

logger = structlog.get_logger()


class SERPService:
    """Service for fetching and managing SERP data."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize SERP service."""
        settings = get_settings()
        self.api_key = api_key or settings.serpapi_key
        self.use_mock = not self.api_key

    async def fetch_serp_results(
        self, query: str, num_results: int = 10
    ) -> SERPAnalysis:
        """Fetch SERP results for a query.

        Args:
            query: Search query/topic
            num_results: Number of results to fetch (default 10)

        Returns:
            SERPAnalysis with results and basic metrics
        """
        if self.use_mock:
            logger.info("Using mock SERP data", query=query)
            return await self._generate_mock_results(query, num_results)

        return await self._fetch_real_results(query, num_results)

    async def _fetch_real_results(
        self, query: str, num_results: int
    ) -> SERPAnalysis:
        """Fetch real results from SerpAPI."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://serpapi.com/search",
                    params={
                        "q": query,
                        "api_key": self.api_key,
                        "num": num_results,
                        "engine": "google",
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()

            results = []
            for idx, item in enumerate(data.get("organic_results", [])[:num_results]):
                results.append(
                    SERPResult(
                        rank=idx + 1,
                        url=item.get("link", ""),
                        title=item.get("title", ""),
                        snippet=item.get("snippet", ""),
                        domain=self._extract_domain(item.get("link", "")),
                    )
                )

            # Extract common questions from "People Also Ask"
            questions = [
                q.get("question", "")
                for q in data.get("related_questions", [])
            ]

            return SERPAnalysis(
                query=query,
                total_results=len(results),
                results=results,
                common_questions=questions,
                avg_title_length=sum(len(r.title) for r in results) / len(results) if results else 0,
                top_domains=list(set(r.domain for r in results if r.domain))[:5],
            )

        except httpx.HTTPError as e:
            logger.error("SerpAPI request failed", error=str(e))
            # Fallback to mock data on API failure
            logger.info("Falling back to mock data")
            return await self._generate_mock_results(query, num_results)

    async def _generate_mock_results(
        self, query: str, num_results: int
    ) -> SERPAnalysis:
        """Generate realistic mock SERP data based on query."""
        # Use query hash for deterministic but varied results
        query_hash = int(hashlib.md5(query.encode()).hexdigest()[:8], 16)
        random.seed(query_hash)

        # Generate realistic domains and content
        domains = [
            "forbes.com", "hubspot.com", "techcrunch.com", "medium.com",
            "entrepreneur.com", "inc.com", "businessinsider.com", "wired.com",
            "zdnet.com", "cnet.com", "pcmag.com", "techradar.com",
            "nytimes.com", "theguardian.com", "bbc.com"
        ]

        # Topic-specific title templates
        title_templates = [
            f"The Ultimate Guide to {query.title()} in 2025",
            f"15 Best {query.title()} [Updated 2025]",
            f"How to Choose the Right {query.title()} for Your Business",
            f"{query.title()}: Everything You Need to Know",
            f"Top 10 {query.title()} Compared & Reviewed",
            f"Why {query.title()} Matters More Than Ever",
            f"A Complete Breakdown of {query.title()}",
            f"Expert Tips for {query.title()} Success",
            f"The Definitive {query.title()} Handbook",
            f"{query.title()}: Trends and Best Practices",
            f"What Makes Great {query.title()}? An In-Depth Analysis",
            f"Mastering {query.title()}: A Step-by-Step Guide",
        ]

        snippet_templates = [
            f"Discover the best strategies for {query}. Our comprehensive guide covers everything from basics to advanced techniques...",
            f"Looking for {query}? We've tested and reviewed the top options to help you make an informed decision...",
            f"Learn how industry leaders are leveraging {query} to drive results. This guide breaks down the key factors...",
            f"In this article, we explore {query} and provide actionable insights you can implement today...",
            f"Our experts have analyzed {query} trends to bring you the most up-to-date recommendations...",
            f"Whether you're new to {query} or looking to optimize, this resource has everything you need...",
            f"Get the complete picture on {query} with real-world examples and expert analysis...",
            f"This comprehensive resource on {query} will help you understand the landscape and make better choices...",
        ]

        # Common questions based on query
        common_questions = [
            f"What is the best {query}?",
            f"How do I choose {query}?",
            f"What are the benefits of {query}?",
            f"How much does {query} cost?",
            f"Is {query} worth it?",
            f"What are the top {query} in 2025?",
            f"How do {query} compare?",
            f"What should I look for in {query}?",
        ]

        random.shuffle(domains)
        random.shuffle(title_templates)
        random.shuffle(snippet_templates)
        random.shuffle(common_questions)

        results = []
        for i in range(min(num_results, len(title_templates))):
            domain = domains[i % len(domains)]
            slug = query.lower().replace(" ", "-")[:30]
            results.append(
                SERPResult(
                    rank=i + 1,
                    url=f"https://{domain}/{slug}-guide-{2025 - (i % 2)}",
                    title=title_templates[i],
                    snippet=snippet_templates[i % len(snippet_templates)],
                    domain=domain,
                )
            )

        return SERPAnalysis(
            query=query,
            total_results=num_results,
            results=results,
            common_questions=common_questions[:6],
            avg_title_length=sum(len(r.title) for r in results) / len(results),
            top_domains=[r.domain for r in results[:5] if r.domain],
        )

    @staticmethod
    def _extract_domain(url: str) -> Optional[str]:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc.replace("www.", "")
        except Exception:
            return None


