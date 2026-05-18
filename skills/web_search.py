"""
✦ Web Search Skill - Search the internet.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from core.skill import Skill

log = logging.getLogger("onyx.skill.web_search")


class WebSearchSkill(Skill):
    """Search the web and return results."""

    def __init__(self, config: dict):
        super().__init__("web_search", config)
        self.api_key = config.get("api_key", "")

    async def run(self, context: dict[str, Any], **kwargs) -> str:
        """Search the web. Provide 'query' in kwargs."""
        query = kwargs.get("query", "")
        if not query:
            return "No search query provided."
        results = await self._search(query)
        return self._format_results(results)

    async def _search(self, query: str) -> list[dict]:
        """Perform web search."""
        if self.api_key:
            return await self._brave_search(query)
        return await self._duckduckgo_search(query)

    async def _brave_search(self, query: str) -> list[dict]:
        """Search via Brave Search API."""
        import httpx
        try:
            async with httpx.AsyncClient() as c:
                r = await c.get(
                    "https://api.search.brave.com/res/v1/web/search",
                    params={"q": query, "count": 5},
                    headers={"X-Subscription-Token": self.api_key},
                    timeout=15,
                )
                if r.status_code == 200:
                    results = r.json().get("web", {}).get("results", [])
                    return [
                        {"title": res.get("title", ""), "url": res.get("url", ""),
                         "snippet": res.get("description", "")}
                        for res in results
                    ]
        except Exception as e:
            log.warning("Brave search failed: %s", e)
        return []

    async def _duckduckgo_search(self, query: str) -> list[dict]:
        """Search via DuckDuckGo (no API key needed)."""
        import httpx
        try:
            async with httpx.AsyncClient() as c:
                r = await c.get(
                    "https://lite.duckduckgo.com/lite/",
                    params={"q": query},
                    timeout=15,
                )
                if r.status_code == 200:
                    import re
                    results = []
                    links = re.findall(
                        r'class="result-link">\s*<a[^>]*href="([^"]*)"[^>]*>([^<]+)',
                        r.text
                    )
                    snippets = re.findall(
                        r'class="result-snippet">([^<]+)',
                        r.text
                    )
                    for i, (url, title) in enumerate(links[:5]):
                        snippet = snippets[i] if i < len(snippets) else ""
                        results.append({"title": title, "url": url, "snippet": snippet.strip()})
                    return results
        except Exception as e:
            log.warning("DuckDuckGo search failed: %s", e)
        return []

    def _format_results(self, results: list[dict]) -> str:
        if not results:
            return "No search results found."
        lines = ["**Search Results:**"]
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. [{r.get('title', '?')}]({r.get('url', '#')})")
            if r.get("snippet"):
                lines.append(f"   _{r['snippet'][:200]}_")
        return "\n".join(lines)
