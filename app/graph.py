import json
import os
import re
import sys
from functools import lru_cache
from datetime import datetime, timezone
from langchain.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from app.brain import Brain
import difflib
from pymongo import MongoClient

from app.examples import format_examples, top_examples
from app.prompts import generate_query_system_prompt
from app.rag.doc_store import search_documents
from app.tools import get_langchain_mongodb_tools, mongodb_collection_descriptions

# ---------------------------------------------------------------------------
# State: chat messages + what the document search / router decided
# ---------------------------------------------------------------------------
class State(MessagesState):
    route: str          # "documents" | "database" | "both"
    docs: str           # document excerpts found for this question
    sources: list[str]  # file names those excerpts came from
    # --- multi-part questions (empty parts = normal single-part question) ---
    parts: list[str]    # the separate questions found in the user's message
    outputs: list[str]  # final query result of each finished part
    part_idx: int       # which part is being worked on
    retries: int        # retries used so far for the current part


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
MAX_RETRIES = 2            # extra attempts if the generated query errors
DOC_CONTEXT_CHARS = 2000    # max size of document excerpts sent to the LLM (~500 tokens)
MAX_RESULT_CHARS = 4000    # max size of query results sent to the LLM (~1000 tokens)
MAX_PARTS = 3              # max separate queries for ONE multi-part question

# Cheap check (no LLM call): does the question ask for more than one thing?
MULTI_PART = re.compile(
    r"\?\s*\S"                                                        # a 2nd question after a "?"
    r"|\b(?:and|also|then|plus)\s+(?:from\s+)?(?:which|what|who|whom|how|when|where)\b"
    r"|\b(?:as well as|along with)\b",
    re.IGNORECASE,
)

SPLIT_PROMPT = (
    "Split the user's message into the separate questions it asks.\n"
    "- Keep metrics about the same subject together in ONE part "
    "(e.g. 'top 3 players by deposits and how many withdrawals each made' is ONE part).\n"
    "- Start a new part only for an independent question about a different subject "
    "(e.g. 'and which affiliate got the most registrations').\n"
    "- Each part must make sense on its own. Copy a time period (like 'this year') into a part "
    "ONLY if the user applied it to that part. Do not add filters or periods the user did not ask for.\n"
    f"- At most {MAX_PARTS} parts.\n"
    "Reply with ONLY a JSON array of strings, nothing else."
)


def looks_multi_part(question: str) -> bool:
    return bool(MULTI_PART.search(question or ""))

# Never sent to the LLM (schema or results) and never returned to the client
SENSITIVE_KEY = re.compile(
    r"password|token|secret|api_?key|iban|bank_?account|kycbank|ip_?address|^__v$", re.IGNORECASE
)

TRANSACTIONS_NOTE = (
    "\n\nTransactions field values:\n"
    "- source: Payment, Game, Admin, Affiliate, Kiosk, Automate, Coupon, Self, Sports\n"
    "- type: Deposit, Withdraw, Credit, Debit, Bet, Win, Rollback\n"
    "- amountType: Real, Bonus, Real_Bonus\n"
    "- status: Pending, Failed, Rejected, Cancelled, Success, Initiated, Refunded, Chargeback\n"
    "- Game activity: source=Game, type in Bet/Win/Rollback. Deposits: source=Payment, "
    "type=Deposit, status=Success. Admin: source=Admin, type in Credit/Debit."
)

ROUTER_PROMPT = (
    "You route questions for a casino CRM assistant. You have document excerpts "
    "(policies, product guides) and a live database (players, transactions, affiliates, games).\n"
    "Reply with ONE word on the first line:\n"
    "DOCUMENTS - the excerpts fully answer the question. Put the answer on the next lines: "
    "plain friendly English, 1-4 sentences, using only the excerpts.\n"
    "DATABASE - the question needs live data (counts, lists, totals, dates, specific players), "
    "or the excerpts are not relevant.\n"
    "BOTH - it needs the excerpts for an explanation AND live data.\n"
    "Never guess beyond the excerpts."
)

CURRENCY_SYMBOL = os.getenv("CURRENCY_SYMBOL", "€")
CURRENCY_NAME = os.getenv("CURRENCY_NAME", "euros (EUR)")

