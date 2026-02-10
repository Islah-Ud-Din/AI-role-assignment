"""Article Content Generator.

Generates high-quality, SEO-optimized article content from outlines.
"""

import json
import re
from typing import Optional

import structlog

from app.models.schemas import (
    ArticleOutline,
    ArticleSection,
    ArticleResponse,
    SEOMetadata,
    KeywordAnalysis,
    LinkSuggestion,
    ExternalReference,
    FAQItem,
    SERPAnalysis,
)
from app.services.llm_client import LLMClient

logger = structlog.get_logger()


CONTENT_SYSTEM_PROMPT = """You are an expert content writer specializing in SEO-optimized articles.
Your writing should be:
1. Engaging and human-like - NOT robotic or repetitive
2. Well-structured with clear transitions
3. Naturally incorporating keywords without stuffing
4. Providing genuine value and actionable insights
5. Using varied sentence structure and vocabulary

Write like a knowledgeable industry expert sharing insights, not a content mill bot.
Each section should flow naturally into the next."""


class ContentGenerator:
    """Generates article content from outlines."""

    def __init__(self, llm_client: LLMClient):
        """Initialize content generator."""
        self.llm_client = llm_client

    async def generate(
        self,
        outline: ArticleOutline,
        serp_analysis: Optional[SERPAnalysis] = None,
    ) -> ArticleResponse:
        """Generate complete article content from outline.

        Args:
            outline: Article outline to expand
            serp_analysis: Optional SERP data for context

        Returns:
            Complete article response with all content and metadata
        """
        logger.info("Generating article content", title=outline.title)

        # Generate content for each section
        sections = await self._generate_sections(outline)

        # Generate FAQ if we have questions
        faq_items = []
        if serp_analysis and serp_analysis.common_questions:
            faq_items = await self._generate_faq(
                serp_analysis.common_questions[:5],
                outline.primary_keyword,
            )

        # Generate linking suggestions
        internal_links = await self._generate_internal_links(outline, sections)
        external_refs = await self._generate_external_references(outline)

        # Compile full content
        full_content = self._compile_content(outline.title, sections, faq_items)
        word_count = len(full_content.split())

        # Analyze keywords in generated content
        keyword_analysis = self._analyze_keywords(
            full_content,
            outline.primary_keyword,
            outline.secondary_keywords,
        )

        # Build SEO metadata
        seo_metadata = SEOMetadata(
            title_tag=outline.title[:60],
            meta_description=outline.meta_description,
            og_title=outline.title[:60],
            og_description=outline.meta_description,
            focus_keyword=outline.primary_keyword,
            secondary_keywords=outline.secondary_keywords,
        )

        # Build SERP summary if available
        serp_summary = None
        if serp_analysis:
            serp_summary = {
                "query": serp_analysis.query,
                "results_analyzed": len(serp_analysis.results),
                "top_themes": [t.theme for t in (serp_analysis.common_themes or [])[:5]],
                "questions_found": len(serp_analysis.common_questions),
            }

        return ArticleResponse(
            title=outline.title,
            sections=sections,
            full_content=full_content,
            word_count=word_count,
            seo_metadata=seo_metadata,
            keyword_analysis=keyword_analysis,
            internal_links=internal_links,
            external_references=external_refs,
            faq_section=faq_items,
            serp_analysis_summary=serp_summary,
        )

    async def _generate_sections(
        self, outline: ArticleOutline
    ) -> list[ArticleSection]:
        """Generate content for each section."""
        sections = []

        for idx, section_outline in enumerate(outline.sections):
            logger.debug("Generating section", section=section_outline.heading)

            # Build context from previous sections
            prev_context = ""
            if sections:
                prev_context = f"Previous section ended with: ...{sections[-1].content[-200:]}"

            prompt = f"""Write the content for this article section.

Article title: {outline.title}
Primary keyword: {outline.primary_keyword}
Target audience: {outline.target_audience}

SECTION TO WRITE:
Heading (H{section_outline.level}): {section_outline.heading}
Target word count: {section_outline.target_word_count} words
Key points to cover: {', '.join(section_outline.key_points)}
Keywords to include naturally: {', '.join(section_outline.keywords_to_include)}

{prev_context}

GUIDELINES:
- Write engaging, human-sounding content
- Naturally incorporate the specified keywords
- Cover all key points with specific, actionable information
- Use varied sentence structure
- Include specific examples or data where relevant
- {"Start with an engaging introduction that hooks the reader" if idx == 0 else "Transition smoothly from the previous section"}
- Do NOT include the heading itself, only the body content

Write approximately {section_outline.target_word_count} words of body content:"""

            content = await self.llm_client.generate(
                prompt,
                system_prompt=CONTENT_SYSTEM_PROMPT,
                max_tokens=section_outline.target_word_count * 2,
                temperature=0.75,
            )

            sections.append(
                ArticleSection(
                    heading=section_outline.heading,
                    level=section_outline.level,
                    content=content.strip(),
                )
            )

        return sections

    async def _generate_faq(
        self, questions: list[str], primary_keyword: str
    ) -> list[FAQItem]:
        """Generate FAQ section from common questions."""
        if not questions:
            return []

        prompt = f"""Create helpful, informative FAQ answers for these questions about {primary_keyword}.

Questions:
{chr(10).join(f'{i+1}. {q}' for i, q in enumerate(questions))}

For each question, provide a clear, concise answer (2-4 sentences).
Format as JSON array:
[
    {{"question": "...", "answer": "..."}},
    ...
]

Return only the JSON array:"""

        try:
            response = await self.llm_client.generate_structured(
                prompt,
                max_tokens=1500,
                temperature=0.5,
            )

            # Parse JSON response
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                faq_data = json.loads(json_match.group())
                return [
                    FAQItem(question=f["question"], answer=f["answer"])
                    for f in faq_data
                ]
        except Exception as e:
            logger.error("Failed to generate FAQ", error=str(e))

        return []

    async def _generate_internal_links(
        self, outline: ArticleOutline, sections: list[ArticleSection]
    ) -> list[LinkSuggestion]:
        """Generate internal linking suggestions."""
        prompt = f"""Based on this article about "{outline.title}", suggest 3-5 internal linking opportunities.

Article sections:
{chr(10).join(f'- {s.heading}' for s in sections)}

Primary topic: {outline.primary_keyword}
Secondary topics: {', '.join(outline.secondary_keywords[:5])}

For each suggestion, provide:
1. Anchor text (the clickable text)
2. Target page topic (what the linked page should be about)
3. Context (which section this link belongs in)
4. Relevance score (0-1)

Format as JSON array:
[
    {{
        "anchor_text": "text to link",
        "suggested_target_topic": "topic of target page",
        "context": "which section to place it",
        "relevance_score": 0.8
    }}
]

Return only the JSON array:"""

        try:
            response = await self.llm_client.generate_structured(
                prompt,
                max_tokens=1000,
                temperature=0.4,
            )

            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                links_data = json.loads(json_match.group())
                return [
                    LinkSuggestion(
                        anchor_text=l["anchor_text"],
                        suggested_target_topic=l["suggested_target_topic"],
                        context=l["context"],
                        relevance_score=l.get("relevance_score", 0.7),
                    )
                    for l in links_data[:5]
                ]
        except Exception as e:
            logger.error("Failed to generate internal links", error=str(e))

        return []

    async def _generate_external_references(
        self, outline: ArticleOutline
    ) -> list[ExternalReference]:
        """Generate external reference suggestions."""
        prompt = f"""Suggest 2-4 authoritative external sources to reference in an article about "{outline.title}".

Primary topic: {outline.primary_keyword}

For each source, specify:
1. Source name (e.g., "Gartner Research", "Harvard Business Review")
2. Source type (industry report, academic study, news article, official documentation)
3. What to cite from them
4. Where in the article to place the citation
5. Why this source adds credibility

Format as JSON array:
[
    {{
        "source_name": "Name of Source",
        "source_type": "industry report",
        "url": null,
        "citation_context": "Cite when discussing [specific point]",
        "credibility_reason": "Why this source is authoritative"
    }}
]

Return only the JSON array:"""

        try:
            response = await self.llm_client.generate_structured(
                prompt,
                max_tokens=800,
                temperature=0.4,
            )

            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                refs_data = json.loads(json_match.group())
                return [
                    ExternalReference(
                        source_name=r["source_name"],
                        source_type=r["source_type"],
                        url=r.get("url"),
                        citation_context=r["citation_context"],
                        credibility_reason=r["credibility_reason"],
                    )
                    for r in refs_data[:4]
                ]
        except Exception as e:
            logger.error("Failed to generate external references", error=str(e))

        return []

    def _compile_content(
        self,
        title: str,
        sections: list[ArticleSection],
        faq_items: list[FAQItem],
    ) -> str:
        """Compile all content into a formatted article."""
        parts = [f"# {title}\n"]

        for section in sections:
            heading_prefix = "#" * (section.level + 1)
            parts.append(f"\n{heading_prefix} {section.heading}\n")
            parts.append(section.content)

        if faq_items:
            parts.append("\n## Frequently Asked Questions\n")
            for faq in faq_items:
                parts.append(f"\n### {faq.question}\n")
                parts.append(faq.answer)

        return "\n".join(parts)

    def _analyze_keywords(
        self,
        content: str,
        primary_keyword: str,
        secondary_keywords: list[str],
    ) -> KeywordAnalysis:
        """Analyze keyword usage in the content."""
        content_lower = content.lower()
        word_count = len(content.split())

        # Count primary keyword
        primary_count = content_lower.count(primary_keyword.lower())
        primary_density = (primary_count / word_count) * 100 if word_count > 0 else 0

        # Count secondary keywords
        secondary_counts = {}
        for kw in secondary_keywords:
            count = content_lower.count(kw.lower())
            if count > 0:
                secondary_counts[kw] = count

        # Extract potential LSI keywords (simple approach)
        lsi_keywords = self._extract_lsi_keywords(content, primary_keyword)

        return KeywordAnalysis(
            primary_keyword=primary_keyword,
            primary_keyword_count=primary_count,
            primary_keyword_density=round(primary_density, 2),
            secondary_keywords=secondary_counts,
            lsi_keywords=lsi_keywords,
        )

    def _extract_lsi_keywords(
        self, content: str, primary_keyword: str
    ) -> list[str]:
        """Extract potential LSI (related) keywords."""
        # Simple extraction based on frequent terms near primary keyword
        words = re.findall(r'\b[a-z]{4,}\b', content.lower())
        word_freq = {}
        for word in words:
            if word not in primary_keyword.lower().split():
                word_freq[word] = word_freq.get(word, 0) + 1

        # Return top frequent words as potential LSI keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [w[0] for w in sorted_words[:10] if w[1] >= 3]


