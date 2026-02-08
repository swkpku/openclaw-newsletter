"""Central configuration for OpenClaw Newsletter."""

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Config:
    """Newsletter configuration loaded from environment variables."""

    # Required
    anthropic_api_key: str = ""
    github_token: str = ""

    # Optional social media keys
    twitter_bearer_token: str = ""
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "OpenClawNewsletter/1.0"
    newsapi_key: str = ""
    discord_bot_token: str = ""
    moltbook_token: str = ""

    # Optional video/events keys
    youtube_api_key: str = ""
    eventbrite_token: str = ""

    # Claude model
    claude_model: str = "claude-sonnet-4-20250514"

    # HTTP settings
    request_timeout: int = 30
    max_retries: int = 3
    retry_backoff_factor: float = 2.0

    # State management
    state_file: str = "state.json"
    max_state_entries: int = 500

    # Site
    buttondown_username: str = "openclaw-newsletter"
    buttondown_api_key: str = ""
    site_url: str = ""

    # Output
    docs_dir: str = "docs"
    templates_dir: str = "templates"
    issues_dir: str = "docs/issues"

    @classmethod
    def from_env(cls) -> "Config":
        # Load .env file if present (no dependency required)
        env_path = Path(".env")
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                value = value.strip().strip("'\"")
                os.environ.setdefault(key.strip(), value)

        return cls(
            anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
            github_token=os.environ.get("GITHUB_TOKEN", ""),
            twitter_bearer_token=os.environ.get("TWITTER_BEARER_TOKEN", ""),
            reddit_client_id=os.environ.get("REDDIT_CLIENT_ID", ""),
            reddit_client_secret=os.environ.get("REDDIT_CLIENT_SECRET", ""),
            newsapi_key=os.environ.get("NEWSAPI_KEY", ""),
            discord_bot_token=os.environ.get("DISCORD_BOT_TOKEN", ""),
            moltbook_token=os.environ.get("MOLTBOOK_TOKEN", ""),
            youtube_api_key=os.environ.get("YOUTUBE_API_KEY", ""),
            eventbrite_token=os.environ.get("EVENTBRITE_TOKEN", ""),
            buttondown_api_key=os.environ.get("BUTTONDOWN_API_KEY", ""),
        )


# --- Source Registry ---

GITHUB_OWNER = "openclaw"
GITHUB_REPO = "openclaw"
GITHUB_API_BASE = "https://api.github.com"
GITHUB_GRAPHQL = "https://api.github.com/graphql"

# ClawHub / Awesome Skills repos
CLAWHUB_OWNER = "openclaw"
CLAWHUB_REPO = "clawhub"
AWESOME_SKILLS_REPOS = [
    {"owner": "VoltAgent", "repo": "awesome-openclaw-skills"},
    {"owner": "sundial-org", "repo": "awesome-openclaw-skills"},
]

# Package registries
NPM_PACKAGE_URL = "https://registry.npmjs.org/openclaw"
HOMEBREW_API_URL = "https://formulae.brew.sh/api/formula/openclaw-cli.json"
DOCKER_HUB_URL = "https://hub.docker.com/v2/repositories/openclaw/openclaw"
VSCODE_MARKETPLACE_URL = (
    "https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery"
)
VSCODE_EXTENSION_NAME = "openclaw.openclaw-vscode"
HUGGINGFACE_API_URL = "https://huggingface.co/api"
DIGITALOCEAN_URL = "https://marketplace.digitalocean.com/apps/openclaw"

# Official web sources
OFFICIAL_BLOG_URL = "https://openclaw.ai/blog"
OFFICIAL_BLOG_RSS = "https://openclaw.ai/blog/rss.xml"
SHOWCASE_URL = "https://openclaw.ai/showcase"
SHOUTOUTS_URL = "https://openclaw.ai/shoutouts"
DOCS_URL = "https://docs.openclaw.ai"
LEARNCLAW_URL = "https://learnclaw.ai/changelog"

# Tech media
HACKERNEWS_API_URL = "https://hn.algolia.com/api/v1/search"
DEVTO_API_URL = "https://dev.to/api/articles"
MEDIUM_RSS_URL = "https://medium.com/feed/tag/openclaw"
LOBSTERS_RSS_URL = "https://lobste.rs/rss"
CACM_RSS_URL = "https://cacm.acm.org/feed"
SCIENTIFIC_AMERICAN_RSS = "https://www.scientificamerican.com/feed/"
TLDR_URL = "https://tldr.tech"