ANSWER_PROMPT = (
    "You answer questions for a casino CRM admin, using ONLY the data provided.\n"
    "- Reply in plain, friendly English: 1-3 sentences, or a short list (max 10 items) "
    "if the data is a list of records.\n"
    "- Never ask the user to provide data or clarify; answer with what the data shows. "
    "If an item has an id but no name, call it 'an unnamed payment method' / 'unnamed item' and still report its number.\n"
    "- Give exact numbers. If more rows exist than shown, say the total count.\n"
    "- Never mention databases, collections, queries, JSON or field names. "
    "Say 'players', not 'documents'.\n"
    "- Write dates like 12 Aug 2026. Do not repeat the question.\n"
    f"- All money amounts are in {CURRENCY_NAME}. Write them with the {CURRENCY_SYMBOL} symbol, "
    f"e.g. {CURRENCY_SYMBOL}1,250.50. Never use $ or USD.\n"
    "- If the data is split into numbered parts, answer EVERY part, in order. "
    "'no matching records' for a part means zero / none for that part; "
    "'could not be retrieved' means say that part could not be answered right now.\n"
    "- If document excerpts are also given, use them for explanations and the data for numbers."
)

# ---------------------------------------------------------------------------
# Init (shared by every partner/database)
# ---------------------------------------------------------------------------
model = Brain().llm

# Static collection guide (business rules), read once
COLLECTION_GUIDE = mongodb_collection_descriptions.invoke({})


# ---------------------------------------------------------------------------
# Topic hints: question keywords -> collection-name fragments (matched against the REAL
# collection list at runtime, so it works whatever your coupon/sports/kyc collections are called)
# ---------------------------------------------------------------------------
TOPIC_HINTS = [
    (("kyc", "verif", "document"), ("kyc", "players")),
    (("payment method", "payment gateway", "epayment", "e-payment", "gateway", "deposit method", "withdraw method", "paid through", "payment type"),
     ("paymentgateway", "transactions")),
    (("who deposited", "by whom", "highest depositor", "top depositor", "which player", "player name", "person who deposited"),
     ("players", "transactions")),
    (("affiliate", "affiliates", "referral partner", "affiliate channel"),
     ("affiliate", "affiliatechannel", "players", "transactions")),
    (("coupon", "promo", "voucher"), ("coupon", "transactions")),
    (("sport", "betslip", "bet slip", "odds"), ("sport", "transactions")),
    (("master provider", "provider", "vendor"), ("masterprovider", "provider", "games")),
    (("game",), ("games",)),
    (("categor",), ("categor", "games")),
]
MAX_COLLECTIONS = 6
_SKIP_VALUE_KEYS = re.compile(r"email|phone|mobile|address|user_?name|first_?name|last_?name|dob|birth", re.IGNORECASE)
_ID_KEY = re.compile(r"(?:Id|_id)$")


def resolve_collections(question: str, requested: list[str], available: list[str]) -> list[str]:
    """Fix wrong/misspelled names from the LLM and add collections the topic obviously needs."""
    by_lower = {a.lower(): a for a in available}
    out = []
    for name in requested:
        n = name.strip().lower()
        if n in by_lower:
            out.append(by_lower[n])
        else:
            close = difflib.get_close_matches(n, list(by_lower), n=1, cutoff=0.6)
            if close:
                out.append(by_lower[close[0]])
    q = question.lower()
    for keywords, needles in TOPIC_HINTS:
        if any(k in q for k in keywords):
            for needle in needles:
                out += [a for a in available if needle in a.lower()]
    return list(dict.fromkeys(out))[:MAX_COLLECTIONS]


@lru_cache(maxsize=32)
def _mongo_client(uri: str) -> MongoClient:
    return MongoClient(uri, serverSelectionTimeoutMS=5000)


