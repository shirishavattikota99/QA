import os
import time
from contextlib import asynccontextmanager
from typing import Any, Literal, Optional

from dotenv import load_dotenv
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
<<<<<<< HEAD
from fastapi.responses import FileResponse
from pathlib import Path

from pydantic import BaseModel, Field

load_dotenv()

from app.conversation import resolve_followup
from app.db import (
    close_db,
    get_conversation,
    get_conversation_turns,
    get_history,
    init_db,
    list_conversations,
    save_chat,
)
=======
from pydantic import BaseModel

load_dotenv()

from app.db import close_db, get_history, init_db, save_chat
>>>>>>> origin/main
from app.graph import ask
from app.helpers.logger import logger
from app.helpers.utils import getMongoDbUri
from app.middleware.auth import authenticate_api_key


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Open the PostgreSQL pool and create the table (no-op if DATABASE_URL is unset)
    await run_in_threadpool(init_db)
    yield
    close_db()


app = FastAPI(title="C-iq AI API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PromptMessage(BaseModel):
    prompt: str
    aiApiKey: str
    partnerId: str
    responseType: Literal["Text", "Graph", "Table"]
    aiLlm: Literal["Gemini", "OpenAi"]
    nodeEnv: Literal["production", "development", "local"]
    appClient: Literal["CORE", "3XE"]
<<<<<<< HEAD
    # Turns of one chat share this id. Send the same id with every message of a chat and a
    # follow-up ("and last month?") is understood in the context of the earlier questions.
    conversationId: Optional[str] = Field(default=None, max_length=64)
=======
>>>>>>> origin/main


class AiResponsePayload(BaseModel):
    error: str = ""
    type: Literal["Text", "Graph", "Table"] = "Text"
    response: Any = None
    suggestion: Optional[Any] = None


class AiResponseFormat(BaseModel):
    success: bool
    data: AiResponsePayload


def resolve_mongo_uri(payload: PromptMessage) -> str:
    """Pick the database for this partner (each partner has its own MongoDB)."""
    try:
        return getMongoDbUri(payload.nodeEnv, payload.appClient, payload.partnerId)
    except Exception:
        # Local testing only: fall back to MONGO_OPERATOR_URI from .env.
        # Never in production, or a partner could be answered from the wrong database.
        fallback = os.getenv("MONGO_OPERATOR_URI")
        if payload.nodeEnv != "production" and fallback:
            return fallback
        raise


@app.get("/api")
async def root():
    return {"message": "C-iq API is running"}


@app.post("/api/ai-prompt", dependencies=[Depends(authenticate_api_key)])
async def ai_chat(payload: PromptMessage, background_tasks: BackgroundTasks):
    started = time.perf_counter()
<<<<<<< HEAD
    conversation_id = (payload.conversationId or "").strip() or None
=======
>>>>>>> origin/main

    def elapsed_ms() -> int:
        return int((time.perf_counter() - started) * 1000)

    try:
        # Log safe fields only (the payload contains aiApiKey)
        logger.debug(
            "AI prompt received: partnerId=%s appClient=%s nodeEnv=%s",
            payload.partnerId, payload.appClient, payload.nodeEnv,
        )

        if not payload.prompt.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Prompt cannot be empty")
        if payload.aiLlm != "Gemini":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported LLM")
        if not payload.partnerId:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="partner id missing")

        mongo_uri = resolve_mongo_uri(payload)

