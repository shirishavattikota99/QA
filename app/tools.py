import os
from typing import List, Optional
from langchain_mongodb.agent_toolkit.database import MongoDBDatabase
from langchain_mongodb.agent_toolkit.toolkit import MongoDBDatabaseToolkit
from app.brain import Brain
from langchain.tools import tool
from app.skills import SKILLS

# Collections the LLM must never see or query: credentials, CMS/content, jobs,
# settings. Hiding them saves tokens (shorter collection list) and is safer.
# Edit this list to match your project.
IGNORED_COLLECTIONS = [
    "communicationCredentials", "emailCredentials", "settings",
    "agendaJobs", "asset", "assets", "banners", "customComponents",
    "dynamicPages", "pageContents", "pageLayouts", "pagelayouts", "pages",
    "languages", "translate",
]


def get_langchain_mongodb_tools(
    connection_string: Optional[str] = None,
    llm=None,
) -> dict:
    """
    Return tools from `langchain-mongodb` toolkit
    """
    mongo_uri = connection_string
    if not mongo_uri:
        raise ValueError("MongoDB connection string is required. Pass `connection_string")

    database = MongoDBDatabase.from_connection_string(
        mongo_uri,
        # 0 = do NOT append 3 full sample documents to every schema. They cost
        # thousands of tokens and contain personal data (emails, phones, hashes).
        # The field list (names + types) is still returned.
        sample_docs_in_collection_info=0,
        ignore_collections=IGNORED_COLLECTIONS,
    )
    model = llm
    toolkit = MongoDBDatabaseToolkit(db=database, llm=model)
    tools = toolkit.get_tools()
    context = toolkit.get_context()
    return {"tools": tools, "context": context}


@tool
def mongodb_collection_descriptions() -> str:
    """Provides descriptions of MongoDB collections and their usage."""
    for skill in SKILLS:
        if skill["name"] == "mongodb_collection_descriptions":
            return skill["content"]
    return "No collection descriptions available."


@tool
def load_skill(skill_name: str) -> str:
    """Load the full content of a skill into the agent's context.

    Use this when you need detailed information about how to handle a specific
    type of request. This will provide you with comprehensive instructions,
    policies, and guidelines for the skill area.

    Args:
        skill_name: The name of the skill to load (e.g., "mongodb_collection_descriptions")
    """
    for skill in SKILLS:
        if skill["name"] == skill_name:
            return f"Loaded skill: {skill_name}\n\n{skill['content']}"

    available = ", ".join(s["name"] for s in SKILLS)
    return f"Skill '{skill_name}' not found. Available skills: {available}"


if __name__ == "__main__":
    res = get_langchain_mongodb_tools(os.getenv("MONGO_OPERATOR_URI"), Brain().llm)
    for t in res["tools"]:
        print(f"{t.name}: {t.description}\n")