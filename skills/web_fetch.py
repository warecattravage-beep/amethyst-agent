"""
✦ Web Fetch Skill — Read content from URLs.
"""
from __future__ import annotations

import logging
from typing import Any

from core.skill import Skill

log = logging.getLogger("onyx.skill.web_fetch")


class WebFetchSkill(Skill):
    """Fetch and extract readable content from web pages."""

    def __init__(self, config: dict):
        super().__init__("web_fetch", config)

    async def run(self, context: dict[str, Any], **kwargs) -> str:
        """Fetch a URL. Provide 'url' in kwargs."""
        import httpx
        url = kwargs.get("url", "")
        if not url:
            return "No URL provided."

        try:
            async with httpx.AsyncClient(timeout=20, follow_redirects=True) as c:
                r = await c.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (compatible; OnyxAgent/1.0)"
                })
                if r.status_code != 200:
                    return f"Error: HTTP {r.status_code}"

                # Simple text extraction
                import re
                text = r.text

                # Try to extract from common text containers
                # Strip scripts and styles
                text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
                text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)

                # Extract title
                title_match = re.search(r'<title[^>]*>(.*?)</title>', text, re.DOTALL)
                title = title_match.group(1).strip() if title_match else ""

                # Get visible text
                text = re.sub(r'<[^>]+>', ' ', text)
                text = re.sub(r'\s+', ' ', text).strip()

                # Truncate to reasonable size
                if len(text) > 8000:
                    text = text[:8000] + "\n\n[...truncated]"

                result = f"**URL:** {url}\n"
                if title:
                    result += f"**Title:** {title}\n"
                result += f"\n{text}"

                return result

        except httpx.TimeoutException:
            return f"Error: request timed out for {url}"
        except Exception as e:
            return f"Error fetching {url}: {e}"
