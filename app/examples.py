"""Verified question -> query example bank (this is how ciq-ai "learns").

Claude is not trained by feeding it questions. Instead, every verified pair lives in
app/rag/knowledge_base/examples.json and the 3 most similar ones are injected into the
query-generation prompt for each new question (dynamic few-shot). Zero extra LLM calls,
~300-500 extra input tokens per request, big accuracy gain on your own metrics.

Example format:
  {"question": "...", "collection": "transactions", "tags": [...],
   "query": "db.transactions.aggregate([... $date(\\"<this_month_start>\\") ...])",
   "source": "seed" | "verified"}
Dates inside examples are written as <placeholders> (see date_values in prompts.py) and are
replaced with real values when the example is shown to the model.
"""
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Optional

from app.prompts import date_values

EXAMPLES_FILE = Path(__file__).resolve().parent / "rag" / "knowledge_base" / "examples.json"

_STOP = {
    "the", "a", "an", "of", "in", "on", "for", "to", "me", "my", "is", "are", "was", "were",
    "how", "many", "much", "what", "show", "get", "give", "list", "tell", "total", "number",
    "and", "or", "by", "with", "from", "did", "do", "does", "we", "our", "all", "please",
    # time words: dates are handled by the date context, so they should not drive matching
    "last", "this", "month", "week", "year", "today", "yesterday", "now", "current", "days", "day",
}
_LITERAL_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")


def _norm(token: str) -> str:
    return token[:-1] if len(token) > 3 and token.endswith("s") else token


def _tokens(text: str) -> set:
    return {_norm(t) for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in _STOP and len(t) > 1}


@lru_cache(maxsize=1)
def load_examples() -> list[dict]:
    try:
        return json.loads(EXAMPLES_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def top_examples(question: str, k: int = 3, collections: Optional[list[str]] = None) -> list[dict]:
    """Most similar examples by word overlap (+ small bonus if on a selected collection)."""
    q = _tokens(question)
    scored = []
    for ex in load_examples():
        t = _tokens(ex["question"]) | {_norm(x.lower()) for x in ex.get("tags", [])}
        inter = len(q & t)
        if not inter:
            continue
        score = inter / len(q | t)
        if collections and ex.get("collection") in collections:
            score += 0.1
        scored.append((score, ex))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [ex for _, ex in scored[:k]]


def format_examples(examples: list[dict]) -> str:
    """Render examples for the prompt, with <placeholders> replaced by today's real dates."""
    if not examples:
        return ""
    vals = date_values()
    blocks = []
    for ex in examples:
        query = ex["query"]
        for name, value in vals.items():
            query = query.replace(f"<{name}>", value)
        blocks.append(f"Q: {ex['question']}\n{query}")
    return "\n\n".join(blocks)


def add_example(question: str, query: str, tags: Optional[list[str]] = None, source: str = "verified") -> str:
    """Append (or replace by question) one example. Returns a status message."""
    query = query.strip()
    m = re.match(r"^db\.([A-Za-z_][A-Za-z0-9_]*)\.aggregate\(\s*\[", query)
    if not m:
        raise ValueError("query must start with db.<collection>.aggregate([")
    if "$limit" not in query and "$count" not in query:
        raise ValueError('query needs a final { "$limit": N } stage (or $count)')
    if _LITERAL_DATE_RE.search(query):
        raise ValueError(
            "query contains literal dates. Replace them with placeholders such as "
            "<last_month_start>, <this_month_start>, <tomorrow_start>, <today_start>, "
            "<yesterday_start>, <last_7d_start>, <last_30d_start>, <this_year_start>."
        )

    data = list(load_examples())
    entry = {
        "question": question.strip(),
        "collection": m.group(1),
        "tags": tags or [],
        "query": query,
        "source": source,
    }
    replaced = False
    for i, ex in enumerate(data):
        if ex["question"].strip().lower() == entry["question"].lower():
            data[i], replaced = entry, True
            break
    if not replaced:
        data.append(entry)

    EXAMPLES_FILE.parent.mkdir(parents=True, exist_ok=True)
    EXAMPLES_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    load_examples.cache_clear()
    return f"{'Updated' if replaced else 'Added'} example #{len(data)} on '{entry['collection']}'"