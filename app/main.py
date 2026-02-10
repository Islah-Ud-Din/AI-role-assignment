"""FastAPI Application - SEO Content Generation Platform.

This is the main entry point for the API. It provides endpoints for:
- Creating article generation jobs
- Tracking job status
- Retrieving generated articles
- Direct (synchronous) article generation for simpler use cases
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Optional

import structlog
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_session, init_db
from app.models.schemas import (
    ArticleRequest,
    ArticleResponse,
    JobCreateResponse,
    JobResponse,
    JobStatus,
    SERPAnalysis,
    ArticleOutline,
)
from app.agents.seo_agent import SEOAgent
from app.jobs.job_manager import JobManager

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting SEO Content Generation Platform")
    await init_db()
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info("Shutting down")


app = FastAPI(
    title="SEO Content Generation Platform",
    description="""
    An intelligent agent-based system that generates SEO-optimized articles.
    
    ## Features
    
    - **SERP Analysis**: Analyzes top 10 search results for competitive insights
    - **Intelligent Outlines**: Creates structured outlines based on successful content
    - **Quality Content**: Generates human-like articles that follow SEO best practices
    - **SEO Validation**: Validates keyword density, heading structure, and more
    - **Job Management**: Track long-running generation tasks with resumability
    
    ## Endpoints
    
    - `POST /generate` - Synchronous article generation (for quick topics)
    - `POST /jobs` - Create async job for article generation
    - `GET /jobs/{job_id}` - Get job status and results
    - `POST /jobs/{job_id}/resume` - Resume a failed/incomplete job
    - `GET /research/{topic}` - Get SERP analysis for a topic
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Background task for async job processing
async def process_job(
    job_id: str,
    request: ArticleRequest,
    session: AsyncSession,
) -> None:
    """Background task to process article generation job."""
    job_manager = JobManager(session)
    agent = SEOAgent()

    try:
        # Get any existing data for resumption
        serp_data, outline = await job_manager.get_resumable_data(job_id)

        # Create progress callback
        async def progress_callback(status: JobStatus, progress: float, step: str):
            await job_manager.update_progress(job_id, status, progress, step)

        # Run research phase and save checkpoint
        if not serp_data:
            await progress_callback(JobStatus.RESEARCHING, 10, "Researching topic")
            serp_data = await agent.research_topic(request.topic)
            await job_manager.save_serp_data(job_id, serp_data)

        # Generate outline and save checkpoint
        if not outline:
            await progress_callback(JobStatus.OUTLINING, 35, "Creating outline")
            outline = await agent.generate_outline_only(request, serp_data)
            await job_manager.save_outline(job_id, outline)

        # Generate full article
        article = await agent.generate_article(
            request,
            progress_callback=progress_callback,
            existing_serp_data=serp_data,
            existing_outline=outline,
        )

        # Save final result
        await job_manager.save_result(job_id, article)

    except Exception as e:
        logger.error("Job processing failed", job_id=job_id, error=str(e))
        await job_manager.mark_failed(job_id, str(e))


# ==================== API Endpoints ====================


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "SEO Content Generation Platform",
        "version": "1.0.0",
    }