@lru_cache(maxsize=128)
def observed_values(uri: str, collection: str) -> str:
    """Distinct values of low-cardinality fields (status, type, booleans) from a sample.

    The schema tool only gives field names/types, so the LLM was guessing values like
    status = "Active" and getting 0 rows. This shows the real values.
    """
    try:
        docs = list(_mongo_client(uri).get_default_database()[collection].aggregate([{"$sample": {"size": 300}}]))
    except Exception:
        return ""
    seen: dict[str, set] = {}
    dates: dict[str, list] = {}
    for d in docs:
        for k, v in d.items():
            if SENSITIVE_KEY.search(k) or _SKIP_VALUE_KEYS.search(k) or _ID_KEY.search(k):
                continue
            if isinstance(v, datetime):
                lo_hi = dates.setdefault(k, [v, v])
                lo_hi[0], lo_hi[1] = min(lo_hi[0], v), max(lo_hi[1], v)
                continue
            if isinstance(v, bool) or (isinstance(v, str) and 0 < len(v) <= 30):
                seen.setdefault(k, set()).add(v)
    lines = [
        f"- {collection}.{k}: {json.dumps(sorted(vals, key=str), ensure_ascii=False)}"
        for k, vals in seen.items()
        if len(vals) <= 12 and not (len(docs) > 20 and len(vals) == len(docs))
    ]
    lines += [
        f"- {collection}.{k}: DATE field, sample range {lo:%Y-%m-%d} to {hi:%Y-%m-%d}"
        for k, (lo, hi) in dates.items()
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _text(content) -> str:
    """Message content can be a str or a list of content blocks."""
    if isinstance(content, str):
        return content
    return "".join(
        b if isinstance(b, str) else b.get("text", "")
        for b in content
        if isinstance(b, (str, dict))
    )


def has_tool_call(state: MessagesState) -> bool:
    return bool(getattr(state["messages"][-1], "tool_calls", None))


def strip_sensitive_schema(schema_text: str) -> str:
    """Drop sensitive field lines (e.g. `password: String`) from schema text."""
    kept = []
    for line in schema_text.splitlines():
        name = line.split(":", 1)[0].strip().split(".")[-1]
        if ":" in line and SENSITIVE_KEY.search(name):
            continue
        kept.append(line)
    return "\n".join(kept)


def _simplify(value):
    """Shrink Mongo extended JSON, drop nulls and sensitive keys."""
    if isinstance(value, dict):
        if set(value) == {"$oid"}:
            return value["$oid"]
        if set(value) == {"$date"}:
            d = value["$date"]
            return re.sub(r"\.\d+Z$", "Z", d) if isinstance(d, str) else d
        for k in ("$numberLong", "$numberInt", "$numberDecimal", "$numberDouble"):
            if set(value) == {k}:
                return float(value[k]) if "." in value[k] else int(float(value[k]))
        return {
            k: _simplify(v)
            for k, v in value.items()
            if v is not None and not SENSITIVE_KEY.search(k)
        }
    if isinstance(value, list):
        return [_simplify(v) for v in value]
    return value


def parse_result(text: str):
    """Query result text -> cleaned python data (list), or None if not JSON."""
    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        return None
    return _simplify(data)


def compact_result(text: str, max_chars: int = MAX_RESULT_CHARS):
    """Return (compact_json, total_rows, shown_rows). Whitespace-free and size-capped."""
    data = parse_result(text)
    if data is None:
        return text[:max_chars], None, None
    if not isinstance(data, list):
        data = [data]
    rows, size = [], 2
    for row in data:
        s = json.dumps(row, separators=(",", ":"), ensure_ascii=False)
        if size + len(s) + 1 > max_chars:
            break
        rows.append(s)
        size += len(s) + 1
    return "[" + ",".join(rows) + "]", len(data), len(rows)


def flatten_context(state: MessagesState, instruction: str) -> HumanMessage:
    """Collapse the conversation into ONE plain-text HumanMessage.

    Gemini 3.x requires a `thought_signature` on every replayed function call
    (400 error otherwise), and a request may not end with a model turn. Sending
    tool *results* as plain text avoids both problems.
    """
    messages = state["messages"]
    question = next((_text(m.content) for m in messages if m.type == "human"), "")
    parts, seen_question = [], False
    for m in messages:
        if m.type == "human" and not seen_question:
            seen_question = True
            continue
        if m.type == "human":
            parts.append(_text(m.content))
        elif m.type == "tool":
            parts.append(f"[{m.name} result]\n{_text(m.content)}")
        elif m.type == "ai":
            for call in getattr(m, "tool_calls", None) or []:
                if call["name"] == "mongodb_query":
                    parts.append(f"[Query tried]\n{call['args'].get('query', '')}")
            if _text(m.content).strip():
                parts.append(_text(m.content))
    context = "\n\n".join(parts)
    return HumanMessage(
        content=f"Question: {question}\n\n{context}\n\n{instruction}"
    )


def _query_attempts(state: MessagesState) -> int:
    return sum(1 for m in state["messages"] if m.type == "tool" and m.name == "mongodb_query")


EMPTY_RESULTS = ("", "[]", "{}", "None")


def _is_bad(text: str) -> bool:
    """A query result that failed or came back empty."""
    return text.startswith("Error") or text in EMPTY_RESULTS


def _question(state: MessagesState) -> str:
    return next((_text(m.content) for m in state["messages"] if m.type == "human"), "")


# ---------------------------------------------------------------------------
# Answer node + routing (no database access needed)
# ---------------------------------------------------------------------------
def answer(state: State):
    """Final LLM call: turn the query result (and document excerpts, if any) into plain English."""
    question = next((_text(m.content) for m in state["messages"] if m.type == "human"), "")
    result = _text(state["messages"][-1].content).strip()
    docs = state.get("docs") if state.get("route") == "both" else ""

    # ---- multi-part question: one result per part ----
    parts = state.get("parts") or []
    if parts:
        outs = state.get("outputs") or []
        results = [outs[i] if i < len(outs) else None for i in range(len(parts))]
        if all(r is None or r.startswith("Error") for r in results):
            return {"messages": [AIMessage(
                content="Sorry, I couldn't retrieve that information right now. "
                        "Please try rephrasing your question."
            )]}
        blocks = []
        for i, (part, r) in enumerate(zip(parts, results), 1):
            if r is None or r.startswith("Error"):
                body = "could not be retrieved"
            elif r in EMPTY_RESULTS:
                body = "no matching records"
            else:
                data, total, shown = compact_result(r)
                rows_info = f"Rows: {total} (showing {shown})\n" if total is not None else ""
                body = f"{rows_info}Data: {data}"
            blocks.append(f"Part {i} - {part}\n{body}")
        doc_part = f"\nDocument excerpts:\n{docs}" if docs else ""
        response = model.invoke([
            SystemMessage(content=ANSWER_PROMPT),
            HumanMessage(content=f"Question: {question}\n\n" + "\n\n".join(blocks) + doc_part),
        ])
        return {"messages": [AIMessage(content=_text(response.content))]}

    if result.startswith("Error"):
        return {"messages": [AIMessage(
            content="Sorry, I couldn't retrieve that information right now. "
                    "Please try rephrasing your question."
        )]}

    data, total, shown = compact_result(result)
    if total == 0 and not docs:
        # No LLM call needed
        if re.search(r"how many|total (no|number)|count|number of", question, re.IGNORECASE):
            return {"messages": [AIMessage(content="The count is 0.")]}
        return {"messages": [AIMessage(content="I couldn't find any records matching your request.")]}

    if total == 0:
        data, rows_info = "no matching records", ""
    else:
        rows_info = f"Rows: {total} (showing {shown})\n" if total is not None else ""
    doc_part = f"\nDocument excerpts:\n{docs}" if docs else ""
    response = model.invoke([
        SystemMessage(content=ANSWER_PROMPT),
        HumanMessage(content=f"Question: {question}\n{rows_info}Data: {data}{doc_part}"),
    ])
    return {"messages": [AIMessage(content=_text(response.content))]}


def retrieve_docs(state: State):
    """Search the documents first (local, free - no Gemini call)."""
    question = next((_text(m.content) for m in state["messages"] if m.type == "human"), "")
    hits = search_documents(question)
    if not hits:
        return {"route": "database", "docs": "", "sources": []}
    docs = "\n\n".join(f"[{h['source']}]\n{h['text']}" for h in hits)[:DOC_CONTEXT_CHARS]
    return {"route": "pending", "docs": docs, "sources": list(dict.fromkeys(h["source"] for h in hits))}


def route_question(state: State):
    """Only runs when relevant documents were found: decide documents / database / both."""
    question = next((_text(m.content) for m in state["messages"] if m.type == "human"), "")
    response = model.invoke([
        SystemMessage(content=ROUTER_PROMPT),
        HumanMessage(content=f"Question: {question}\n\nDocument excerpts:\n{state['docs']}"),
    ])
    text = _text(response.content).strip()
    m = re.match(r"\W*(DOCUMENTS|DATABASE|BOTH)\b", text, re.IGNORECASE)
    choice = m.group(1).lower() if m else "database"  # unclear reply -> use the database, as before
    if choice == "documents":
        reply = text[m.end():].strip(" :-\n")
        if reply:
            return {"route": "documents", "messages": [AIMessage(content=reply)]}
        choice = "database"
    return {"route": choice}


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------
def route_after_docs(state: State):
    return "router" if state.get("docs") else "database"


def route_after_router(state: State):
    return "documents" if state.get("route") == "documents" else "database"


def route_after_generate(state: State):
    # Only run the query if the LLM actually made a tool call
    if has_tool_call(state):
        return "run"
    # Multi-part: the model could not build a query for a later part -> answer with what we have
    return "answer" if state.get("parts") and state.get("outputs") else "end"


def route_after_run(state: State):
    parts = state.get("parts") or []
    if parts:
        if state.get("retries", 0) > 0:               # record_result decided to retry this part
            return "retry"
        if state.get("part_idx", 0) < len(parts):     # more parts to do
            return "next"
        return "answer"
    # normal single-part question (unchanged)
    text = _text(state["messages"][-1].content).strip()
    failed = text.startswith("Error") or text in ("", "[]", "{}", "None")
    if failed and _query_attempts(state) <= MAX_RETRIES:
        return "retry"
    return "answer"


def split_parts(state: State):
    """Multi-part questions only: split the message into its separate questions (1 small LLM call)."""
    none = {"parts": [], "outputs": [], "part_idx": 0, "retries": 0}
    question = _question(state)
    if not looks_multi_part(question):
        return none
    response = model.invoke([SystemMessage(content=SPLIT_PROMPT), HumanMessage(content=question)])
    found = re.search(r"\[.*\]", _text(response.content), re.DOTALL)
    try:
        parts = [p.strip() for p in json.loads(found.group(0)) if isinstance(p, str) and p.strip()] if found else []
    except ValueError:
        parts = []
    parts = parts[:MAX_PARTS]
    if len(parts) < 2:
        return none  # really one question -> normal flow
    return {"parts": parts, "outputs": [], "part_idx": 0, "retries": 0}


def record_result(state: State):
    """Multi-part only: save this part's result, then retry the part or move to the next one."""
    if not state.get("parts"):
        return {"retries": state.get("retries", 0)}  # normal question: no change
    last = next(
        (_text(m.content).strip() for m in reversed(state["messages"]) if m.type == "tool" and m.name == "mongodb_query"),
        "",
    )
    retries = state.get("retries", 0)
    if _is_bad(last) and retries < MAX_RETRIES:
        return {"retries": retries + 1}
    return {
        "outputs": (state.get("outputs") or []) + [last],
        "part_idx": state.get("part_idx", 0) + 1,
        "retries": 0,
    }


# ---------------------------------------------------------------------------
# Graph factory: one graph per database (each partner has its own MongoDB)
# ---------------------------------------------------------------------------
def build_graph(mongo_uri: str):
    tools = get_langchain_mongodb_tools(mongo_uri, llm=model)["tools"]

    def _get_tool(name: str):
        for t in tools:
            if t.name == name:
                return t
        raise ValueError(f"Tool '{name}' not found. Available: {[t.name for t in tools]}")

    list_collections_tool = _get_tool("mongodb_list_collections")
    get_schema_tool = _get_tool("mongodb_schema")
    run_query_tool = _get_tool("mongodb_query")
    run_query_node = ToolNode([run_query_tool], name="run_query")

    available: list[str] = []

    def list_tables(state: MessagesState):
        """Load usable collection names (no LLM call)."""
        collections = list_collections_tool.invoke({})
        available[:] = [c for c in re.findall(r"[A-Za-z_]\w*", str(collections)) if c.lower() != "collections"]
        return {"messages": [HumanMessage(content=f"Collections: {collections}")]}

    def select_collections(state: MessagesState):
        """LLM call 1: pick collections and request their schema (one step)."""
        system = (
            "You are a MongoDB expert for a casino CRM.\n"
            "Pick ONLY the collections needed for the question and call `mongodb_schema` "
            "with their exact names (comma-separated). Do not guess names.\n\n"
            "AFFILIATE RULE: If the question asks which affiliate referred, brought, "
            "or registered the most players, select both players and affiliates "
            "when those exact collection names exist. Use players.affiliateId as "
            "the affiliate reference. Never use players.affiliateQueryParams as "
            "the affiliate identifier. Include affiliates when the answer requires "
            "an affiliate name. Use only fields confirmed by the supplied schema.\n\n"
            f"{COLLECTION_GUIDE}"
        )

        
        llm = model.bind_tools([get_schema_tool], tool_choice="mongodb_schema")
        response = llm.invoke([
            SystemMessage(content=system),
            flatten_context(state, "Call `mongodb_schema` now."),
        ])
        # Repair wrong names and add the collections the topic needs (kyc, coupons, sports, payments...)
        question = next((_text(m.content) for m in state["messages"] if m.type == "human"), "")
        for call in getattr(response, "tool_calls", None) or []:
            requested = str(call["args"].get("collection_names", "")).split(",")
            fixed = resolve_collections(question, requested, available)
            if fixed:
                call["args"]["collection_names"] = ", ".join(fixed)
        return {"messages": [response]}

    def get_schema(state: MessagesState):
        """Fetch schema (field names/types only) and remove sensitive fields."""
        calls = getattr(state["messages"][-1], "tool_calls", None) or []
        if not calls:
            return {"messages": [HumanMessage(content="No schema available.")]}
        out = []
        for call in calls:
            try:
                text = strip_sensitive_schema(get_schema_tool.invoke(call["args"]))
                names = [n.strip() for n in str(call["args"].get("collection_names", "")).split(",") if n.strip()]
                hints = "\n".join(h for h in (observed_values(mongo_uri, n) for n in names) if h)
                if hints:
                    text += "\n\nObserved values (use exactly these for filters):\n" + hints
            except Exception as e:  # e.g. unknown collection name
                text = f"Error: {e}"
            out.append(ToolMessage(content=text, tool_call_id=call["id"], name=call["name"]))
        return {"messages": out}

    def generate_query(state: State):
        """LLM call 2: write the MongoDB aggregation query."""
        today = datetime.now(timezone.utc).date().isoformat()
        schema_text = " ".join(
            _text(m.content) for m in state["messages"] if m.type == "tool" and m.name == "mongodb_schema"
        )
        system = (
            f"{generate_query_system_prompt}\n\n"
            f"Current UTC date: {today}\n"
            "Use the schema and observed values provided for this question. "
            "Select a query strategy that matches the user's actual intent; do not apply "
            "unrelated business rules or assume every question is about transactions."
        )
        if "Collection name: transactions" in schema_text:
            system += TRANSACTIONS_NOTE
        question = next((_text(m.content) for m in state["messages"] if m.type == "human"), "")
        shots = format_examples(top_examples(question))
        if shots:
            system += f"\n\nVerified examples (follow their style):\n{shots}"

        parts = state.get("parts") or []
        if parts:
            idx = min(state.get("part_idx", 0), len(parts) - 1)
            instruction = (
                f"The user asked several things. Write ONE query for ONLY this part "
                f"(part {idx + 1} of {len(parts)}): {parts[idx]}\n"
                "Make it self-contained in a single pipeline: use $lookup / $group for names and "
                "counts instead of copying ids from earlier results. Do not repeat a query that "
                "already ran for another part. Use a date range ONLY if THIS part states one; "
                "do not take a period from the other parts of the question."
            )
            retrying = state.get("retries", 0) > 0
        else:
            instruction = "Now call `mongodb_query` with the aggregation query that answers the question."
            retrying = bool(_query_attempts(state))
        if retrying:
            instruction += (
                " The previous query for this part failed or returned no rows. Keep the SAME collection "
                "(only names from the schema exist; never invent one like db.Sports). Re-check the date "
                "field (use a DATE field listed under 'Observed values') and every filter value "
                "(exact spelling/case) against 'Observed values'. Keep ALL filters from the question "
                "(source, type, status, dates); do not drop or change them. Write ids as "
                "ObjectId(\"...\"), never as {\"$oid\": ...}."
            )

        # Not forced: the model may answer in plain text if it cannot build a query.
        llm = model.bind_tools([run_query_tool])
        response = llm.invoke([
            SystemMessage(content=system),
            flatten_context(state, instruction),
        ])
        return {"messages": [response]}

    builder = StateGraph(State)
    builder.add_node("retrieve_docs", retrieve_docs)
    builder.add_node("route_question", route_question)
    builder.add_node("list_tables", list_tables)
    builder.add_node("select_collections", select_collections)
    builder.add_node("get_schema", get_schema)
    builder.add_node("split_parts", split_parts)
    builder.add_node("generate_query", generate_query)
    builder.add_node("run_query", run_query_node)
    builder.add_node("record_result", record_result)
    builder.add_node("answer", answer)

    builder.add_edge(START, "retrieve_docs")
    builder.add_conditional_edges("retrieve_docs", route_after_docs, {"router": "route_question", "database": "list_tables"})
    builder.add_conditional_edges("route_question", route_after_router, {"documents": END, "database": "list_tables"})
    builder.add_edge("list_tables", "select_collections")
    builder.add_edge("select_collections", "get_schema")
    builder.add_edge("get_schema", "split_parts")
    builder.add_edge("split_parts", "generate_query")
    builder.add_conditional_edges(
        "generate_query", route_after_generate, {"run": "run_query", "answer": "answer", "end": END}
    )
    builder.add_edge("run_query", "record_result")
    builder.add_conditional_edges(
        "record_result", route_after_run, {"retry": "generate_query", "next": "generate_query", "answer": "answer"}
    )
    builder.add_edge("answer", END)
    return builder.compile()


@lru_cache(maxsize=32)
def get_graph(mongo_uri: str):
    """Build once per database and reuse (keeps the Mongo connection open)."""
    return build_graph(mongo_uri)


# ---------------------------------------------------------------------------
# Public helper (use this from FastAPI / your chat app)
# ---------------------------------------------------------------------------
def collections_from_query(query: str | None) -> list[str]:
    """Collections a MongoDB query actually reads: db.<collection>.aggregate + $lookup "from"."""
    if not query:
        return []
    names = re.findall(r"\bdb\.(\w+)\.", query)
    names += re.findall(r"[\"']from[\"']\s*:\s*[\"'](\w+)[\"']", query)
    return list(dict.fromkeys(names))


def build_sources(route: str, doc_files: list[str], query: str | None, schema_calls: list[str]) -> list[dict]:
    """Where the answer came from: database collections and/or document files."""
    sources = []
    if route in ("database", "both"):
        collections = collections_from_query(query) or schema_calls
        sources += [{"type": "database", "name": name} for name in collections]
    if route in ("documents", "both"):
        sources += [{"type": "document", "name": name} for name in doc_files]
    return sources


def ask(question: str, mongo_uri: str | None = None) -> dict:
    """Run the graph. Returns {"answer", "route", "sources", "data", "query", "row_count"}.

    mongo_uri: the partner's database. Defaults to MONGO_OPERATOR_URI (local testing).
    """
    uri = mongo_uri or os.getenv("MONGO_OPERATOR_URI")
    if not uri:
        raise ValueError("No MongoDB URI: pass mongo_uri or set MONGO_OPERATOR_URI")
    out = get_graph(uri).invoke(
        {"messages": [HumanMessage(content=question)]},
        config={"recursion_limit": 60},
    )
    msgs = out["messages"]

    raw = next(
        (_text(m.content) for m in reversed(msgs) if m.type == "tool" and m.name == "mongodb_query"),
        None,
    )
    # every query that was run (several for multi-part questions), in order
    query = "\n\n".join(
        call["args"].get("query") or ""
        for m in msgs if m.type == "ai"
        for call in (getattr(m, "tool_calls", None) or [])
        if call["name"] == "mongodb_query"
    ) or None
    data = parse_result(raw) if raw else None  # cleaned rows, no sensitive fields
    route = out.get("route") or "database"
    schema_calls = [
        name.strip()
        for m in msgs if m.type == "ai"
        for call in (getattr(m, "tool_calls", None) or []) if call["name"] == "mongodb_schema"
        for name in str(call["args"].get("collection_names", "")).split(",") if name.strip()
    ]
    return {
        "answer": _text(msgs[-1].content),
        "route": route,  # "documents", "database" or "both"
        # [{"type": "database", "name": "transactions"}, {"type": "document", "name": "policy.md"}]
        "sources": build_sources(route, out.get("sources", []), query, schema_calls),
        "data": data,
        "query": query,  # the MongoDB query that was run (for auditing)
        "row_count": len(data) if isinstance(data, list) else None,
    }


# ---------------------------------------------------------------------------
# CLI:  python -m app.graph "your question"      (GRAPH_DEBUG=1 to see every step)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "Get me the players who registered through affiliates in last month."
    print("\nQuestion:", q)
    if os.getenv("GRAPH_DEBUG"):
        uri = os.getenv("MONGO_OPERATOR_URI")
        for step in get_graph(uri).stream({"messages": [HumanMessage(content=q)]}, stream_mode="values"):
            step["messages"][-1].pretty_print()
    else:
        res = ask(q)
        print("\nAnswer:", res["answer"])
        srcs = ", ".join(f"{x['type']}:{x['name']}" for x in res["sources"])
        print(f"\n(route: {res['route']}" + (f", sources: {srcs}" if srcs else "") + ")")