"""Offline test for conversation continuity (no Gemini/Claude key, no MongoDB needed).

Run from the project root:
    python scripts/test_conversation.py

It replaces the query graph and the language model with small fakes, then calls the real
FastAPI app + SQLite history to check that:
  * a follow-up is rewritten using the earlier turns of the SAME conversation,
  * a first question, or a question in a new conversation, is passed through unchanged,
  * conversations never leak between partners or chats,
  * failed turns are not used as context, and a failed rewrite falls back to the question,
  * history can be listed and reopened.
"""
import os
import sys
import tempfile
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

os.environ["SQLITE_PATH"] = os.path.join(tempfile.mkdtemp(), "test_history.db")
os.environ["AUTH_API_KEY"] = "test-key"
os.environ["MONGO_OPERATOR_URI"] = "mongodb://unused"
os.environ.pop("DATABASE_URL", None)

# --- fake query graph: answers with the exact question it was given -------------------------
asked = []  # questions that reached the graph


def fake_ask(question, mongo_uri=None):
    asked.append(question)
    if "boom" in question:
        raise RuntimeError("query failed")
    return {"answer": f"ANSWER[{question}]", "route": "database", "sources": [{"type": "database", "name": "players"}],
            "data": None, "query": "db.players.aggregate([])", "row_count": 1}


graph_stub = types.ModuleType("app.graph")
graph_stub.ask = fake_ask
sys.modules["app.graph"] = graph_stub

# --- fake rewriter model: records what it was shown, rewrites "and X?" follow-ups -----------
import app.conversation as conversation  # noqa: E402


class FakeLLM:
    def __init__(self):
        self.calls = []
        self.fail = False

    def invoke(self, messages):
        if self.fail:
            raise RuntimeError("model unavailable")
        prompt = messages[-1].content
        self.calls.append(prompt)
        newest = prompt.split("Newest message:")[1].strip()
        if newest.lower().startswith("and "):
            earlier = prompt.split("Earlier turns:")[1].split("Newest message:")[0]
            last_question = [ln for ln in earlier.splitlines() if ln.startswith("User:")][-1][6:]
            return types.SimpleNamespace(content=f"{last_question} (changed: {newest[4:]})")
        return types.SimpleNamespace(content=newest)


llm = FakeLLM()
conversation._llm = llm

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402

BODY = dict(aiApiKey="x", partnerId="P1", responseType="Text", aiLlm="Gemini", nodeEnv="local", appClient="CORE")
QS = "?apiKey=test-key"
checks = []


def check(name, ok, detail=""):
    checks.append(ok)
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"  -> {detail}"))


def post(client, prompt, conversation_id=None, partner="P1"):
    body = dict(BODY, prompt=prompt, partnerId=partner)
    if conversation_id:
        body["conversationId"] = conversation_id
    return client.post("/api/ai-prompt" + QS, json=body).json()


with TestClient(main.app) as client:
    # 1. first question: no history, no model call, unchanged
    r = post(client, "top affiliates this month", "c1")
    check("first question passes through", asked[-1] == "top affiliates this month" and r["data"]["resolvedQuestion"] is None, (asked, r))
    check("no rewrite call without history", len(llm.calls) == 0, llm.calls)

    # 2. follow-up in the same conversation: rewritten with context
    r = post(client, "and last month?", "c1")
    check("follow-up is rewritten", asked[-1] == "top affiliates this month (changed: last month?)", asked[-1])
    check("rewrite saw the first question and its answer",
          "top affiliates this month" in llm.calls[-1] and "ANSWER[top affiliates this month]" in llm.calls[-1], llm.calls[-1])
    check("response reports what was asked", r["data"]["resolvedQuestion"] == asked[-1], r)

    # 3. a third turn builds on the rewritten question, not the raw "and last month?"
    r = post(client, "and withdrawals?", "c1")
    check("context uses the standalone question of earlier turns",
          asked[-1] == "top affiliates this month (changed: last month?) (changed: withdrawals?)", asked[-1])

    # 4. same words in a NEW conversation get no context
    n = len(llm.calls)
    post(client, "and last month?", "c2")
    check("new conversation has no context", asked[-1] == "and last month?" and len(llm.calls) == n, asked[-1])

    # 5. another partner cannot read conversation c1
    post(client, "and yesterday?", "c1", partner="P2")
    check("conversations are isolated per partner", asked[-1] == "and yesterday?", asked[-1])

    # 6. a failed turn is not used as context
    bad = post(client, "boom question", "c3")
    check("failed turn returns an error", bad["success"] is False, bad)
    post(client, "players per country", "c3")
    post(client, "and last year?", "c3")
    check("failed turn skipped in context", "boom" not in llm.calls[-1] and asked[-1].startswith("players per country"), llm.calls[-1])

    # 7. rewrite failure falls back to the original question
    llm.fail = True
    r = post(client, "and last week?", "c1")
    check("rewrite failure uses original question", asked[-1] == "and last week?" and r["success"], (asked[-1], r))
    llm.fail = False

    # 8. no conversationId (old clients): unchanged behaviour
    n = len(llm.calls)
    r = post(client, "and last month?")
    check("no conversationId means no rewrite", asked[-1] == "and last month?" and len(llm.calls) == n, asked[-1])

    # 9. history endpoints
    convs = client.get("/api/ai-conversations" + QS + "&partnerId=P1").json()["data"]
    by_id = {c["conversation_id"]: c for c in convs}
    check("conversation list has titles and turn counts",
          by_id["c1"]["title"] == "top affiliates this month" and by_id["c1"]["turns"] == 4 and set(by_id) == {"c1", "c2", "c3"}, convs)
    check("most recently used conversation first", [c["conversation_id"] for c in convs] == ["c1", "c3", "c2"], [c["conversation_id"] for c in convs])
    turns = client.get("/api/ai-conversation" + QS + "&partnerId=P1&conversationId=c1").json()["data"]
    check("reopened conversation is complete and ordered",
          [t["question"] for t in turns] == ["top affiliates this month", "and last month?", "and withdrawals?", "and last week?"]
          and turns[1]["resolved_question"] == "top affiliates this month (changed: last month?)", turns)
    other = client.get("/api/ai-conversation" + QS + "&partnerId=P2&conversationId=c1").json()["data"]
    check("other partner only sees their own turns", all(t["question"] == "and yesterday?" for t in other), other)

    # 10. API key still required, UI page served
    check("history needs the api key", client.get("/api/ai-conversations?partnerId=P1").status_code == 401)
    page = client.get("/chat")
    check("chat page is served", page.status_code == 200 and "<html" in page.text.lower(), page.status_code)

print(f"\n{sum(checks)}/{len(checks)} checks passed")
sys.exit(0 if all(checks) else 1)
