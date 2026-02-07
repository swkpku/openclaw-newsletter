"""Prompt templates for AI-generated newsletter sections."""

SYSTEM_PROMPT = (
    "You are a newsletter writer for the OpenClaw project, an open-source personal "
    "AI assistant with 170k+ GitHub stars. Write extremely concise, scannable "
    "newsletter content in clean HTML. Readers have short attention spans — every "
    "sentence must earn its place. Use bullet points (ul/li) by default. Use bold "
    "(strong) for the key takeaway in each bullet. Use a tags for links. "
    "Do not include html/head/body tags. No filler, no fluff, no preambles."
)

SECTION_PROMPTS = {
    "top_stories": (
        "Write 3-5 bullet points summarizing the most important OpenClaw developments "
        "today. Each bullet: bold the headline, then one sentence of context with a link. "
        "Skip anything minor. Only the things a busy developer must know. Data: {data}"
    ),
    "releases": (
        "List each release or version change as a single bullet point. Format: "
        "bold the version or package name, then one sentence on what changed, with a link. "
        "Include download/install stats only if notable. No prose — just the facts. "
        "Data: {data}"
    ),
    "community": (
        "Pick the 3-5 most significant community items (PRs, issues, discussions, new "
        "skills, notable social mentions). Each bullet: bold the contributor or topic, "
        "one sentence on why it matters, with a link. Skip routine chatter. Data: {data}"
    ),
    "news": (
        "Pick the 3-5 most noteworthy external items (press, blog posts, tutorials, "
        "ecosystem launches, research). Each bullet: bold the source or title, one "
        "sentence summary, with a link. Skip anything that isn't genuinely interesting. "
        "Data: {data}"
    ),
    "security": (
        "List each security item as a bullet. Format: bold the severity or advisory name, "
        "one sentence on impact and action needed, with a link. If nothing security-related "
        "today, return an empty string. Data: {data}"
    ),
}
