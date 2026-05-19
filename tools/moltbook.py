"""
✦ Moltbook — Social network for AI agents.
Post, comment, upvote, browse feed, and manage your profile.
"""

from __future__ import annotations

import logging
import os

from tools import register_tool

log = logging.getLogger("onyx.tool.moltbook")

API_BASE = "https://www.moltbook.com/api/v1"


def _api_key() -> str:
    """Get Moltbook API key from environment."""
    return os.environ.get("MOLTBOOK_API_KEY") or os.environ.get("MOLTBOOK_KEY") or ""


async def _api(method: str, path: str, data: dict = None) -> str:
    """Make an authenticated request to the Moltbook API."""
    import httpx

    key = _api_key()
    if not key:
        return "Error: MOLTBOOK_API_KEY not set. Set it in your environment."

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    url = f"{API_BASE}{path}"

    async with httpx.AsyncClient(timeout=20) as client:
        try:
            if method == "GET":
                r = await client.get(url, headers=headers)
            elif method == "POST":
                r = await client.post(url, headers=headers, json=data or {})
            elif method == "DELETE":
                r = await client.delete(url, headers=headers)
            elif method == "PATCH":
                r = await client.patch(url, headers=headers, json=data or {})
            else:
                return f"Error: unsupported method {method}"

            if r.status_code == 429:
                return "Rate limited. Try again in a minute."
            if r.status_code >= 500:
                return f"Moltbook server error ({r.status_code}). Try again later."

            # Truncate very long responses
            text = r.text
            if len(text) > 2500:
                text = text[:2500] + "\n...(truncated)"
            return text

        except httpx.ConnectError:
            return "Error: cannot reach Moltbook (www.moltbook.com). Check your internet."
        except httpx.TimeoutException:
            return "Error: Moltbook request timed out."
        except Exception as e:
            return f"Error: {e}"


# ── Tool handlers ───────────────────────────────────────────────────


async def _feed_handler(args: dict) -> str:
    """Browse the Moltbook feed."""
    sort = args.get("sort", "hot")
    limit = min(args.get("limit", 25), 50)
    cursor = args.get("cursor", "")
    path = f"/posts?sort={sort}&limit={limit}"
    if cursor:
        path += f"&cursor={cursor}"
    result = await _api("GET", path)
    return f"Moltbook feed ({sort}):\n{result}"


async def _post_handler(args: dict) -> str:
    """Create a post on Moltbook."""
    payload = {
        "submolt_name": args["submolt"],
        "title": args["title"],
    }
    if args.get("content"):
        payload["content"] = args["content"]
    if args.get("url"):
        payload["url"] = args["url"]
        payload["type"] = "link"

    result = await _api("POST", "/posts", payload)
    return f"Post result:\n{result}"


async def _comment_handler(args: dict) -> str:
    """Comment on a post."""
    payload = {"content": args["content"]}
    if args.get("parent_id"):
        payload["parent_id"] = args["parent_id"]

    result = await _api("POST", f"/posts/{args['post_id']}/comments", payload)
    return f"Comment result:\n{result}"


async def _upvote_handler(args: dict) -> str:
    """Upvote a post or comment."""
    obj_type = args.get("type", "post")
    obj_id = args["id"]
    result = await _api("POST", f"/{obj_type}s/{obj_id}/upvote")
    return f"Upvote result: {result[:500]}"


async def _profile_handler(args: dict) -> str:
    """View your or another agent's profile."""
    name = args.get("name", "")
    if name:
        result = await _api("GET", f"/agents/profile?name={name}")
    else:
        result = await _api("GET", "/agents/me")
    return f"Profile:\n{result}"


async def _search_handler(args: dict) -> str:
    """Search Moltbook."""
    query = args["query"]
    limit = min(args.get("limit", 10), 25)
    result = await _api("GET", f"/search?q={query}&type=content&limit={limit}")
    return f"Search results for '{query}':\n{result}"


async def _submolts_handler(args: dict) -> str:
    """List submolts or view a specific submolt."""
    name = args.get("name", "")
    if name:
        result = await _api("GET", f"/submolts/{name}")
    else:
        result = await _api("GET", "/submolts?limit=25")
    return f"Submolts:\n{result[:2000]}"


# ── Register tools ─────────────────────────────────────────────────

for tool_name, description, params, handler in [
    (
        "moltbook_feed",
        "Browse the Moltbook social feed. Shows recent posts. Sort options: hot (popular), new (recent), top (all-time best), rising (trending). Use cursor for pagination.",
        {
            "sort": {
                "type": "string",
                "enum": ["hot", "new", "top", "rising"],
                "description": "Sort order (default: hot)",
            },
            "limit": {
                "type": "integer",
                "description": "Number of posts (max 50)",
            },
            "cursor": {
                "type": "string",
                "description": "Pagination cursor from previous response",
            },
        },
        _feed_handler,
    ),
    (
        "moltbook_post",
        "Create a post on Moltbook in a specific submolt (community). You need a submolt_name (e.g. 'general', 'aithoughts').",
        {
            "submolt": {
                "type": "string",
                "description": "Community name to post in (e.g. general, aithoughts)",
            },
            "title": {
                "type": "string",
                "description": "Post title (max 300 chars)",
            },
            "content": {
                "type": "string",
                "description": "Post body text (optional)",
            },
            "url": {
                "type": "string",
                "description": "URL for link posts (optional)",
            },
        },
        _post_handler,
    ),
    (
        "moltbook_comment",
        "Comment on a Moltbook post. You can reply to an existing comment by providing parent_id.",
        {
            "post_id": {
                "type": "string",
                "description": "ID of the post to comment on",
            },
            "content": {
                "type": "string",
                "description": "Comment text",
            },
            "parent_id": {
                "type": "string",
                "description": "Reply to a specific comment (optional)",
            },
        },
        _comment_handler,
    ),
    (
        "moltbook_upvote",
        "Upvote a post or comment on Moltbook.",
        {
            "id": {
                "type": "string",
                "description": "ID of the post or comment to upvote",
            },
            "type": {
                "type": "string",
                "enum": ["post", "comment"],
                "description": "Type of item to upvote",
            },
        },
        _upvote_handler,
    ),
    (
        "moltbook_profile",
        "View your Moltbook profile or another agent's profile. Omit name to see your own.",
        {
            "name": {
                "type": "string",
                "description": "Agent name to look up (omit for your own profile)",
            },
        },
        _profile_handler,
    ),
    (
        "moltbook_search",
        "Search Moltbook for posts and comments matching a query.",
        {
            "query": {
                "type": "string",
                "description": "Search query",
            },
            "limit": {
                "type": "integer",
                "description": "Max results (max 25)",
            },
        },
        _search_handler,
    ),
    (
        "moltbook_submolts",
        "List available submolts (communities) or view details of a specific one.",
        {
            "name": {
                "type": "string",
                "description": "Submolt name to view (omit to list all)",
            },
        },
        _submolts_handler,
    ),
]:
    register_tool(tool_name, {
        "type": "function",
        "function": {
            "name": tool_name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": params,
                "required": [k for k, v in params.items() if k in {
                    "submolt", "title", "post_id", "content", "id", "query",
                }],
            },
        },
    }, handler)
