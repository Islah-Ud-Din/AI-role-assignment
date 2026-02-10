"""SEO Validation Service.

Validates that generated content meets SEO best practices and quality criteria.
"""

from typing import Optional

import structlog

from app.models.schemas import ArticleResponse, SEOValidationResult

logger = structlog.get_logger()


class SEOValidator:
    """Validates articles against SEO best practices."""

    # SEO validation thresholds
    MIN_WORD_COUNT = 300
    MAX_WORD_COUNT = 15000
    MIN_KEYWORD_DENSITY = 0.5
    MAX_KEYWORD_DENSITY = 3.0
    MIN_TITLE_LENGTH = 30
    MAX_TITLE_LENGTH = 60
    MIN_META_DESC_LENGTH = 120
    MAX_META_DESC_LENGTH = 160
    MIN_H2_HEADINGS = 2
    MIN_INTERNAL_LINKS = 2
    MIN_EXTERNAL_REFS = 1

    def validate(self, article: ArticleResponse) -> SEOValidationResult:
        """Validate an article against SEO criteria.

        Args:
            article: Generated article to validate

        Returns:
            SEOValidationResult with pass/fail status and details
        """
        logger.info("Validating article SEO", title=article.title)

        checks = {}
        issues = []
        suggestions = []

        # 1. Word count check
        checks["word_count_adequate"] = self._check_word_count(
            article.word_count, issues, suggestions
        )

        # 2. Title tag check
        checks["title_tag_optimized"] = self._check_title_tag(
            article.seo_metadata.title_tag,
            article.keyword_analysis.primary_keyword,
            issues,
            suggestions,
        )

        # 3. Meta description check
        checks["meta_description_optimized"] = self._check_meta_description(
            article.seo_metadata.meta_description,
            article.keyword_analysis.primary_keyword,
            issues,
            suggestions,
        )

        # 4. Keyword density check
        checks["keyword_density_optimal"] = self._check_keyword_density(
            article.keyword_analysis.primary_keyword_density,
            issues,
            suggestions,
        )

        # 5. Heading structure check
        checks["heading_structure_valid"] = self._check_heading_structure(
            article.sections,
            issues,
            suggestions,
        )

        # 6. Primary keyword in first paragraph
        checks["keyword_in_intro"] = self._check_keyword_in_intro(
            article.sections,
            article.keyword_analysis.primary_keyword,
            issues,
            suggestions,
        )

        # 7. Internal links check
        checks["internal_links_present"] = self._check_internal_links(
            article.internal_links,
            issues,
            suggestions,
        )

        # 8. External references check
        checks["external_refs_present"] = self._check_external_refs(
            article.external_references,
            issues,
            suggestions,
        )

        # 9. Content uniqueness indicators
        checks["content_appears_unique"] = self._check_content_uniqueness(
            article.sections,
            issues,
            suggestions,
        )

        # Calculate overall score
        passed_checks = sum(1 for v in checks.values() if v)
        total_checks = len(checks)
        score = (passed_checks / total_checks) * 100 if total_checks > 0 else 0

        is_valid = score >= 70  # 70% threshold for validity

        result = SEOValidationResult(
            is_valid=is_valid,
            score=round(score, 1),
            checks=checks,
            issues=issues,
            suggestions=suggestions,
        )

        logger.info(
            "SEO validation complete",
            is_valid=is_valid,
            score=score,
            issues=len(issues),
        )

        return result

    def _check_word_count(
        self,
        word_count: int,
        issues: list,
        suggestions: list,
    ) -> bool:
        """Check if word count is within acceptable range."""
        if word_count < self.MIN_WORD_COUNT:
            issues.append(
                f"Word count ({word_count}) is below minimum ({self.MIN_WORD_COUNT})"
            )
            suggestions.append("Add more comprehensive content to each section")
            return False
        elif word_count > self.MAX_WORD_COUNT:
            issues.append(
                f"Word count ({word_count}) exceeds maximum ({self.MAX_WORD_COUNT})"
            )
            suggestions.append("Consider splitting into multiple articles")
            return False
        return True

    def _check_title_tag(
        self,
        title: str,
        keyword: str,
        issues: list,
        suggestions: list,
    ) -> bool:
        """Check title tag optimization."""
        valid = True

        # Length check
        if len(title) < self.MIN_TITLE_LENGTH:
            issues.append(f"Title tag too short ({len(title)} chars)")
            suggestions.append("Expand title to 50-60 characters")
            valid = False
        elif len(title) > self.MAX_TITLE_LENGTH:
            issues.append(f"Title tag too long ({len(title)} chars) - may be truncated")
            suggestions.append("Shorten title to under 60 characters")
            valid = False

        # Keyword presence
        if keyword.lower() not in title.lower():
            issues.append("Primary keyword not found in title tag")
            suggestions.append("Include the primary keyword near the beginning of the title")
            valid = False

        return valid

    def _check_meta_description(
        self,
        description: str,
        keyword: str,
        issues: list,
        suggestions: list,
    ) -> bool:
        """Check meta description optimization."""
        valid = True

        # Length check
        if len(description) < self.MIN_META_DESC_LENGTH:
            issues.append(f"Meta description too short ({len(description)} chars)")
            suggestions.append("Expand meta description to 150-160 characters")
            valid = False
        elif len(description) > self.MAX_META_DESC_LENGTH:
            issues.append(f"Meta description too long ({len(description)} chars)")
            suggestions.append("Shorten meta description to under 160 characters")
            valid = False

        # Keyword presence
        if keyword.lower() not in description.lower():
            issues.append("Primary keyword not found in meta description")
            suggestions.append("Include the primary keyword naturally in the meta description")
            valid = False

        return valid

    def _check_keyword_density(
        self,
        density: float,
        issues: list,
        suggestions: list,
    ) -> bool:
        """Check keyword density is optimal."""
        if density < self.MIN_KEYWORD_DENSITY:
            issues.append(f"Keyword density ({density}%) is too low")
            suggestions.append("Increase natural usage of primary keyword throughout content")
            return False
        elif density > self.MAX_KEYWORD_DENSITY:
            issues.append(f"Keyword density ({density}%) is too high - potential keyword stuffing")
            suggestions.append("Reduce keyword usage to avoid over-optimization penalty")
            return False
        return True

    def _check_heading_structure(
        self,
        sections: list,
        issues: list,
        suggestions: list,
    ) -> bool:
        """Check heading hierarchy and structure."""
        valid = True

        # Count H2 headings
        h2_count = sum(1 for s in sections if s.level == 2)
        if h2_count < self.MIN_H2_HEADINGS:
            issues.append(f"Only {h2_count} H2 headings - need at least {self.MIN_H2_HEADINGS}")
            suggestions.append("Add more H2 sections to improve content structure")
            valid = False

        # Check for proper hierarchy (no H3 without preceding H2)
        last_level = 1
        for section in sections:
            if section.level > last_level + 1:
                issues.append(f"Heading hierarchy jump from H{last_level} to H{section.level}")
                suggestions.append("Ensure proper heading hierarchy (H1 -> H2 -> H3)")
                valid = False
                break
            last_level = section.level

        return valid

    def _check_keyword_in_intro(
        self,
        sections: list,
        keyword: str,
        issues: list,
        suggestions: list,
    ) -> bool:
        """Check if primary keyword appears in introduction."""
        if not sections:
            return False

        first_section_content = sections[0].content.lower()
        first_200_words = " ".join(first_section_content.split()[:200])

        if keyword.lower() not in first_200_words:
            issues.append("Primary keyword not found in first 200 words")
            suggestions.append("Include the primary keyword in the introduction")
            return False
        return True

    def _check_internal_links(
        self,
        internal_links: list,
        issues: list,
        suggestions: list,
    ) -> bool:
        """Check internal linking suggestions."""
        if len(internal_links) < self.MIN_INTERNAL_LINKS:
            issues.append(
                f"Only {len(internal_links)} internal link suggestions - "
                f"recommend at least {self.MIN_INTERNAL_LINKS}"
            )
            suggestions.append("Add more internal linking opportunities")
            return False
        return True

    def _check_external_refs(
        self,
        external_refs: list,
        issues: list,
        suggestions: list,
    ) -> bool:
        """Check external reference suggestions."""
        if len(external_refs) < self.MIN_EXTERNAL_REFS:
            issues.append("No external references - content may lack credibility signals")
            suggestions.append("Add citations to authoritative external sources")
            return False
        return True

    def _check_content_uniqueness(
        self,
        sections: list,
        issues: list,
        suggestions: list,
    ) -> bool:
        """Basic check for content uniqueness indicators."""
        # Check for repetitive phrases
        all_content = " ".join(s.content for s in sections).lower()
        words = all_content.split()

        # Look for excessive repetition of 4-word phrases
        phrases = []
        for i in range(len(words) - 3):
            phrase = " ".join(words[i : i + 4])
            phrases.append(phrase)

        phrase_counts = {}
        for phrase in phrases:
            phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1

        # Flag if any phrase appears more than 3 times
        repetitive = [p for p, c in phrase_counts.items() if c > 3]
        if len(repetitive) > 5:
            issues.append("Content contains repetitive phrases")
            suggestions.append("Vary language and sentence structure more")
            return False

        return True


