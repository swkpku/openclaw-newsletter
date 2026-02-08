"""Main orchestrator for the OpenClaw Newsletter generator."""

import logging
import sys
from datetime import date

from src.config import Config
from src.collectors.github_releases import GitHubReleasesCollector
from src.collectors.github_activity import GitHubActivityCollector
from src.collectors.github_stats import GitHubStatsCollector
from src.collectors.github_sponsors import GitHubSponsorsCollector
from src.collectors.clawhub_skills import ClawHubSkillsCollector
from src.collectors.awesome_skills import AwesomeSkillsCollector
from src.collectors.npm_registry import NpmRegistryCollector
from src.collectors.homebrew_stats import HomebrewStatsCollector
from src.collectors.docker_hub import DockerHubCollector
from src.collectors.vscode_marketplace import VSCodeMarketplaceCollector
from src.collectors.huggingface import HuggingFaceCollector
from src.collectors.digitalocean import DigitalOceanCollector
from src.collectors.blog_feed import BlogFeedCollector
from src.collectors.showcase import ShowcaseCollector
from src.collectors.docs_updates import DocsUpdatesCollector
from src.collectors.learnclaw import LearnClawCollector
from src.collectors.hackernews import HackerNewsCollector
from src.collectors.devto import DevToCollector
from src.collectors.medium import MediumCollector
from src.collectors.lobsters import LobstersCollector
from src.collectors.academic_news import AcademicNewsCollector
from src.collectors.substack import SubstackCollector
from src.collectors.tldr_news import TldrNewsCollector
from src.collectors.claw360 import Claw360Collector
from src.collectors.clawhunt import ClawhuntCollector
from src.collectors.alternativeto import AlternativeToCollector
from src.collectors.wikipedia import WikipediaCollector
from src.collectors.product_hunt import ProductHuntCollector
from src.collectors.stackoverflow import StackOverflowCollector
from src.collectors.g2_learning import G2LearningCollector
from src.collectors.security_feeds import SecurityFeedsCollector
from src.collectors.arxiv_papers import ArxivPapersCollector
from src.collectors.twitter import TwitterCollector
from src.collectors.reddit import RedditCollector
from src.collectors.linkedin_news import LinkedInNewsCollector
from src.collectors.discord_feed import DiscordFeedCollector
from src.collectors.moltbook import MoltbookCollector
from src.collectors.youtube import YouTubeCollector
from src.collectors.events import EventsCollector
from src.collectors.tech_news import TechNewsCollector
from src.generator.content_assembler import ContentAssembler
from src.renderer.html_renderer import HTMLRenderer
from src.renderer.archive_builder import ArchiveBuilder
from src.renderer.rss_builder import RSSBuilder
from src.state.state_manager import StateManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

ALL_COLLECTORS = [
    # Tier 1: Core GitHub
    GitHubReleasesCollector,
    GitHubActivityCollector,
    GitHubStatsCollector,
    GitHubSponsorsCollector,
    ClawHubSkillsCollector,
    AwesomeSkillsCollector,
    # Tier 2: Package Registries
    NpmRegistryCollector,
    HomebrewStatsCollector,
    DockerHubCollector,
    VSCodeMarketplaceCollector,
    HuggingFaceCollector,
    DigitalOceanCollector,
    # Tier 3: Official Web
    BlogFeedCollector,
    ShowcaseCollector,
    DocsUpdatesCollector,
    LearnClawCollector,
    # Tier 4: Tech Media
    HackerNewsCollector,
    DevToCollector,
    MediumCollector,
    LobstersCollector,
    AcademicNewsCollector,
    SubstackCollector,
    TldrNewsCollector,
    # Tier 5: Ecosystem
    Claw360Collector,
    ClawhuntCollector,
    AlternativeToCollector,
    WikipediaCollector,
    ProductHuntCollector,
    StackOverflowCollector,
    G2LearningCollector,
    # Tier 6: Security & Research
    SecurityFeedsCollector,
    ArxivPapersCollector,
    # Tier 7-9: API-key sources
    TwitterCollector,
    RedditCollector,
    LinkedInNewsCollector,
    DiscordFeedCollector,
    MoltbookCollector,
    YouTubeCollector,
    EventsCollector,
    TechNewsCollector,
]


def main() -> None:
    """Run the newsletter generation pipeline."""
    config = Config.from_env()
    today = date.today().isoformat()

    logger.info(f"=== OpenClaw Newsletter Generation - {today} ===")

    # 1. Load state
    state = StateManager(config.state_file, config.max_state_entries)
    logger.info(f"State loaded. Last run: {state.last_run}. Covered items: {len(state.state['covered_items'])}")

    # 2. Collect from all sources
    logger.info(f"Running {len(ALL_COLLECTORS)} collectors...")
    results = []
    for collector_cls in ALL_COLLECTORS:
        collector = collector_cls(config)
        result = collector.run(state)
        results.append(result)

    # Count results
    total_items = sum(len(r.items) for r in results)
    available = sum(1 for r in results if not r.skipped and r.error is None)
    skipped = sum(1 for r in results if r.skipped)
    errors = sum(1 for r in results if r.error)
    logger.info(
        f"Collection complete: {total_items} items from {available} sources "
        f"({skipped} skipped, {errors} errors)"
    )

    # 3. Gate check
    if total_items == 0:
        logger.info("No new content found. Skipping issue generation.")
        state.save()
        return

    # 4-5. Categorize and generate via content assembler
    assembler = ContentAssembler(config)
    issue = assembler.assemble(results, today)
    logger.info(
        f"Issue assembled: {len(issue.active_sections)} active sections, "
        f"{issue.total_items} total items"
    )

    # 6. Render HTML
    renderer = HTMLRenderer(config)
    issue_filename = renderer.render_issue(issue)

    archive = ArchiveBuilder(config)
    archive.build()

    rss = RSSBuilder(config)
    rss.build()

    latest = archive.get_latest_issue()
    renderer.render_index(latest)

    # 7. Save state - mark all collected items as covered
    for result in results:
        state.mark_items_covered([item.id for item in result.items])
    state.save()

    logger.info(f"=== Newsletter generated: docs/issues/{issue_filename} ===")


if __name__ == "__main__":
    main()
