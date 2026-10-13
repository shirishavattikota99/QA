"""
ciq-ai query router: sends each question to exactly ONE source.
  mongo  -> your existing agent (app.graph.ask) on the partner's own MongoDB
  chroma -> semantic search over the ciq_db vector store (data-model docs)
  none   -> out of scope

Usage:  from app.router import route_and_answer
        result = route_and_answer(prompt, mongo_uri)
        # -> {"route", "reason", "answer", "query", "row_count"}

Uses the project's own Gemini wrapper (app.brain.Brain), so no extra packages.

Optional .env: CHROMA_PATH (default <project>/ciq_db), CHROMA_COLLECTION (default ciq_db),
               EMBEDDING_MODEL (default sentence-transformers/multi-qa-mpnet-base-dot-v1;
               must match the model used when the docs were ingested)
"""
import json
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

import chromadb
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from pydantic import BaseModel

from app.brain import Brain
from app.graph import ask

load_dotenv()

log = logging.getLogger("ciq")

llm = Brain().llm

CHROMA_PATH = os.getenv("CHROMA_PATH") or str(Path(__file__).resolve().parent.parent / "ciq_db")
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "ciq_db")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/multi-qa-mpnet-base-dot-v1")


def _text(msg) -> str:
    t = msg.text
    return t() if callable(t) else t


# ---------------------------------------------------------------------------
# 1. ROUTER
# ---------------------------------------------------------------------------
class RouteDecision(BaseModel):
    route: Literal["mongo", "chroma", "none"]
    reason: str


ROUTER_SYSTEM = """You route questions for a casino CRM analytics assistant.

mongo  -> needs live numbers or records: counts, sums, averages, lists, trends,
          rankings, per-player/per-game/per-gateway data, date ranges.
          e.g. "total deposits this month", "list players with pending KYC"
chroma -> needs knowledge from the data-model documentation: what a collection
          or field means, which collection stores something, how collections
          relate, definitions and process explanations.
          e.g. "what does the kyc_status field mean?", "which collection stores
          deposits?", "how are players and transactions related?", "what is an FTD?"

Pick exactly ONE source, never both. If a question touches both, choose by its
main ask: wants a number/record/list/trend -> mongo (e.g. "why is NGR negative
this month?" is answered from the data); wants a meaning/definition/structure/
process explanation -> chroma. Casual chat or out-of-scope -> "none"."""


def decide_route(question: str) -> RouteDecision:
    router = llm.with_structured_output(RouteDecision)
    return router.invoke([("system", ROUTER_SYSTEM), ("human", question)])


# ---------------------------------------------------------------------------
# 2. CHROMA PATH
# ---------------------------------------------------------------------------
@lru_cache(maxsize=1)
def get_vectorstore() -> Chroma:
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    return Chroma(client=client, collection_name=CHROMA_COLLECTION, embedding_function=embeddings)


def answer_from_chroma(question: str, k: int = 4) -> dict:
    hits = get_vectorstore().similarity_search(question, k=k)
    context = [{"text": h.page_content, "meta": h.metadata} for h in hits]
    r = llm.invoke([
        ("system", "Answer using ONLY the provided documentation context. "
                   "If it is insufficient, say so instead of guessing."),
        ("human", f"Question: {question}\n\nContext:\n{json.dumps(context, default=str)}"),
    ])
    return {
        "answer": _text(r),
        "query": f"[chroma:{CHROMA_COLLECTION}] similarity_search k={k}",
        "row_count": len(hits),
    }


# ---------------------------------------------------------------------------
# 3. ENTRY POINT
# ---------------------------------------------------------------------------
def route_and_answer(question: str, mongo_uri: str) -> dict:
    decision = decide_route(question)
    route = decision.route
    log.info("route=%s | reason=%s | q=%s", route, decision.reason, question)

    if route == "mongo":
        res = ask(question, mongo_uri)  # your existing agent, on the partner's DB
        out = {"answer": res["answer"], "query": res["query"], "row_count": res["row_count"]}
    elif route == "chroma":
        out = answer_from_chroma(question)
    else:
        out = {
            "answer": "I can only help with CRM data and data-model questions.",
            "query": "[none]",
            "row_count": 0,
        }
    return {"route": route, "reason": decision.reason, **out}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    uri = os.environ["MONGO_OPERATOR_URI"]
    for q in [
        "What is the total deposit amount this month?",   # -> mongo
        "What does the kyc_status field mean?",           # -> chroma
        "Why is NGR negative this month?",                # -> mongo
        "What's the weather today?",                      # -> none
    ]:
        out = route_and_answer(q, uri)
        print(q, "->", out["route"], "|", out["reason"])