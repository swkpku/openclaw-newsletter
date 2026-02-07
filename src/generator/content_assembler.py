"""Content assembler that bridges collectors to AI generation to a NewsletterIssue."""

import logging

from src.config import Config, SECTIONS, COLLECTOR_SECTION_MAP
from src.generator.ai_writer import AIWriter
from src.models.data_models import CollectorResult, ContentItem, NewsletterSection, NewsletterIssue

logger = logging.getLogger(__name__)


class ContentAssembler:
    """Groups collected items into sections, generates AI content, and produces a NewsletterIssue."""

    def __init__(self, config: Config):
        self.config = config
        self.ai_writer = AIWriter(config)

    def assemble(self, collector_results: list[CollectorResult], issue_date: str) -> NewsletterIssue:
        """Group items into sections, generate AI content, return complete issue.

        Args:
            collector_results: Results from all collectors.
            issue_date: Date string (YYYY-MM-DD) for the newsletter issue.

        Returns:
            A fully assembled NewsletterIssue.
        """
        # 1. Group all items by section using COLLECTOR_SECTION_MAP
        section_items: dict[str, list[ContentItem]] = {}
        all_items: list[ContentItem] = []

        for result in collector_results:
            if result.error or result.skipped:
                continue
            section_id = COLLECTOR_SECTION_MAP.get(result.collector_name)
            if not section_id:
                logger.warning(
                    "No section mapping for collector '%s'; skipping %d items",
                    result.collector_name,
                    len(result.items),
                )
                continue
            section_items.setdefault(section_id, []).extend(result.items)
            all_items.extend(result.items)

        logger.info(
            "Grouped %d items into %d sections from %d collector results",
            len(all_items),
            len(section_items),
            len(collector_results),
        )

        # 2. For each section in SECTIONS, generate content
        sections: list[NewsletterSection] = []

        for section_def in SECTIONS:
            section_id = section_def["id"]
            title = section_def["title"]

            if section_id == "editorial":
                # Editorial needs AI to summarize — skip in fallback mode
                if not all_items or not self.ai_writer.is_available():
                    continue
                content_html = self.ai_writer.generate_section(section_id, all_items)
                section = NewsletterSection(
                    id=section_id,
                    title=title,
                    content_html=content_html,
                    items=[],  # Don't count editorial items to avoid duplication
                )
            else:
                items = section_items.get(section_id, [])
                if not items:
                    logger.debug("Skipping section '%s' — no items", section_id)
                    continue
                content_html = self.ai_writer.generate_section(section_id, items)
                section = NewsletterSection(
                    id=section_id,
                    title=title,
                    content_html=content_html,
                    items=items,
                )

            sections.append(section)
            logger.info("Built section '%s' with %d items", section_id, len(section.items))

        # 3. Return the complete issue
        issue = NewsletterIssue(date=issue_date, sections=sections)
        logger.info(
            "Assembled newsletter issue for %s: %d sections, %d total items",
            issue_date,
            len(issue.active_sections),
            issue.total_items,
        )
        return issue