<<<<<<< HEAD
        # Conversation continuity: a follow-up is rewritten into a standalone question using
        # the earlier turns of the same conversation. First questions are passed through as-is.
        resolved = payload.prompt.strip()
        if conversation_id:
            turns = await run_in_threadpool(get_conversation_turns, payload.partnerId, conversation_id)
            resolved = await run_in_threadpool(resolve_followup, resolved, turns)

        # The graph is synchronous; run it in a worker thread so the server stays responsive
        result = await run_in_threadpool(ask, resolved, mongo_uri)

        record = dict(
=======
        # The graph is synchronous; run it in a worker thread so the server stays responsive
        result = await run_in_threadpool(ask, payload.prompt, mongo_uri)

        # Save after the response is sent, so history never slows down or breaks the chat
        background_tasks.add_task(
            save_chat,
>>>>>>> origin/main
            partner_id=payload.partnerId,
            app_client=payload.appClient,
            node_env=payload.nodeEnv,
            question=payload.prompt,
            answer=result["answer"],
            success=True,
            generated_query=result["query"],
            row_count=result["row_count"],
            duration_ms=elapsed_ms(),
            route=result["route"],
            sources=[f"{x['type']}:{x['name']}" for x in result["sources"]],
<<<<<<< HEAD
            conversation_id=conversation_id,
            resolved_question=resolved if resolved != payload.prompt.strip() else None,
        )
        if conversation_id:
            # Save before replying: the user's next follow-up reads this turn back as context
            await run_in_threadpool(lambda: save_chat(**record))
        else:
            # Save after the response is sent, so history never slows down or breaks the chat
            background_tasks.add_task(save_chat, **record)
=======
        )
>>>>>>> origin/main

        return {
            "success": True,
            "data": {
                "response": result["answer"],
                "type": "Text",
                "route": result["route"],      # "database", "documents" or "both"
                "sources": result["sources"],  # e.g. [{"type": "database", "name": "transactions"}]
<<<<<<< HEAD
                "conversationId": conversation_id,
                # What was actually asked, when a follow-up was rewritten (else null)
                "resolvedQuestion": record["resolved_question"],
                # For the "Generated query" panel (every attempt, retries included)
                "generatedQuery": result["query"],
                "rowCount": result["row_count"],
                "durationMs": record["duration_ms"],
                # Raw query error / model text can contain internals: development only
                "queryError": result.get("error") if payload.nodeEnv != "production" else None,
                "modelNote": result.get("model_note") if payload.nodeEnv != "production" else None,
=======
>>>>>>> origin/main
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error in ai_chat: %s", e)
        background_tasks.add_task(
            save_chat,
            partner_id=payload.partnerId,
            app_client=payload.appClient,
            node_env=payload.nodeEnv,
            question=payload.prompt,
            answer=None,
            success=False,
            error=str(e),
            duration_ms=elapsed_ms(),
<<<<<<< HEAD
            conversation_id=conversation_id,
=======
>>>>>>> origin/main
        )
        # Real message outside production; generic in production (it can contain internals)
        detail = str(e) if payload.nodeEnv != "production" else "Something went wrong. Please try again."
        return {"success": False, "data": {"error": detail}}


@app.get("/api/ai-history", dependencies=[Depends(authenticate_api_key)])
async def ai_history(partnerId: str, limit: int = 50):
    """Latest saved questions and answers for one partner."""
    rows = await run_in_threadpool(get_history, partnerId, limit)
    return {"success": True, "data": rows}


<<<<<<< HEAD
@app.get("/api/ai-conversations", dependencies=[Depends(authenticate_api_key)])
async def ai_conversations(partnerId: str, limit: int = 50):
    """Saved chats for one partner, newest first (id, title, number of turns, times)."""
    rows = await run_in_threadpool(list_conversations, partnerId, limit)
    return {"success": True, "data": rows}


@app.get("/api/ai-conversation", dependencies=[Depends(authenticate_api_key)])
async def ai_conversation(partnerId: str, conversationId: str):
    """Every question and answer of one saved chat, oldest first."""
    rows = await run_in_threadpool(get_conversation, partnerId, conversationId)
    return {"success": True, "data": rows}


CHAT_PAGE = Path(__file__).resolve().parent / "static" / "chat.html"


@app.get("/chat", include_in_schema=False)
async def chat_page():
    """The chat web page. It calls the /api endpoints above on the same server."""
    return FileResponse(CHAT_PAGE)


=======
>>>>>>> origin/main
# run the app
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True,
    )