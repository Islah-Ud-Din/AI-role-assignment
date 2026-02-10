"""Article Outline Generator.

Creates structured outlines based on SERP analysis and SEO best practices.
"""

import json
import re
from typing import Optional

import structlog

from app.models.schemas import (
    ArticleOutline,
    OutlineSection,
    SERPAnalysis,
    ArticleRequest,
)
from app.services.llm_client import LLMClient

logger = structlog.get_logger()


OUTLINE_SYSTEM_PROMPT = """You are an expert SEO content strategist. Your task is to create detailed, 
SEO-optimized article outlines that will rank well in search engines while providing genuine value to readers.

Key principles:
1. Primary keyword should appear in the H1 title and naturally in H2s
2. Cover topics that competing content covers, but add unique angles
3. Structure should follow a logical flow that matches search intent
4. Include actionable, specific subsections that provide real value
5. Balance SEO optimization with readability - no keyword stuffing

Output format: Valid JSON matching the specified schema."""


class OutlineGenerator:
    """Generates SEO-optimized article outlines."""

    def __init__(self, llm_client: LLMClient):
        """Initialize outline generator."""
        self.llm_client = llm_client

    async def generate(
        self,
        request: ArticleRequest,
        serp_analysis: SERPAnalysis,
    ) -> ArticleOutline:
        """Generate an article outline based on request and SERP analysis.

        Args:
            request: Original article request
            serp_analysis: Analyzed SERP data

        Returns:
            Structured article outline
        """
        logger.info("Generating article outline", topic=request.topic)

        prompt = self._build_prompt(request, serp_analysis)

        response = await self.llm_client.generate_structured(
            prompt,
            system_prompt=OUTLINE_SYSTEM_PROMPT,
            max_tokens=3000,
            temperature=0.6,
        )

        outline = self._parse_response(response, request)

        logger.info(
            "Outline generated",
            sections=len(outline.sections),
            estimated_words=outline.estimated_word_count,
        )

        return outline

    def _build_prompt(
        self, request: ArticleRequest, serp_analysis: SERPAnalysis
    ) -> str:
        """Build the prompt for outline generation."""
        # Format themes for the prompt
        themes_text = ""
        if serp_analysis.common_themes:
            themes_text = "Common themes from top-ranking content:\n"
            for theme in serp_analysis.common_themes[:7]:
                themes_text += f"- {theme.theme} (found in {theme.frequency} results)\n"

        # Format questions
        questions_text = ""
        if serp_analysis.common_questions:
            questions_text = "Common questions users ask:\n"
            for q in serp_analysis.common_questions[:6]:
                questions_text += f"- {q}\n"

        # Format competitor titles
        competitor_titles = "Top-ranking article titles:\n"
        for result in serp_analysis.results[:5]:
            competitor_titles += f"- {result.title}\n"

        prompt = f"""Create a comprehensive SEO-optimized article outline for the topic: "{request.topic}"

Target word count: {request.target_word_count} words
Language: {request.language}

COMPETITIVE ANALYSIS:
{competitor_titles}

{themes_text}

{questions_text}

REQUIREMENTS:
1. Create a compelling H1 title that includes the primary keyword
2. Write a meta description (max 155 characters) that encourages clicks
3. Structure with H2 and H3 headings covering all important subtopics
4. Each section should have 2-4 key points to cover
5. Distribute target word count across sections proportionally
6. Identify primary keyword and 5-8 secondary keywords
7. Consider including an FAQ section if questions are relevant

OUTPUT FORMAT (valid JSON):
{{
    "title": "H1 title with primary keyword",
    "meta_description": "Compelling 150-155 char description",
    "primary_keyword": "main keyword",
    "secondary_keywords": ["keyword1", "keyword2", ...],
    "target_audience": "who this article is for",
    "content_angle": "unique angle/value proposition",
    "sections": [
        {{
            "heading": "Section heading",
            "level": 2,
            "key_points": ["point 1", "point 2"],
            "target_word_count": 200,
            "keywords_to_include": ["relevant", "keywords"]
        }}
    ],
    "estimated_word_count": {request.target_word_count}
}}

Return ONLY valid JSON, no additional text."""

        return prompt

    def _parse_response(
        self, response: str, request: ArticleRequest
    ) -> ArticleOutline:
        """Parse LLM response into ArticleOutline."""
        # Extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', response)
        if not json_match:
            logger.warning("No JSON found in response, using fallback outline")
            return self._create_fallback_outline(request)

        try:
            data = json.loads(json_match.group())

            sections = []
            for s in data.get("sections", []):
                sections.append(
                    OutlineSection(
                        heading=s.get("heading", "Untitled Section"),
                        level=s.get("level", 2),
                        key_points=s.get("key_points", []),
                        target_word_count=s.get("target_word_count", 200),
                        keywords_to_include=s.get("keywords_to_include", []),
                    )
                )

            return ArticleOutline(
                title=data.get("title", request.topic.title()),
                meta_description=data.get("meta_description", "")[:160],
                primary_keyword=data.get("primary_keyword", request.topic),
                secondary_keywords=data.get("secondary_keywords", []),
                sections=sections,
                estimated_word_count=data.get("estimated_word_count", request.target_word_count),
                target_audience=data.get("target_audience", ""),
                content_angle=data.get("content_angle", ""),
            )

        except json.JSONDecodeError as e:
            logger.error("Failed to parse outline JSON", error=str(e))
            return self._create_fallback_outline(request)

    def _create_fallback_outline(self, request: ArticleRequest) -> ArticleOutline:
        """Create a basic fallback outline if LLM fails."""
        topic = request.topic
        word_count = request.target_word_count

        sections = [
            OutlineSection(
                heading=f"What is {topic.title()}?",
                level=2,
                key_points=["Definition", "Importance", "Background"],
                target_word_count=int(word_count * 0.15),
            ),
            OutlineSection(
                heading=f"Key Benefits of {topic.title()}",
                level=2,
                key_points=["Primary benefits", "Use cases", "Who it helps"],
                target_word_count=int(word_count * 0.2),
            ),
            OutlineSection(
                heading=f"How to Get Started with {topic.title()}",
                level=2,
                key_points=["Step 1", "Step 2", "Step 3", "Best practices"],
                target_word_count=int(word_count * 0.25),
            ),
            OutlineSection(
                heading=f"Top {topic.title()} Options to Consider",
                level=2,
                key_points=["Option 1", "Option 2", "Option 3", "Comparison"],
                target_word_count=int(word_count * 0.25),
            ),
            OutlineSection(
                heading=f"Conclusion: Making the Most of {topic.title()}",
                level=2,
                key_points=["Summary", "Key takeaways", "Next steps"],
                target_word_count=int(word_count * 0.15),
            ),
        ]

        return ArticleOutline(
            title=f"The Complete Guide to {topic.title()} in 2025",
            meta_description=f"Discover everything you need to know about {topic}. Our comprehensive guide covers benefits, best practices, and top options.",
            primary_keyword=topic.lower(),
            secondary_keywords=[f"best {topic}", f"{topic} guide", f"{topic} tips"],
            sections=sections,
            estimated_word_count=word_count,
            target_audience="Professionals and enthusiasts",
            content_angle="Comprehensive guide",
        )


