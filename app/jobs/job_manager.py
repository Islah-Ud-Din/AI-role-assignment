"""Job Management System.

Handles job persistence, status tracking, and resumability for article generation.
"""

import json
import uuid
from datetime import datetime
from typing import Optional

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Job
from app.models.schemas import (
    ArticleRequest,
    ArticleResponse,
    ArticleOutline,
    SERPAnalysis,
    JobStatus,
    JobResponse,
)

logger = structlog.get_logger()


class JobManager:
    """Manages article generation jobs with persistence."""

    def __init__(self, session: AsyncSession):
        """Initialize job manager with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def create_job(self, request: ArticleRequest) -> str:
        """Create a new job for article generation.

        Args:
            request: Article generation request

        Returns:
            Job ID
        """
        job_id = str(uuid.uuid4())

        job = Job(
            id=job_id,
            status=JobStatus.PENDING,
            progress=0.0,
            current_step="Job created",
            topic=request.topic,
            target_word_count=request.target_word_count,
            language=request.language,
        )

        self.session.add(job)
        await self.session.commit()

        logger.info("Job created", job_id=job_id, topic=request.topic)
        return job_id

    async def get_job(self, job_id: str) -> Optional[JobResponse]:
        """Get job status and details.

        Args:
            job_id: Job ID to retrieve

        Returns:
            JobResponse or None if not found
        """
        result = await self.session.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()

        if not job:
            return None

        # Parse result JSON if available
        article_result = None
        if job.result:
            try:
                result_data = json.loads(job.result)
                article_result = ArticleResponse(**result_data)
            except Exception as e:
                logger.error("Failed to parse job result", error=str(e))

        return JobResponse(
            job_id=job.id,
            status=job.status,
            progress=job.progress,
            current_step=job.current_step,
            created_at=job.created_at,
            updated_at=job.updated_at,
            completed_at=job.completed_at,
            error_message=job.error_message,
            result=article_result,
            serp_data_collected=job.serp_collected,
            outline_generated=job.outline_generated,
        )

    async def update_progress(
        self,
        job_id: str,
        status: JobStatus,
        progress: float,
        current_step: str,
    ) -> None:
        """Update job progress.

        Args:
            job_id: Job ID
            status: New status
            progress: Progress percentage (0-100)
            current_step: Description of current step
        """
        result = await self.session.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()

        if job:
            job.status = status
            job.progress = progress
            job.current_step = current_step
            job.updated_at = datetime.utcnow()

            if status == JobStatus.COMPLETED:
                job.completed_at = datetime.utcnow()

            await self.session.commit()
            logger.debug("Job progress updated", job_id=job_id, progress=progress)

    async def save_serp_data(
        self, job_id: str, serp_analysis: SERPAnalysis
    ) -> None:
        """Save SERP analysis data for resumability.

        Args:
            job_id: Job ID
            serp_analysis: SERP analysis to save
        """
        result = await self.session.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()

        if job:
            job.serp_data = serp_analysis.model_dump_json()
            job.serp_collected = True
            job.updated_at = datetime.utcnow()
            await self.session.commit()
            logger.info("SERP data saved", job_id=job_id)

    async def save_outline(self, job_id: str, outline: ArticleOutline) -> None:
        """Save generated outline for resumability.

        Args:
            job_id: Job ID
            outline: Outline to save
        """
        result = await self.session.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()

        if job:
            job.outline_data = outline.model_dump_json()
            job.outline_generated = True
            job.updated_at = datetime.utcnow()
            await self.session.commit()
            logger.info("Outline saved", job_id=job_id)

    async def save_result(
        self, job_id: str, article: ArticleResponse
    ) -> None:
        """Save the final article result.

        Args:
            job_id: Job ID
            article: Generated article
        """
        result = await self.session.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()

        if job:
            job.result = article.model_dump_json()
            job.content_generated = True
            job.status = JobStatus.COMPLETED
            job.progress = 100.0
            job.current_step = "Complete"
            job.completed_at = datetime.utcnow()
            job.updated_at = datetime.utcnow()
            await self.session.commit()
            logger.info("Job result saved", job_id=job_id)

    async def mark_failed(self, job_id: str, error_message: str) -> None:
        """Mark a job as failed.

        Args:
            job_id: Job ID
            error_message: Error description
        """
        result = await self.session.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()

        if job:
            job.status = JobStatus.FAILED
            job.error_message = error_message
            job.updated_at = datetime.utcnow()
            await self.session.commit()
            logger.error("Job marked as failed", job_id=job_id, error=error_message)

    async def get_resumable_data(
        self, job_id: str
    ) -> tuple[Optional[SERPAnalysis], Optional[ArticleOutline]]:
        """Get saved intermediate data for job resumption.

        Args:
            job_id: Job ID

        Returns:
            Tuple of (SERP analysis, outline) - either can be None
        """
        result = await self.session.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()

        if not job:
            return None, None

        serp_analysis = None
        outline = None

        if job.serp_data:
            try:
                serp_analysis = SERPAnalysis.model_validate_json(job.serp_data)
            except Exception as e:
                logger.error("Failed to parse SERP data", error=str(e))

        if job.outline_data:
            try:
                outline = ArticleOutline.model_validate_json(job.outline_data)
            except Exception as e:
                logger.error("Failed to parse outline", error=str(e))

        return serp_analysis, outline

    async def list_jobs(
        self,
        status: Optional[JobStatus] = None,
        limit: int = 50,
    ) -> list[JobResponse]:
        """List jobs, optionally filtered by status.

        Args:
            status: Optional status filter
            limit: Maximum number of jobs to return

        Returns:
            List of job responses
        """
        query = select(Job).order_by(Job.created_at.desc()).limit(limit)

        if status:
            query = query.where(Job.status == status)

        result = await self.session.execute(query)
        jobs = result.scalars().all()

        return [
            JobResponse(
                job_id=job.id,
                status=job.status,
                progress=job.progress,
                current_step=job.current_step,
                created_at=job.created_at,
                updated_at=job.updated_at,
                completed_at=job.completed_at,
                error_message=job.error_message,
                serp_data_collected=job.serp_collected,
                outline_generated=job.outline_generated,
            )
            for job in jobs
        ]


