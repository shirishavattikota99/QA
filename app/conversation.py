"""Conversation continuity: turn a follow-up question into a standalone one.

The query graph (app.graph.ask) answers ONE self-contained question. When a user asks
"and what about last month?" or "which of those deposited?", the graph has no idea what
"those" or "and" refer to. So before calling the graph we rewrite the follow-up into a
standalone question using the earlier turns of the same conversation:

    turns = get_conversation_turns(partner_id, conversation_id)   # oldest first
    standalone = resolve_followup("and last month?", turns)
    result = ask(standalone, mongo_uri)

No history -> no LLM call and the question is returned unchanged. If the rewrite fails for
any reason the original question is used, so a rewrite problem never breaks the chat.
"""
import logging
import re
from typing import Optional

log = logging.getLogger("ciq")

MAX_TURNS = 4            # most recent turns shown to the rewriter
MAX_ANSWER_CHARS = 700   # each earlier answer is cut to this size (entity names come first)
MAX_REWRITE_CHARS = 600  # a longer rewrite is treated as a failed rewrite

REWRITE_PROMPT = (
    "You rewrite follow-up questions for a casino CRM data assistant.\n"
    "You get the earlier turns of a conversation and the user's newest message.\n"
    "Rewrite the newest message as ONE complete, standalone question that can be answered "
    "without seeing the conversation.\n"
    "- Replace references like 'it', 'they', 'those', 'that affiliate', 'the first one', "
    "'the same period' with the real names, metrics and time periods from the earlier turns.\n"
    "- If the message only changes one part (for example 'and last month?', 'what about "
    "withdrawals?', 'now for coupons'), keep everything else from the previous question and "
    "change only that part.\n"
    "- If the message is already a complete question on its own, or starts a new topic, "
    "return it unchanged.\n"
    "- Keep the user's own wording and relative dates ('this month', 'last year') as written. "
    "Do not invent filters, names, numbers or periods that are not in the conversation.\n"
    "- Do not answer the question. Reply with ONLY the rewritten question, on one line."
)


def _text(content) -> str:
    """LLM message content can be a str or a list of content blocks."""
    if isinstance(content, str):
        return content
    return "".join(
        b if isinstance(b, str) else b.get("text", "")
        for b in content
        if isinstance(b, (str, dict))
    )


def format_turns(turns: list[dict]) -> str:
    """Last few turns as plain text: the standalone question and a short answer."""
    lines = []
    for t in turns[-MAX_TURNS:]:
        question = (t.get("resolved_question") or t.get("question") or "").strip()
        answer = (t.get("answer") or "").strip()
        if not question or not answer:
            continue  # a failed turn gives the rewriter nothing to refer to
        if len(answer) > MAX_ANSWER_CHARS:
            answer = answer[:MAX_ANSWER_CHARS].rstrip() + "..."
        lines.append(f"User: {question}\nAssistant: {answer}")
    return "\n\n".join(lines)


def _clean(reply: str) -> str:
    """Take the first non-empty line and drop labels or quotes the model may add."""
    line = next((ln.strip() for ln in reply.splitlines() if ln.strip()), "")
    line = re.sub(r"^(?:rewritten|standalone)?\s*question\s*:\s*", "", line, flags=re.IGNORECASE)
    return line.strip().strip("\"'`").strip()


def resolve_followup(question: str, turns: list[dict], llm=None) -> str:
    """Return a standalone version of `question` (or `question` itself when nothing changes).

    llm: any object with .invoke(messages) -> message with .content. Defaults to the
    project's model (app.brain.Brain); passed in by tests.
    """
    question = (question or "").strip()
    history = format_turns(turns or [])
    if not question or not history:
        return question

    try:
        from langchain_core.messages import HumanMessage, SystemMessage

        if llm is None:
            llm = _default_llm()
        response = llm.invoke([
            SystemMessage(content=REWRITE_PROMPT),
            HumanMessage(content=f"Earlier turns:\n{history}\n\nNewest message: {question}"),
        ])
        rewritten = _clean(_text(response.content))
    except Exception as e:  # never break the chat because the rewrite failed
        log.warning("Follow-up rewrite failed, using the original question: %s", e)
        return question

    if not rewritten or len(rewritten) > MAX_REWRITE_CHARS:
        return question
    return rewritten


_llm = None


def _default_llm():
    """One shared model instance, created on first use."""
    global _llm
    if _llm is None:
        from app.brain import Brain

        _llm = Brain().llm
    return _llm
