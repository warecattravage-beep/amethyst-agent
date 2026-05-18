"""
✦ Notion Skill - Integrate with Notion API.
Uses httpx (lazy import) for async HTTP requests.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from core.skill import Skill

log = logging.getLogger("onyx.skill.notion")

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


class NotionSkill(Skill):
    """Interact with Notion via the official API."""

    def __init__(self, config: dict):
        super().__init__("notion", config)
        self.api_key = config.get("api_key", "")
        self.database_id = config.get("database_id", "")

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION,
        }

    async def run(self, context: dict[str, Any], **kwargs) -> str:
        """Execute a Notion action.

        Args:
            action: 'list_databases', 'query', 'create_page', or 'search'
            database_id: Notion database ID (required for query, create_page)
            query: Search query string (required for search)
            properties: Dict of property values (required for create_page)

        Returns:
            Formatted result string.
        """
        action = kwargs.get("action", "").strip().lower()
        if not action:
            return "Error: No action specified."

        if not self.api_key:
            return "Error: Notion API key not configured. Set it in config."

        if action == "list_databases":
            return await self._list_databases()
        elif action == "query":
            database_id = kwargs.get("database_id", self.database_id)
            return await self._query_database(database_id)
        elif action == "create_page":
            database_id = kwargs.get("database_id", self.database_id)
            properties = kwargs.get("properties", {})
            return await self._create_page(database_id, properties)
        elif action == "search":
            query = kwargs.get("query", "")
            return await self._search(query)
        else:
            return f"Error: Unknown action '{action}'."

    async def _request(self, method: str, path: str, data: dict | None = None) -> dict:
        """Make an async HTTP request to the Notion API."""
        try:
            import httpx
        except ImportError:
            return {"error": "httpx is required. Install with: pip install httpx"}

        url = f"{NOTION_API_BASE}/{path.lstrip('/')}"
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self._headers(),
                    json=data,
                )
                if response.status_code in (200, 201):
                    return response.json()
                else:
                    try:
                        err = response.json()
                        msg = err.get("message", str(err))
                    except Exception:
                        msg = response.text[:500]
                    return {"error": f"Notion API error ({response.status_code}): {msg}"}
        except httpx.TimeoutException:
            return {"error": "Notion API request timed out"}
        except Exception as e:
            return {"error": f"Notion request failed: {e}"}

    async def _list_databases(self) -> str:
        """List all accessible databases."""
        data = await self._request("GET", "databases")
        if "error" in data:
            return f"Error: {data['error']}"

        results = data.get("results", [])
        if not results:
            return "No databases found. Ensure your integration has access."

        lines = ["**Notion Databases:**", ""]
        for db in results:
            title = "Untitled"
            title_data = db.get("title", [])
            if title_data:
                title = title_data[0].get("plain_text", "Untitled")
            db_id = db.get("id", "?")
            lines.append(f"  • **{title}** - `{db_id}`")

        return "\n".join(lines)

    async def _query_database(self, database_id: str) -> str:
        """Query a database for its pages."""
        if not database_id:
            return "Error: No database_id provided."

        data = await self._request("POST", f"databases/{database_id}/query", {})
        if "error" in data:
            return f"Error: {data['error']}"

        results = data.get("results", [])
        if not results:
            return "No pages found in this database."

        lines = [f"**Database results ({len(results)} pages):**", ""]
        for i, page in enumerate(results[:20], 1):
            # Extract page title from properties
            props = page.get("properties", {})
            title_str = str(page.get("id", "?")[:8])
            for prop_name, prop_data in props.items():
                ptype = prop_data.get("type", "")
                if ptype == "title":
                    titles = prop_data.get("title", [])
                    if titles:
                        title_str = titles[0].get("plain_text", prop_name)
                        break
                elif ptype == "rich_text":
                    texts = prop_data.get("rich_text", [])
                    if texts:
                        title_str = texts[0].get("plain_text", prop_name)
                        break
            page_id = page.get("id", "?")[:8]
            lines.append(f"  {i}. **{title_str}** - `{page_id}`")

        if len(results) > 20:
            lines.append(f"  ... and {len(results) - 20} more")

        return "\n".join(lines)

    async def _create_page(self, database_id: str, properties: dict) -> str:
        """Create a new page in a database."""
        if not database_id:
            return "Error: No database_id provided."
        if not properties:
            return "Error: No properties provided. Use a dict of property values."

        payload = {
            "parent": {"database_id": database_id},
            "properties": properties,
        }

        data = await self._request("POST", "pages", payload)
        if "error" in data:
            return f"Error: {data['error']}"

        page_id = data.get("id", "?")
        url = data.get("url", "")
        return f"✅ Page created: `{page_id}`\n{url}"

    async def _search(self, query: str) -> str:
        """Search Notion for pages, databases, etc."""
        if not query:
            return "Error: No search query provided."

        payload = {"query": query, "sort": {"direction": "descending", "timestamp": "last_edited_time"}}
        data = await self._request("POST", "search", payload)
        if "error" in data:
            return f"Error: {data['error']}"

        results = data.get("results", [])
        if not results:
            return f"No Notion results found for: _{query}_"

        lines = [f"**Notion search: _{query}_**", f"Found {len(results)} result(s):", ""]
        for i, item in enumerate(results[:10], 1):
            obj_type = item.get("object", "?")
            item_id = item.get("id", "?")[:8]
            title = "Untitled"
            if obj_type == "database":
                title_data = item.get("title", [])
                if title_data:
                    title = title_data[0].get("plain_text", "Untitled")
            elif obj_type == "page":
                props = item.get("properties", {})
                for prop_name, prop_data in props.items():
                    ptype = prop_data.get("type", "")
                    if ptype == "title":
                        titles = prop_data.get("title", [])
                        if titles:
                            title = titles[0].get("plain_text", prop_name)
                            break
            lines.append(f"  {i}. **{title}** ({obj_type}) - `{item_id}`")

        if len(results) > 10:
            lines.append(f"  ... and {len(results) - 10} more")

        return "\n".join(lines)