SUBSTACK_FEEDS = [
    "https://simonwillison.substack.com/feed",
    "https://thealgorithmicbridge.substack.com/feed",
    "https://aitidbits.substack.com/feed",
    "https://bensbites.beehiiv.com/feed",
    "https://thesequence.substack.com/feed",
    "https://importai.substack.com/feed",
    "https://lastweekinai.substack.com/feed",
    "https://theaiedge.substack.com/feed",
]

# Ecosystem platforms
CLAW360_URL = "https://claw360.io"
CLAWHUNT_SPACE_URL = "https://clawhunt.space"
CLAWHUNT_SH_URL = "https://clawhunt.sh"
ALTERNATIVETO_URL = "https://alternativeto.net/software/clawdbot"
WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"
WIKIPEDIA_ARTICLE = "OpenClaw_(software)"
PRODUCT_HUNT_URL = "https://www.producthunt.com/products/openclaw"
STACKOVERFLOW_API_URL = "https://api.stackexchange.com/2.3"
G2_LEARNING_URL = "https://learn.g2.com/feed"

# Security & Research
SECURITY_RSS_FEEDS = [
    "https://www.crowdstrike.com/blog/feed",
    "https://www.bitdefender.com/blog/api/rss/labs/",
    "https://feeds.trendmicro.com/TrendMicroResearch",
]
ARXIV_API_URL = "https://export.arxiv.org/api/query"

# Social media
TWITTER_API_URL = "https://api.twitter.com/2"
REDDIT_SUBREDDITS = ["LocalLLM", "artificial", "programming"]
DISCORD_GUILD_ID = ""
MOLTBOOK_API_URL = "https://moltbook.com/api/v1"

# Video & Events
YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3"
EVENTBRITE_API_URL = "https://www.eventbriteapi.com/v3"

# NewsAPI
NEWSAPI_URL = "https://newsapi.org/v2/everything"
NEWSAPI_DOMAINS = "techcrunch.com,venturebeat.com,wired.com,theverge.com,arstechnica.com"

# Search keywords used across multiple collectors
SEARCH_KEYWORDS = ["openclaw", "open claw", "claw ai assistant"]

# Newsletter section definitions — focused, scannable daily briefing
SECTIONS = [
    {"id": "top_stories", "title": "Top Stories"},
    {"id": "trending_x", "title": "Trending on X"},
    {"id": "releases", "title": "Releases"},
    {"id": "community", "title": "Community"},
    {"id": "news", "title": "News"},
    {"id": "security", "title": "Security"},
]

# Mapping: collector name -> newsletter section
# All collectors still run; output is consolidated into 5 focused sections.
COLLECTOR_SECTION_MAP = {
    # Releases
    "github_releases": "releases",
    "github_stats": "releases",
    "npm_registry": "releases",
    "homebrew_stats": "releases",
    "docker_hub": "releases",
    "vscode_marketplace": "releases",
    # Community (GitHub activity, skills, discussions, social)
    "github_activity": "community",
    "github_sponsors": "community",
    "clawhub_skills": "community",
    "awesome_skills": "community",
    "showcase": "community",
    "stackoverflow": "community",
    "reddit": "community",
    "discord_feed": "community",
    "twitter": "trending_x",
    "linkedin_news": "community",
    "moltbook": "community",
    "youtube": "community",
    # News (press, blogs, research, ecosystem, events, resources)
    "hackernews": "news",
    "devto": "news",
    "medium": "news",
    "lobsters": "news",
    "substack": "news",
    "tldr_news": "news",
    "tech_news": "news",
    "blog_feed": "news",
    "docs_updates": "news",
    "learnclaw": "news",
    "academic_news": "news",
    "arxiv_papers": "news",
    "claw360": "news",
    "clawhunt": "news",
    "alternativeto": "news",
    "wikipedia": "news",
    "product_hunt": "news",
    "g2_learning": "news",
    "huggingface": "news",
    "digitalocean": "news",
    "events": "news",
    # Security (standalone — too important to bury)
    "security_feeds": "security",
}
