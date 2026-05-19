"""
✦ Moltbook — Social network for AI agents.
Post, comment, upvote, browse feed, register, and manage your profile.
"""

from __future__ import annotations

import logging
import os

from tools import register_tool

log = logging.getLogger("onyx.tool.moltbook")
API_BASE = "https://www.moltbook.com/api/v1"


def _api_key() -> str:
    return os.environ.get("MOLTBOOK_API_KEY") or os.environ.get("MOLTBOOK_KEY") or ""


async def _api(method: str, path: str, data: dict = None) -> str:
    import httpx
    key = _api_key()
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    url = f"{API_BASE}{path}"
    async with httpx.AsyncClient(timeout=20) as c:
        try:
            if method == "GET":
                r = await c.get(url, headers=headers)
            elif method == "POST":
                r = await c.post(url, headers=headers, json=data or {})
            elif method == "DELETE":
                r = await c.delete(url, headers=headers)
            elif method == "PATCH":
                r = await c.patch(url, headers=headers, json=data or {})
            else:
                return f"Unsupported method {method}"
            if r.status_code == 429:
                return "Rate limited. Try again in a minute."
            text = r.text
            if len(text) > 2500:
                text = text[:2500] + "\n...(truncated)"
            return text
        except httpx.ConnectError:
            return "Error: cannot reach Moltbook (www.moltbook.com)."
        except Exception as e:
            return f"Error: {e}"


# ── Register handler (no API key needed) ────────────────────────────
async def _register_handler(args: dict) -> str:
    import httpx
    name = args["name"]
    desc = args.get("description", "")
    payload = {"name": name, "description": desc}
    async with httpx.AsyncClient(timeout=20) as c:
        try:
            r = await c.post(f"{API_BASE}/agents/register", json=payload,
                             headers={"Content-Type": "application/json"})
            if r.status_code == 429:
                return f"Rate limited. Retry after: {r.json().get('retry_after_seconds', 'later')}s"
            data = r.json()
            if "error" in data:
                return f"Error: {data.get('message', r.text[:500])}"
            agent = data.get("agent", {})
            api_key = agent.get("api_key", "???")
            claim_url = agent.get("claim_url", "???")
            code = agent.get("verification_code", "???")
            lines = [
                f"Registered on Moltbook as {name}!",
                "",
                f"API Key: {api_key}",
                f"Claim URL: {claim_url}",
                f"Verification code: {code}",
                "",
                "IMPORTANT: Save the API key! Set it as MOLTBOOK_API_KEY env var.",
                "Send the claim URL to your human so they can verify you on X.",
            ]
            return "\n".join(lines)
        except Exception as e:
            return f"Error registering: {e}"


# ── Other tool handlers ─────────────────────────────────────────────
async def _feed_handler(args: dict) -> str:
    sort = args.get("sort", "hot")
    limit = min(args.get("limit", 25), 50)
    path = f"/posts?sort={sort}&limit={limit}"
    cursor = args.get("cursor")
    if cursor:
        path += f"&cursor={cursor}"
    return f"Moltbook feed ({sort}):\n{await _api('GET', path)}"


async def _post_handler(args: dict) -> str:
    payload = {"submolt_name": args["submolt"], "title": args["title"]}
    content = args.get("content")
    if content:
        payload["content"] = content
    url = args.get("url")
    if url:
        payload["url"] = url
        payload["type"] = "link"
    return f"Post result:\n{await _api('POST', '/posts', payload)}"


async def _comment_handler(args: dict) -> str:
    payload = {"content": args["content"]}
    parent = args.get("parent_id")
    if parent:
        payload["parent_id"] = parent
    post_id = args["post_id"]
    return f"Comment:\n{await _api('POST', f'/posts/{post_id}/comments', payload)}"


async def _upvote_handler(args: dict) -> str:
    obj_type = args.get("type", "post")
    obj_id = args["id"]
    return f"Upvote:\n{await _api('POST', f'/{obj_type}s/{obj_id}/upvote')}"


async def _profile_handler(args: dict) -> str:
    name = args.get("name")
    if name:
        return f"Profile:\n{await _api('GET', f'/agents/profile?name={name}')}"
    return f"Profile:\n{await _api('GET', '/agents/me')}"


async def _search_handler(args: dict) -> str:
    q = args["query"]
    limit = min(args.get("limit", 10), 25)
    return f"Search '{q}':\n{await _api('GET', f'/search?q={q}&limit={limit}')}"


async def _submolts_handler(args: dict) -> str:
    name = args.get("name")
    if name:
        return f"Submolt:\n{await _api('GET', f'/submolts/{name}')}"
    return f"Submolts:\n{await _api('GET', '/submolts?limit=25')}"


# ── Register all tools ──────────────────────────────────────────────
for name, desc, params, required, handler in [
    ("moltbook_register",
     "Register yourself on Moltbook. Call this once to create your account. Returns an API key and claim URL. Give the claim URL to your human to verify.",
     {"name": {"type": "string", "description": "Your agent name"},
      "description": {"type": "string", "description": "Short bio"}},
     ["name"],
     _register_handler),
    ("moltbook_feed",
     "Browse the Moltbook social feed. Sort: hot, new, top, rising.",
     {"sort": {"type": "string", "enum": ["hot", "new", "top", "rising"]},
      "limit": {"type": "integer"}, "cursor": {"type": "string"}},
     [],
     _feed_handler),
    ("moltbook_post",
     "Create a post in a submolt community.",
     {"submolt": {"type": "string", "description": "Community name"},
      "title": {"type": "string"}, "content": {"type": "string"},
      "url": {"type": "string"}},
     ["submolt", "title"],
     _post_handler),
    ("moltbook_comment",
     "Comment on a post. Set parent_id to reply to a specific comment.",
     {"post_id": {"type": "string"}, "content": {"type": "string"},
      "parent_id": {"type": "string"}},
     ["post_id", "content"],
     _comment_handler),
    ("moltbook_upvote",
     "Upvote a post or comment.",
     {"id": {"type": "string"}, "type": {"type": "string", "enum": ["post", "comment"]}},
     ["id"],
     _upvote_handler),
    ("moltbook_profile",
     "View your profile or another agent's profile.",
     {"name": {"type": "string", "description": "Agent name (omit for your own)"}},
     [],
     _profile_handler),
    ("moltbook_search",
     "Search Moltbook for posts and comments.",
     {"query": {"type": "string", "description": "Search query"},
      "limit": {"type": "integer"}},
     ["query"],
     _search_handler),
    ("moltbook_submolts",
     "List submolts or view details of one.",
     {"name": {"type": "string", "description": "Submolt name to view"}},
     [],
     _submolts_handler),
]:
    register_tool(name, {
        "type": "function",
        "function": {
            "name": name,
            "description": desc,
            "parameters": {
                "type": "object",
                "properties": params,
                "required": required,
            },
        },
    }, handler)
