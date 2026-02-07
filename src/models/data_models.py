"""Data models for the OpenClaw Newsletter."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ContentItem:
    """A single piece of content collected from any source."""

    id: str  # Unique identifier for deduplication
    source: str  # Collector name (e.g., "github_releases")
    title: str
    url: str = ""
    description: str = ""
    author: str = ""
    published_at: str = ""  # ISO format string
    content_type: str = ""  # e.g., "release", "article", "discussion"
    metadata: dict = field(default_factory=dict)  # Source-specific extra data

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source,
            "title": self.title,
            "url": self.url,
            "description": self.description,
            "author": self.author,
            "published_at": self.published_at,
            "content_type": self.content_type,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ContentItem":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class CollectorResult:
    """Result from a single collector run."""

    collector_name: str
    items: list[ContentItem] = field(default_factory=list)
    error: Optional[str] = None
    skipped: bool = False  # True if collector was unavailable (missing API key)


@dataclass
class NewsletterSection:
    """A section of the newsletter."""

    id: str  # e.g., "releases", "community"
    title: str
    content_html: str = ""  # AI-generated or fallback HTML
    items: list[ContentItem] = field(default_factory=list)

    @property
    def has_content(self) -> bool:
        return bool(self.content_html) or bool(self.items)


@dataclass
class NewsletterIssue:
    """A complete newsletter issue."""

    date: str  # YYYY-MM-DD
    sections: list[NewsletterSection] = field(default_factory=list)
    generated_at: str = ""
    total_items: int = 0

    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.utcnow().isoformat()
        if not self.total_items:
            self.total_items = sum(len(s.items) for s in self.sections)

    @property
    def active_sections(self) -> list[NewsletterSection]:
        return [s for s in self.sections if s.has_content]
