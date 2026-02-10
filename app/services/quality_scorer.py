"""Content Quality Scoring Service.

Evaluates generated content quality and determines if revisions are needed.
"""

import re
from typing import Optional

import structlog

from app.models.schemas import ArticleResponse, QualityScore
from app.services.llm_client import LLMClient

logger = structlog.get_logger()


class QualityScorer:
    """Evaluates and scores content quality."""

    # Quality thresholds
    MIN_ACCEPTABLE_SCORE = 70
    REVISION_THRESHOLD = 60

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """Initialize quality scorer."""
        self.llm_client = llm_client

    async def score(self, article: ArticleResponse) -> QualityScore:
        """Score the quality of generated content.

        Args:
            article: Article to score

        Returns:
            QualityScore with detailed metrics
        """
        logger.info("Scoring content quality", title=article.title)

        # Calculate readability score
        readability_score = self._calculate_readability(article)

        # Calculate SEO score from validation if available
        seo_score = 80.0  # Default
        if article.seo_validation:
            seo_score = article.seo_validation.score

        # Calculate uniqueness indicators
        uniqueness = self._assess_uniqueness(article)

        # Get improvement suggestions
        suggestions = self._generate_suggestions(article, readability_score, seo_score)

        # Calculate overall score (weighted average)
        overall_score = (
            readability_score * 0.4 +
            seo_score * 0.4 +
            uniqueness.get("variety_score", 70) * 0.2
        )

        needs_revision = overall_score < self.REVISION_THRESHOLD

        result = QualityScore(
            overall_score=round(overall_score, 1),
            readability_score=round(readability_score, 1),
            seo_score=round(seo_score, 1),
            uniqueness_indicators=uniqueness,
            improvement_suggestions=suggestions,
            needs_revision=needs_revision,
        )

        logger.info(
            "Quality scoring complete",
            overall_score=result.overall_score,
            needs_revision=needs_revision,
        )

        return result

    def _calculate_readability(self, article: ArticleResponse) -> float:
        """Calculate readability score using multiple metrics."""
        content = article.full_content
        sentences = self._split_sentences(content)
        words = content.split()
        syllable_count = sum(self._count_syllables(w) for w in words)

        if not sentences or not words:
            return 50.0

        # Average sentence length
        avg_sentence_length = len(words) / len(sentences)

        # Average syllables per word
        avg_syllables = syllable_count / len(words) if words else 2

        # Flesch Reading Ease (simplified)
        # Higher is easier to read
        flesch = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables)
        flesch = max(0, min(100, flesch))  # Clamp to 0-100

        # Adjust for ideal range (aim for 60-70 Flesch score for general audience)
        if 50 <= flesch <= 70:
            readability_score = 90 + (flesch - 60)  # Bonus for optimal range
        elif flesch > 70:
            readability_score = 85 - (flesch - 70) * 0.3  # Slightly penalize too simple
        else:
            readability_score = 60 + (flesch / 50) * 20  # Scale up from difficult

        # Penalize very long sentences
        long_sentences = sum(1 for s in sentences if len(s.split()) > 30)
        if long_sentences > len(sentences) * 0.2:
            readability_score -= 10

        # Check paragraph structure
        paragraphs = [p for p in content.split("\n\n") if p.strip()]
        avg_para_length = len(words) / len(paragraphs) if paragraphs else 0

        if 50 <= avg_para_length <= 150:
            readability_score += 5  # Good paragraph length
        elif avg_para_length > 200:
            readability_score -= 5  # Paragraphs too long

        return max(0, min(100, readability_score))

    def _assess_uniqueness(self, article: ArticleResponse) -> dict:
        """Assess content uniqueness indicators."""
        content = article.full_content.lower()
        words = content.split()

        # Vocabulary richness (type-token ratio)
        unique_words = set(words)
        ttr = len(unique_words) / len(words) if words else 0
        vocabulary_score = min(100, ttr * 200)  # Scale to 0-100

        # Sentence variety
        sentences = self._split_sentences(content)
        sentence_lengths = [len(s.split()) for s in sentences]
        length_variety = 0
        if sentence_lengths:
            avg_len = sum(sentence_lengths) / len(sentence_lengths)
            variance = sum((l - avg_len) ** 2 for l in sentence_lengths) / len(sentence_lengths)
            length_variety = min(100, (variance ** 0.5) * 10)

        # Check for cliché phrases
        cliches = [
            "in today's world", "at the end of the day", "it goes without saying",
            "needless to say", "in conclusion", "last but not least",
            "each and every", "first and foremost", "when all is said and done",
        ]
        cliche_count = sum(1 for c in cliches if c in content)
        cliche_penalty = cliche_count * 5

        variety_score = (vocabulary_score + length_variety) / 2 - cliche_penalty
        variety_score = max(0, min(100, variety_score))

        return {
            "vocabulary_richness": round(vocabulary_score, 1),
            "sentence_variety": round(length_variety, 1),
            "cliche_count": cliche_count,
            "variety_score": round(variety_score, 1),
        }

    def _generate_suggestions(
        self,
        article: ArticleResponse,
        readability: float,
        seo_score: float,
    ) -> list[str]:
        """Generate improvement suggestions."""
        suggestions = []

        # Readability suggestions
        if readability < 60:
            suggestions.append("Simplify sentence structure - use shorter sentences")
            suggestions.append("Break up long paragraphs into smaller chunks")
        elif readability < 75:
            suggestions.append("Consider varying sentence length for better flow")

        # SEO suggestions
        if seo_score < 70:
            suggestions.append("Review keyword placement in headings and intro")

        # Word count suggestions
        if article.word_count < 1000:
            suggestions.append("Consider expanding content depth in key sections")
        elif article.word_count > 3000:
            suggestions.append("Consider adding a table of contents for navigation")

        # Structure suggestions
        section_count = len(article.sections)
        if section_count < 4:
            suggestions.append("Add more sections to improve content depth")
        elif section_count > 10:
            suggestions.append("Consider consolidating some sections for focus")

        # Link suggestions
        if len(article.internal_links) < 3:
            suggestions.append("Add more internal linking opportunities")
        if len(article.external_references) < 2:
            suggestions.append("Include more authoritative external references")

        return suggestions[:5]  # Return top 5 suggestions

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences."""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip() and len(s.split()) > 2]

    def _count_syllables(self, word: str) -> int:
        """Estimate syllable count for a word."""
        word = word.lower().strip()
        if len(word) <= 3:
            return 1

        # Count vowel groups
        vowels = "aeiouy"
        count = 0
        prev_vowel = False

        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel

        # Adjust for silent e
        if word.endswith("e"):
            count -= 1

        return max(1, count)

    async def suggest_revisions(
        self,
        article: ArticleResponse,
        quality_score: QualityScore,
    ) -> Optional[str]:
        """Use LLM to suggest specific revisions if quality is low."""
        if not self.llm_client or not quality_score.needs_revision:
            return None

        prompt = f"""Review this article and suggest specific revisions to improve quality.

Current scores:
- Overall: {quality_score.overall_score}/100
- Readability: {quality_score.readability_score}/100
- SEO: {quality_score.seo_score}/100

Issues identified:
{chr(10).join(f'- {s}' for s in quality_score.improvement_suggestions)}

Article title: {article.title}
Word count: {article.word_count}

Provide 3-5 specific, actionable revisions to improve this content:"""

        try:
            response = await self.llm_client.generate(
                prompt,
                max_tokens=500,
                temperature=0.5,
            )
            return response.strip()
        except Exception as e:
            logger.error("Failed to generate revision suggestions", error=str(e))
            return None


