"""Pytest configuration and fixtures."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.models.database import Base


@pytest_asyncio.fixture
async def async_session():
    """Create an in-memory database session for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def sample_article_request():
    """Sample article request for testing."""
    from app.models.schemas import ArticleRequest

    return ArticleRequest(
        topic="best productivity tools for remote teams",
        target_word_count=1500,
        language="en",
    )


@pytest.fixture
def sample_serp_results():
    """Sample SERP results for testing."""
    from app.models.schemas import SERPResult, SERPAnalysis

    results = [
        SERPResult(
            rank=1,
            url="https://example1.com/productivity-tools",
            title="15 Best Productivity Tools for Remote Teams in 2025",
            snippet="Discover the top productivity tools that help remote teams collaborate effectively...",
            domain="example1.com",
        ),
        SERPResult(
            rank=2,
            url="https://example2.com/remote-work-tools",
            title="The Ultimate Guide to Remote Work Productivity Tools",
            snippet="Our comprehensive guide covers the best tools for communication, project management...",
            domain="example2.com",
        ),
        SERPResult(
            rank=3,
            url="https://example3.com/team-collaboration",
            title="How to Choose Productivity Tools for Your Remote Team",
            snippet="Learn the key factors to consider when selecting productivity software...",
            domain="example3.com",
        ),
    ]

    return SERPAnalysis(
        query="best productivity tools for remote teams",
        total_results=3,
        results=results,
        common_questions=[
            "What are the best productivity tools for remote work?",
            "How do I improve my remote team's productivity?",
        ],
        top_domains=["example1.com", "example2.com", "example3.com"],
    )


