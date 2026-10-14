"""Shared helpers for the domain knowledge packs (affiliates, transactions, ...)."""
import re

from app.prompts import date_values

_WORD = re.compile(r"[a-z0-9]+")


def name_expr(prefix: str) -> str:
    """Display name of an affiliate: companyName, else username, else the id as text."""
    return (
        '{"$let": {"vars": {"c": {"$ifNull": ["' + prefix + 'companyName", ""]}}, '
        '"in": {"$cond": [{"$ne": ["$$c", ""]}, "$$c", '
        '{"$ifNull": ["' + prefix + 'username", {"$toString": "$_id"}]}]}}}'
    )


def player_name_expr(prefix: str = "$p.") -> str:
    """Display name of a player: first + last name, else username, else the id as text."""
    return (
        '{"$let": {"vars": {"n": {"$trim": {"input": {"$concat": [{"$ifNull": ["' + prefix + 'firstName", ""]}, " ", '
        '{"$ifNull": ["' + prefix + 'lastName", ""]}]}}}}, '
        '"in": {"$cond": [{"$ne": ["$$n", ""]}, "$$n", {"$ifNull": ["' + prefix + 'username", {"$toString": "$_id"}]}]}}}'
    )


TOKENS = {
    "@AFF_LOOKUP@": '{"$lookup": {"from": "affiliates", "localField": "_id", "foreignField": "_id", "as": "aff"}}',
    "@AFF_UNWIND@": '{"$unwind": {"path": "$aff", "preserveNullAndEmptyArrays": True}}',
    "@NAME_AFF@": name_expr("$aff."),
    "@NAME_DIRECT@": name_expr("$"),
    "@PLAYER_LOOKUP@": '{"$lookup": {"from": "players", "localField": "_id", "foreignField": "_id", "as": "p"}}',
    "@PLAYER_UNWIND@": '{"$unwind": {"path": "$p", "preserveNullAndEmptyArrays": True}}',
    "@PLAYER_NAME@": player_name_expr("$p."),
}


def render(text: str) -> str:
    """Fill the @TOKENS@ and the <date_placeholders> of an example query."""
    for token, value in TOKENS.items():
        text = text.replace(token, value)
    for key, value in date_values().items():
        text = text.replace(f"<{key}>", value)
    return text


def pick_examples(question: str, examples: list[dict], k: int = 3) -> list[dict]:
    """The k examples most similar to the question (keyword hits count 3x, shared words 1x)."""
    q = (question or "").lower()
    q_words = set(_WORD.findall(q))
    scored = []
    for ex in examples:
        score = 3 * sum(1 for kw in ex["keywords"] if kw in q)
        score += len(q_words & set(_WORD.findall(ex["q"].lower())))
        if score > 0:
            score += ex.get("bonus", 0)
        scored.append((score, ex))
    scored.sort(key=lambda s: s[0], reverse=True)
    picked = [ex for score, ex in scored[:k] if score > 0]
    return picked or examples[:1]


def format_examples(examples: list[dict]) -> str:
    return "\n\n".join(f"Question: {ex['q']}\nQuery: {render(ex['query'])}" for ex in examples)