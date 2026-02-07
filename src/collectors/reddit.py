"""Collector for Reddit discussions about OpenClaw."""

import logging

from src.collectors.base import BaseCollector
from src.config import REDDIT_SUBREDDITS
from src.models.data_models import ContentItem
from src.state.state_manager import StateManager

logger = logging.getLogger(__name__)


class RedditCollector(BaseCollector):
    """Fetches OpenClaw-related posts from configured subreddits using praw."""

    name = "reddit"

    def is_available(self) -> bool:
        return bool(self.config.reddit_client_id and self.config.reddit_client_secret)

    def collect(self, state: StateManager) -> list[ContentItem]:
        import praw

        reddit = praw.Reddit(
            client_id=self.config.reddit_client_id,
            client_secret=self.config.reddit_client_secret,
            user_agent=self.config.reddit_user_agent,
        )

        items: list[ContentItem] = []
        for subreddit_name in REDDIT_SUBREDDITS:
            try:
                subreddit = reddit.subreddit(subreddit_name)
                for submission in subreddit.search("openclaw", limit=10):
                    item_id = f"reddit:{submission.id}"
                    if state.is_covered(item_id):
                        continue

                    items.append(
                        ContentItem(
                            id=item_id,
                            source=self.name,
                            title=submission.title,
                            url=f"https://reddit.com{submission.permalink}",
                            description=submission.selftext[:500] if submission.selftext else "",
                            author=str(submission.author) if submission.author else "",
                            published_at="",
                            content_type="reddit_post",
                            metadata={
                                "subreddit": subreddit_name,
                                "score": submission.score,
                                "num_comments": submission.num_comments,
                                "upvote_ratio": submission.upvote_ratio,
                            },
                        )
                    )
            except Exception as e:
                logger.warning(f"Error searching r/{subreddit_name}: {e}")

        return items
