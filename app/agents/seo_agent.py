"""SEO Content Generation Agent.

Main orchestrator that coordinates all services to generate
SEO-optimized articles from topics.
"""

import time
from typing import Optional, Callable, Awaitable

import structlog

from app.models.schemas import (
    ArticleRequest,
    ArticleResponse,
    ArticleOutline,
    SERPAnalysis,
    JobStatus,
)
from app.services.serp_service import SERPService
from app.services.analyzer import SERPAnalyzer
from app.services.outline_generator import OutlineGenerator
from app.services.content_generator import ContentGenerator
from app.services.seo_validator import SEOValidator
from app.services.quality_scorer import QualityScorer
from app.services.llm_client import LLMClient

logger = structlog.get_logger()

# Type for progress callback
ProgressCallback = Callable[[JobStatus, float, str], Awaitable[None]]


class SEOAgent:
    """Agent that orchestrates SEO content generation."""

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        serp_service: Optional[SERPService] = None,
    ):
        """Initialize the SEO Agent with required services.

        Args:
            llm_client: LLM client for content generation
            serp_service: SERP data service
        """
        self.llm_client = llm_client or LLMClient()
        self.serp_service = serp_service or SERPService()

        # Initialize dependent services
        self.analyzer = SERPAnalyzer(self.llm_client)
        self.outline_generator = OutlineGenerator(self.llm_client)
        self.content_generator = ContentGenerator(self.llm_client)
        self.seo_validator = SEOValidator()
        self.quality_scorer = QualityScorer(self.llm_client)

    async def generate_article(
        self,
        request: ArticleRequest,
        progress_callback: Optional[ProgressCallback] = None,
        # Resume parameters
        existing_serp_data: Optional[SERPAnalysis] = None,
        existing_outline: Optional[ArticleOutline] = None,
    ) -> ArticleResponse:
        """Generate a complete SEO-optimized article.

        This is the main entry point for article generation. It orchestrates
        all steps from SERP research to final content validation.

        Args:
            request: Article generation request
            progress_callback: Optional callback for progress updates
            existing_serp_data: Pre-collected SERP data (for resume)
            existing_outline: Pre-generated outline (for resume)

        Returns:
            Complete ArticleResponse with content and metadata
        """
        start_time = time.time()

        logger.info(
            "Starting article generation",
            topic=request.topic,
            target_words=request.target_word_count,
        )

        async def update_progress(
            status: JobStatus, progress: float, step: str
        ) -> None:
            """Update progress through callback if provided."""
            if progress_callback:
                await progress_callback(status, progress, step)
            logger.info("Progress update", status=status, progress=progress, step=step)

        try:
            # Step 1: Research (SERP data collection)
            if existing_serp_data:
                logger.info("Using existing SERP data")
                serp_analysis = existing_serp_data
            else:
                await update_progress(JobStatus.RESEARCHING, 10, "Fetching search results")
                serp_data = await self.serp_service.fetch_serp_results(
                    request.topic, num_results=10
                )
                await update_progress(JobStatus.ANALYZING, 20, "Analyzing competitive landscape")
                serp_analysis = await self.analyzer.analyze(serp_data)

            # Step 2: Outline Generation
            if existing_outline:
                logger.info("Using existing outline")
                outline = existing_outline
            else:
                await update_progress(JobStatus.OUTLINING, 35, "Creating article outline")
                outline = await self.outline_generator.generate(request, serp_analysis)

            # Step 3: Content Generation
            await update_progress(JobStatus.GENERATING, 50, "Generating article content")
            article = await self.content_generator.generate(outline, serp_analysis)

            # Step 4: SEO Validation
            await update_progress(JobStatus.VALIDATING, 80, "Validating SEO criteria")
            validation_result = self.seo_validator.validate(article)
            article.seo_validation = validation_result

            # Step 5: Quality Scoring
            await update_progress(JobStatus.VALIDATING, 90, "Scoring content quality")
            quality_score = await self.quality_scorer.score(article)
            article.quality_score = quality_score

            # Step 6: Revision if needed (optional enhancement)
            if quality_score.needs_revision:
                logger.warning(
                    "Article quality below threshold",
                    score=quality_score.overall_score,
                )
                # In a full implementation, we could trigger revisions here

            # Calculate generation time
            article.generation_time_seconds = round(time.time() - start_time, 2)

            await update_progress(JobStatus.COMPLETED, 100, "Article generation complete")

            logger.info(
                "Article generation complete",
                word_count=article.word_count,
                quality_score=quality_score.overall_score,
                seo_valid=validation_result.is_valid,
                time_seconds=article.generation_time_seconds,
            )

            return article

        except Exception as e:
            logger.error("Article generation failed", error=str(e), exc_info=True)
            if progress_callback:
                await progress_callback(JobStatus.FAILED, 0, f"Error: {str(e)}")
            raise

    async def research_topic(self, topic: str) -> SERPAnalysis:
        """Perform only the research phase.

        Useful for preview or when you want to separate research from generation.

        Args:
            topic: Topic to research

        Returns:
            Analyzed SERP data
        """
        logger.info("Researching topic", topic=topic)

        serp_data = await self.serp_service.fetch_serp_results(topic, num_results=10)
        analysis = await self.analyzer.analyze(serp_data)

        return analysis

    async def generate_outline_only(
        self,
        request: ArticleRequest,
        serp_analysis: Optional[SERPAnalysis] = None,
    ) -> ArticleOutline:
        """Generate only the article outline.

        Args:
            request: Article request
            serp_analysis: Optional pre-fetched SERP analysis

        Returns:
            Article outline
        """
        if not serp_analysis:
            serp_analysis = await self.research_topic(request.topic)

        return await self.outline_generator.generate(request, serp_analysis)

    def get_content_recommendations(self, serp_analysis: SERPAnalysis) -> dict:
        """Get content recommendations based on SERP analysis.

        Args:
            serp_analysis: Analyzed SERP data

        Returns:
            Dictionary of content recommendations
        """
        return self.analyzer.get_content_recommendations(serp_analysis)


