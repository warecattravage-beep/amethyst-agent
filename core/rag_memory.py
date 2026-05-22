"""
✦ RAG Memory - Simple keyword-based search over past conversations.
No external dependencies; uses word matching + frequency scoring.
"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any

log = logging.getLogger("amethyst.rag_memory")

# Path to the searchable memory text file
MEMORY_FILE = "data/rag_memory.txt"

# How many entries to keep in rotation
MAX_ENTRIES = 5000


class RAGMemory:
    """Simple keyword-based RAG over conversation history.

    Stores all messages as plain text entries with timestamps,
    and provides search over them using word matching + frequency scoring.
    No embeddings or external dependencies.
    """

    def __init__(self, data_dir: str | Path = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.memory_file = self.data_dir / "rag_memory.txt"
        self.entries: list[dict] = []
        self._load()

    # ── Persistence ──

    def _load(self):
        """Load entries from the memory file."""
        if not self.memory_file.exists():
            self.entries = []
            return
        try:
            raw = self.memory_file.read_text(encoding="utf-8", errors="replace")
            lines = raw.strip().split("\n")
            self.entries = []
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if isinstance(entry, dict) and "content" in entry:
                        self.entries.append(entry)
                except json.JSONDecodeError:
                    continue
            log.info("RAG memory loaded: %d entries", len(self.entries))
        except Exception as e:
            log.warning("RAG memory load error: %s", e)
            self.entries = []

    def save(self):
        """Save entries to the memory file."""
        try:
            lines = []
            for entry in self.entries:
                lines.append(json.dumps(entry, ensure_ascii=False))
            self.memory_file.write_text("\n".join(lines), encoding="utf-8")
            log.debug("RAG memory saved: %d entries", len(self.entries))
        except Exception as e:
            log.warning("RAG memory save error: %s", e)

    # ── Adding entries ──

    def add(self, role: str, content: str, chat_id: str = ""):
        """Add a message to the searchable memory store."""
        if not content or not content.strip():
            return

        entry = {
            "role": role,
            "content": content,
            "chat_id": chat_id,
            "ts": time.time(),
        }
        self.entries.append(entry)

        # Trim to max entries
        if len(self.entries) > MAX_ENTRIES:
            self.entries = self.entries[-MAX_ENTRIES:]

        # Auto-save every 50 entries
        if len(self.entries) % 50 == 0:
            self.save()

    # ── Search ──

    def _tokenize(self, text: str) -> set[str]:
        """Split text into lowercase keyword tokens."""
        # Remove punctuation, split on whitespace
        clean = re.sub(r'[^\w\s]', ' ', text.lower())
        # Filter out very short words and common stop words
        stops = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "shall", "can",
            "to", "of", "in", "for", "on", "at", "by", "with", "from",
            "as", "into", "through", "during", "before", "after", "above",
            "below", "between", "and", "but", "or", "nor", "not", "so",
            "yet", "both", "either", "neither", "each", "every", "all",
            "no", "none", "any", "some", "such", "only", "own", "same",
            "it", "its", "this", "that", "these", "those", "i", "you",
            "he", "she", "we", "they", "me", "him", "her", "us", "them",
            "my", "your", "his", "its", "our", "their", "mine", "yours",
            "theirs", "what", "which", "who", "whom", "whose", "why",
            "how", "when", "where", "here", "there", "then", "than",
            "too", "very", "just", "about", "up", "out", "if", "while",
            "because", "until", "unless", "since", "so", "though", "although",
            "also", "well", "back", "over", "still", "even", "much",
            "off", "down", "now", "like", "get", "got", "here", "there",
        }
        return {w for w in clean.split() if len(w) > 2 and w not in stops}

    def search(self, query: str, limit: int = 5) -> list[dict]:
        """Search past memory entries for keyword matches.

        Uses simple word matching + frequency scoring (TF-style).
        Returns list of matching entries sorted by relevance, each with:
          - content: the matched text
          - role: user or assistant
          - score: relevance score (higher = better match)
          - ts: timestamp
        """
        if not query or not query.strip():
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        scored = []
        for entry in self.entries:
            content = entry.get("content", "")
            entry_tokens = self._tokenize(content)
            if not entry_tokens:
                continue

            # Count matching tokens
            matches = query_tokens & entry_tokens
            if not matches:
                continue

            # Score: (matches / query_tokens) * (matches / entry_tokens)
            # This gives higher weight to entries that match more of the query
            # AND have a higher density of matches
            recall = len(matches) / len(query_tokens)
            precision = len(matches) / len(entry_tokens)
            score = (recall + precision) / 2

            # Bonus for exact phrase matches
            query_lower = query.lower()
            content_lower = content.lower()
            if query_lower in content_lower:
                score += 0.3

            scored.append({
                "content": content,
                "role": entry.get("role", "user"),
                "chat_id": entry.get("chat_id", ""),
                "score": round(score, 4),
                "ts": entry.get("ts", 0),
            })

        # Sort by score descending, then by recency
        scored.sort(key=lambda x: (x["score"], x["ts"]), reverse=True)
        return scored[:limit]

    def get_relevant_context(self, query: str, limit: int = 3) -> str:
        """Get relevant history as a formatted string for model context."""
        results = self.search(query, limit=limit)
        if not results:
            return ""

        parts = []
        for r in results:
            role = r["role"].capitalize()
            content = r["content"]
            if len(content) > 500:
                content = content[:500] + "..."
            parts.append(f"[{role}] {content}")

        return "Related past context:\n" + "\n---\n".join(parts)

    def clear(self):
        """Clear all RAG memory entries."""
        self.entries = []
        self.save()
        log.info("RAG memory cleared")
