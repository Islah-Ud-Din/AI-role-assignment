"""SERP Analysis Service.

Analyzes search results to extract themes, patterns, and insights
that inform content creation.
"""

import re
from collections import Counter
from typing import Optional

import structlog

from app.models.schemas import SERPAnalysis, ThemeAnalysis, SERPResult
from app.services.llm_client import LLMClient

logger = structlog.get_logger()


class SERPAnalyzer:
    """Analyzes SERP data to extract actionable insights."""

    # Common stop words to filter out
    STOP_WORDS = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
        "be", "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "can", "this", "that", "these",
        "those", "it", "its", "your", "you", "we", "our", "their", "them",
        "what", "which", "who", "how", "when", "where", "why", "all", "each",
        "every", "both", "few", "more", "most", "other", "some", "such", "no",
        "not", "only", "own", "same", "so", "than", "too", "very", "just",
        "about", "into", "over", "after", "before", "between", "under",
        "again", "further", "then", "once", "here", "there", "any", "out",
    }

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """Initialize analyzer with optional LLM client."""
        self.llm_client = llm_client

    async def analyze(self, serp_data: SERPAnalysis) -> SERPAnalysis:
        """Perform comprehensive analysis on SERP data.

        Args:
            serp_data: Raw SERP data from search results

        Returns:
            Enhanced SERPAnalysis with themes and insights
        """
        logger.info("Analyzing SERP data", query=serp_data.query, results=len(serp_data.results))

        # Extract themes from titles and snippets
        themes = self._extract_themes(serp_data.results)

        # Analyze content patterns
        content_indicators = self._analyze_content_patterns(serp_data.results)

        # Extract additional questions if LLM is available
        if self.llm_client and not serp_data.common_questions:
            questions = await self._extract_questions_with_llm(serp_data)
            serp_data.common_questions = questions

        # Update the analysis
        serp_data.common_themes = themes
        serp_data.avg_content_indicators = content_indicators

        logger.info(
            "SERP analysis complete",
            themes=len(themes),
            questions=len(serp_data.common_questions),
        )

        return serp_data

    def _extract_themes(self, results: list[SERPResult]) -> list[ThemeAnalysis]:
        """Extract common themes from SERP results."""
        # Combine all text for analysis
        all_text = " ".join(
            f"{r.title} {r.snippet}" for r in results
        ).lower()

        # Extract meaningful phrases (2-3 word combinations)
        words = re.findall(r'\b[a-z]+\b', all_text)
        filtered_words = [w for w in words if w not in self.STOP_WORDS and len(w) > 3]

        # Count word frequencies
        word_freq = Counter(filtered_words)

        # Extract bigrams and trigrams
        bigrams = [
            f"{filtered_words[i]} {filtered_words[i+1]}"
            for i in range(len(filtered_words) - 1)
            if filtered_words[i] not in self.STOP_WORDS
            and filtered_words[i+1] not in self.STOP_WORDS
        ]
        bigram_freq = Counter(bigrams)

        # Build themes from most common patterns
        themes = []

        # Add top single-word themes
        for word, count in word_freq.most_common(10):
            if count >= 2:  # Appears in at least 2 results
                related = [
                    bg for bg, _ in bigram_freq.most_common(20)
                    if word in bg
                ][:3]
                themes.append(
                    ThemeAnalysis(
                        theme=word,
                        frequency=count,
                        related_keywords=related,
                        example_headings=self._find_headings_with_theme(results, word),
                    )
                )

        # Add top bigram themes
        for phrase, count in bigram_freq.most_common(5):
            if count >= 2:
                themes.append(
                    ThemeAnalysis(
                        theme=phrase,
                        frequency=count,
                        related_keywords=[],
                        example_headings=self._find_headings_with_theme(results, phrase),
                    )
                )

        # Sort by frequency and return top themes
        themes.sort(key=lambda t: t.frequency, reverse=True)
        return themes[:10]

    def _find_headings_with_theme(
        self, results: list[SERPResult], theme: str
    ) -> list[str]:
        """Find example headings that contain the theme."""
        headings = []
        theme_lower = theme.lower()
        for result in results:
            if theme_lower in result.title.lower():
                headings.append(result.title)
                if len(headings) >= 3:
                    break
        return headings

    def _analyze_content_patterns(
        self, results: list[SERPResult]
    ) -> dict[str, int]:
        """Analyze common content patterns in results."""
        patterns = {
            "listicles": 0,  # "10 best", "15 top", etc.
            "how_to": 0,     # "How to" guides
            "ultimate_guide": 0,  # Comprehensive guides
            "comparison": 0,  # "vs", "compared"
            "year_specific": 0,  # Contains year (2024, 2025)
            "question_based": 0,  # What, Why, How titles
        }

        for result in results:
            title_lower = result.title.lower()

            # Check for listicles
            if re.search(r'\d+\s+(best|top|ways|tips|tools|reasons)', title_lower):
                patterns["listicles"] += 1

            # Check for how-to content
            if "how to" in title_lower:
                patterns["how_to"] += 1

            # Check for comprehensive guides
            if any(word in title_lower for word in ["ultimate", "complete", "comprehensive", "definitive"]):
                patterns["ultimate_guide"] += 1

            # Check for comparisons
            if any(word in title_lower for word in [" vs ", "compared", "comparison", "versus"]):
                patterns["comparison"] += 1

            # Check for year-specific content
            if re.search(r'20\d{2}', title_lower):
                patterns["year_specific"] += 1

            # Check for question-based titles
            if any(title_lower.startswith(q) for q in ["what", "why", "how", "when", "where", "which"]):
                patterns["question_based"] += 1

        return patterns

    async def _extract_questions_with_llm(
        self, serp_data: SERPAnalysis
    ) -> list[str]:
        """Use LLM to extract common questions from SERP data."""
        if not self.llm_client:
            return []

        prompt = f"""Based on these search results for "{serp_data.query}", identify 5-8 common questions users might have:

Results:
{chr(10).join(f"- {r.title}: {r.snippet}" for r in serp_data.results[:5])}

Return only the questions, one per line, without numbering."""

        try:
            response = await self.llm_client.generate(
                prompt,
                max_tokens=500,
                temperature=0.3,
            )
            questions = [q.strip() for q in response.strip().split("\n") if q.strip()]
            return questions[:8]
        except Exception as e:
            logger.error("Failed to extract questions with LLM", error=str(e))
            return []

    def get_content_recommendations(self, serp_data: SERPAnalysis) -> dict:
        """Generate content recommendations based on analysis."""
        indicators = serp_data.avg_content_indicators or {}

        recommendations = {
            "suggested_format": "comprehensive_guide",
            "include_list_format": indicators.get("listicles", 0) >= 3,
            "include_how_to_section": indicators.get("how_to", 0) >= 2,
            "include_comparisons": indicators.get("comparison", 0) >= 2,
            "use_current_year": indicators.get("year_specific", 0) >= 3,
            "address_questions": len(serp_data.common_questions) > 0,
            "top_themes_to_cover": [t.theme for t in (serp_data.common_themes or [])[:5]],
        }

        # Determine primary format
        if indicators.get("listicles", 0) >= 5:
            recommendations["suggested_format"] = "listicle"
        elif indicators.get("how_to", 0) >= 4:
            recommendations["suggested_format"] = "how_to_guide"
        elif indicators.get("comparison", 0) >= 4:
            recommendations["suggested_format"] = "comparison"

        return recommendations


