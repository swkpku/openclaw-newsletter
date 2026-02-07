# OpenClaw Newsletter

Automated daily newsletter for the [OpenClaw](https://github.com/openclaw/openclaw) project (170k+ GitHub stars). Collects content from 46 sources, generates editorial summaries with Claude, and publishes a styled newsletter to GitHub Pages.

## Features

- **46 content sources** across GitHub, package registries, blogs, social media, research, and more
- **AI-generated summaries** using Anthropic's Claude for each newsletter section
- **12 newsletter sections** covering releases, skills, community, press, research, security, and more
- **Dark mode support** with responsive CSS
- **GitHub Pages deployment** with automatic daily runs via GitHub Actions
- **Deduplication** via persistent state tracking across runs
- **Graceful degradation** -- missing API keys simply skip those collectors

## Quick Start

```bash
git clone https://github.com/openclaw/openclaw-newsletter.git
cd openclaw-newsletter
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key_here
python -m src.main
```

The generated newsletter will be written to `docs/index.html`.

## Content Sources (46)

### Tier 1 -- GitHub (no API key required)

| # | Source | Description |
|---|--------|-------------|
| 1 | GitHub Releases | Latest releases from openclaw/openclaw |
| 2 | GitHub Activity | Recent issues, PRs, and discussions |
| 3 | GitHub Stats | Star count, fork count, contributor activity |
| 4 | GitHub Sponsors | New and notable sponsors |

### Tier 2 -- Package Registries (no API key required)

| # | Source | Description |
|---|--------|-------------|
| 5 | npm Registry | Download stats and version info |
| 6 | Homebrew Stats | Install counts from Homebrew |
| 7 | Docker Hub | Pull counts and image tags |
| 8 | VS Code Marketplace | Extension installs and ratings |
| 9 | HuggingFace | Models and spaces using OpenClaw |
| 10 | DigitalOcean Marketplace | Marketplace listing activity |

### Tier 3 -- Official Web Sources (no API key required)

| # | Source | Description |
|---|--------|-------------|
| 11 | Official Blog (RSS) | Posts from openclaw.ai/blog |
| 12 | Showcase | Community projects on openclaw.ai/showcase |
| 13 | Docs Updates | Recent changes to docs.openclaw.ai |
| 14 | LearnClaw Changelog | Updates from learnclaw.ai |
| 15 | ClawHub Skills | New skills on ClawHub |
| 16 | Awesome Skills | Community-curated skill lists |

### Tier 4 -- Tech Media (no API key required)

| # | Source | Description |
|---|--------|-------------|
| 17 | Hacker News | Mentions on HN via Algolia API |
| 18 | Dev.to | Tagged articles on Dev.to |
| 19 | Medium | Tagged articles via RSS |
| 20 | Lobsters | Mentions on lobste.rs |
| 21 | Academic News (CACM, SciAm) | Coverage in academic outlets |
| 22 | Substack | 8 AI-focused Substack newsletters |
| 23 | TLDR Newsletter | Mentions in TLDR daily digest |

### Tier 5 -- Ecosystem Platforms (no API key required)

| # | Source | Description |
|---|--------|-------------|
| 24 | Claw360 | Listings on claw360.io |
| 25 | ClawHunt (space + sh) | Listings on clawhunt.space and clawhunt.sh |
| 26 | AlternativeTo | Comparisons on alternativeto.net |
| 27 | Wikipedia | Edits to the OpenClaw Wikipedia article |
| 28 | Product Hunt | Activity on Product Hunt |
| 29 | Stack Overflow | Questions tagged with OpenClaw |
| 30 | G2 Learning | Articles from G2 learning hub |

### Tier 6 -- Security & Research (no API key required)

| # | Source | Description |
|---|--------|-------------|
| 31 | Security Feeds | CrowdStrike, Bitdefender, Trend Micro RSS |
| 32 | arXiv Papers | Recent papers mentioning OpenClaw |

### Tier 7 -- Social Media (API keys required)

| # | Source | Description | Key Required |
|---|--------|-------------|--------------|
| 33 | Twitter/X | Mentions and hashtags | TWITTER_BEARER_TOKEN |
| 34 | Reddit | Posts from r/LocalLLM, r/artificial, r/programming | REDDIT_CLIENT_ID + SECRET |
| 35 | LinkedIn News | Professional mentions | (scraped) |
| 36 | Discord | Messages from OpenClaw Discord | DISCORD_BOT_TOKEN |
| 37 | Moltbook | Posts on Moltbook | MOLTBOOK_TOKEN |

### Tier 8 -- Video & Events (API keys required)

| # | Source | Description | Key Required |
|---|--------|-------------|--------------|
| 38 | YouTube | Videos mentioning OpenClaw | YOUTUBE_API_KEY |
| 39 | Eventbrite | Upcoming events and meetups | EVENTBRITE_TOKEN |

### Tier 9 -- News Aggregators (API key required)

| # | Source | Description | Key Required |
|---|--------|-------------|--------------|
| 40 | NewsAPI | TechCrunch, VentureBeat, Wired, The Verge, Ars Technica | NEWSAPI_KEY |

*Sources 41-46 include LinkedIn scraping, Shoutouts page, and additional cross-referenced feeds from the collectors above.*

## API Keys

| Key | Required | Description |
|-----|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Powers AI-generated summaries via Claude |
| `GITHUB_TOKEN` | Auto | Auto-provided in GitHub Actions; increases rate limits locally |
| `TWITTER_BEARER_TOKEN` | No | Twitter/X API v2 bearer token |
| `REDDIT_CLIENT_ID` | No | Reddit API client ID |
| `REDDIT_CLIENT_SECRET` | No | Reddit API client secret |
| `NEWSAPI_KEY` | No | NewsAPI.org API key |
| `DISCORD_BOT_TOKEN` | No | Discord bot token for guild access |
| `MOLTBOOK_TOKEN` | No | Moltbook API token |
| `YOUTUBE_API_KEY` | No | YouTube Data API v3 key |
| `EVENTBRITE_TOKEN` | No | Eventbrite API token |

Copy `.env.example` to `.env` and fill in your keys.

## Architecture

```
                         +------------------+
                         |    src/main.py   |
                         |  (orchestrator)  |
                         +--------+---------+
                                  |
                  +---------------+---------------+
                  |                               |
        +---------+---------+          +----------+----------+
        |  src/collectors/  |          |  src/state/         |
        |  46 collectors    |          |  state_manager.py   |
        |  (base.py +       |          |  (deduplication)    |
        |   one per source) |          +----------+----------+
        +---------+---------+                     |
                  |                               |
                  v                               v
        +---------+---------+          +----------+----------+
        |  src/models/      |          |  state.json         |
        |  data_models.py   |          |  (persistent state) |
        |  (ContentItem,    |          +---------------------+
        |   NewsletterIssue)|
        +---------+---------+
                  |
                  v
        +---------+---------+
        |  src/generator/   |
        |  (Claude AI)      |
        |  section summaries|
        +---------+---------+
                  |
                  v
        +---------+---------+
        |  src/renderer/    |
        |  Jinja2 templates |-----> docs/index.html
        |  + CSS            |-----> docs/issues/YYYY-MM-DD.html
        +---------+---------+
```

**Data flow:** Collectors gather content -> State manager deduplicates -> Generator creates AI summaries -> Renderer produces HTML via Jinja2 templates -> Output to `docs/` for GitHub Pages.

## Newsletter Sections

| # | Section | Description |
|---|---------|-------------|
| 1 | Editorial Intro | AI-generated overview of the day's highlights |
| 2 | Release Updates | New versions, package stats, distribution updates |
| 3 | New Skills Spotlight | Newly published skills from ClawHub and community |
| 4 | Tips & Tricks | Usage tips and workflow improvements |
| 5 | Community Spotlight | Notable issues, PRs, discussions, sponsors |
| 6 | Social Buzz | Twitter, Moltbook, YouTube mentions |
| 7 | Ecosystem Watch | Third-party platforms, integrations, marketplaces |
| 8 | Events & Meetups | Upcoming events and conferences |
| 9 | In The Press | Media coverage from tech publications |
| 10 | Research & Academia | arXiv papers and academic coverage |
| 11 | Security Corner | Security-related news and advisories |
| 12 | Useful Resources | Blog posts, docs updates, tutorials |

## GitHub Actions Setup

1. Go to your repository **Settings > Secrets and variables > Actions**
2. Add `ANTHROPIC_API_KEY` as a repository secret
3. Optionally add any other API keys from the table above
4. Enable GitHub Pages from **Settings > Pages**, set source to the `docs/` folder
5. The workflow runs daily and on push to `main`

The `GITHUB_TOKEN` is automatically provided by GitHub Actions.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-collector`)
3. Add your collector in `src/collectors/` following the `BaseCollector` pattern
4. Register it in `src/config.py` under `COLLECTOR_SECTION_MAP`
5. Submit a pull request

## License

MIT
