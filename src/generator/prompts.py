"""Prompt templates for AI-generated newsletter sections."""

SYSTEM_PROMPT = (
    "You are a newsletter writer for the OpenClaw project, an open-source personal "
    "AI assistant with 170k+ GitHub stars. Write engaging, concise newsletter content "
    "in clean HTML format. Use h3 for sub-headings, p for paragraphs, ul/li for lists, "
    "and a tags for links. Do not include html/head/body tags. Keep the tone professional "
    "but approachable."
)

SECTION_PROMPTS = {
    "editorial": (
        "Write a brief, engaging editorial intro (2-3 paragraphs) summarizing the top "
        "stories in the OpenClaw ecosystem today. Highlight the most significant "
        "developments. Data: {data}"
    ),
    "releases": (
        "Summarize the latest OpenClaw release updates, version changes, and package "
        "statistics. Include version numbers, key changelog highlights, and "
        "download/install trends. Data: {data}"
    ),
    "skills": (
        "Highlight newly published or trending OpenClaw skills from ClawHub and "
        "awesome-skills lists. Describe what each skill does and why it's useful. "
        "Data: {data}"
    ),
    "tips": (
        "Generate 2-3 practical tips and tricks for OpenClaw users based on recent "
        "features and community discussions. Make them actionable with brief code "
        "examples if relevant. Data: {data}"
    ),
    "community": (
        "Summarize community highlights including notable GitHub discussions, Reddit "
        "threads, Discord conversations, and contributor spotlights. Data: {data}"
    ),
    "social": (
        "Summarize notable social media mentions of OpenClaw from Twitter, LinkedIn, "
        "YouTube, and Moltbook. Include key quotes or insights. Data: {data}"
    ),
    "ecosystem": (
        "Report on the OpenClaw ecosystem including new services on Claw360, launches "
        "on ClawHunt, marketplace updates, and competitor comparisons. Data: {data}"
    ),
    "events": (
        "List upcoming events, meetups, hackathons, and conferences related to OpenClaw "
        "or AI assistants. Include dates, locations, and registration links. Data: {data}"
    ),
    "press": (
        "Summarize press coverage of OpenClaw from tech media including Hacker News "
        "discussions, Dev.to articles, Medium posts, Substack newsletters, and news "
        "outlets. Data: {data}"
    ),
    "research": (
        "Summarize recent academic research and papers related to OpenClaw, AI "
        "assistants, or relevant AI agent topics from ArXiv, CACM, and Scientific "
        "American. Data: {data}"
    ),
    "security": (
        "Report on security advisories, best practices, and security-related analysis "
        "relevant to OpenClaw and AI assistants. Data: {data}"
    ),
    "resources": (
        "Compile useful resources including new blog posts, documentation updates, "
        "tutorials, and Wikipedia edits related to OpenClaw. Data: {data}"
    ),
}