@app.post(
    "/generate",
    response_model=ArticleResponse,
    tags=["Content Generation"],
    summary="Generate article synchronously",
)
async def generate_article(request: ArticleRequest) -> ArticleResponse:
    """Generate an SEO-optimized article synchronously.

    This endpoint blocks until the article is generated. Use for:
    - Simple topics that generate quickly
    - Testing and development
    - When you need the result immediately

    For longer content or production use, prefer the async job endpoints.

    **Request Body:**
    - `topic`: The main topic or keyword (required)
    - `target_word_count`: Target length in words (default: 1500)
    - `language`: Language code (default: "en")

    **Returns:** Complete article with content, SEO metadata, and quality scores.
    """
    logger.info("Sync article generation requested", topic=request.topic)

    try:
        agent = SEOAgent()
        article = await agent.generate_article(request)
        return article

    except Exception as e:
        logger.error("Generation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@app.post(
    "/jobs",
    response_model=JobCreateResponse,
    tags=["Jobs"],
    summary="Create article generation job",
)
async def create_job(
    request: ArticleRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> JobCreateResponse:
    """Create an asynchronous article generation job.

    This immediately returns a job ID that you can use to track progress.
    The article generation happens in the background.

    **Benefits of async jobs:**
    - Non-blocking API calls
    - Progress tracking
    - Automatic checkpointing for resumability
    - Better for long-form content

    **Request Body:**
    - `topic`: The main topic or keyword (required)
    - `target_word_count`: Target length in words (default: 1500)
    - `language`: Language code (default: "en")

    **Returns:** Job ID and initial status.
    """
    job_manager = JobManager(session)

    try:
        job_id = await job_manager.create_job(request)

        # Schedule background processing
        background_tasks.add_task(
            process_job,
            job_id,
            request,
            session,
        )

        return JobCreateResponse(
            job_id=job_id,
            status=JobStatus.PENDING,
            message="Job created successfully. Use GET /jobs/{job_id} to track progress.",
        )

    except Exception as e:
        logger.error("Failed to create job", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")


@app.get(
    "/jobs/{job_id}",
    response_model=JobResponse,
    tags=["Jobs"],
    summary="Get job status",
)
async def get_job(
    job_id: str,
    session: AsyncSession = Depends(get_session),
) -> JobResponse:
    """Get the status and results of an article generation job.

    **Status values:**
    - `pending`: Job created, waiting to start
    - `researching`: Fetching and analyzing SERP data
    - `analyzing`: Extracting themes and insights
    - `outlining`: Creating article structure
    - `generating`: Writing content
    - `validating`: Checking SEO criteria
    - `completed`: Article ready
    - `failed`: Error occurred

    **Returns:** Job details including progress percentage and results (if complete).
    """
    job_manager = JobManager(session)
    job = await job_manager.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


@app.get(
    "/jobs",
    response_model=list[JobResponse],
    tags=["Jobs"],
    summary="List all jobs",
)
async def list_jobs(
    status: Optional[JobStatus] = None,
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
) -> list[JobResponse]:
    """List article generation jobs.

    **Query Parameters:**
    - `status`: Filter by job status (optional)
    - `limit`: Maximum number of jobs to return (default: 50)

    **Returns:** List of jobs ordered by creation time (newest first).
    """
    job_manager = JobManager(session)
    return await job_manager.list_jobs(status=status, limit=limit)


@app.post(
    "/jobs/{job_id}/resume",
    response_model=JobResponse,
    tags=["Jobs"],
    summary="Resume a failed or incomplete job",
)
async def resume_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> JobResponse:
    """Resume a failed or incomplete article generation job.

    The system saves checkpoints during processing:
    - After SERP data collection
    - After outline generation

    Resuming will skip already-completed steps, saving time and API costs.

    **Returns:** Updated job status.
    """
    job_manager = JobManager(session)
    job = await job_manager.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status == JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Job already completed")

    if job.status not in [JobStatus.FAILED, JobStatus.PENDING]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot resume job with status: {job.status}",
        )

    # Recreate request from job data
    # Note: In production, store full request in job
    result = await session.execute(
        "SELECT topic, target_word_count, language FROM jobs WHERE id = :id",
        {"id": job_id},
    )
    row = result.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Job data not found")

    request = ArticleRequest(
        topic=row[0],
        target_word_count=int(row[1]),
        language=row[2],
    )

    # Update status and schedule background processing
    await job_manager.update_progress(
        job_id, JobStatus.PENDING, 0, "Resuming job"
    )

    background_tasks.add_task(
        process_job,
        job_id,
        request,
        session,
    )

    return await job_manager.get_job(job_id)


@app.get(
    "/research/{topic}",
    response_model=SERPAnalysis,
    tags=["Research"],
    summary="Research a topic",
)
async def research_topic(topic: str) -> SERPAnalysis:
    """Get SERP analysis for a topic without generating an article.

    This is useful for:
    - Understanding the competitive landscape
    - Previewing what themes will be covered
    - Planning content strategy

    **Path Parameters:**
    - `topic`: The topic or keyword to research

    **Returns:** SERP analysis with themes, questions, and competitor insights.
    """
    try:
        agent = SEOAgent()
        analysis = await agent.research_topic(topic)
        return analysis

    except Exception as e:
        logger.error("Research failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Research failed: {str(e)}")


@app.post(
    "/outline",
    response_model=ArticleOutline,
    tags=["Research"],
    summary="Generate article outline only",
)
async def generate_outline(request: ArticleRequest) -> ArticleOutline:
    """Generate an article outline without full content.

    Useful for:
    - Previewing article structure before committing
    - Getting outline approval before generation
    - Understanding how the agent interprets the topic

    **Request Body:**
    - `topic`: The main topic or keyword (required)
    - `target_word_count`: Target length in words (default: 1500)
    - `language`: Language code (default: "en")

    **Returns:** Structured outline with sections, key points, and SEO metadata.
    """
    try:
        agent = SEOAgent()
        outline = await agent.generate_outline_only(request)
        return outline

    except Exception as e:
        logger.error("Outline generation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Outline generation failed: {str(e)}")


# Run with: uvicorn app.main:app --reload
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )


