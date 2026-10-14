from langchain.agents.middleware import AgentMiddleware, before_model, AgentState
from typing import NotRequired
from app.helpers.utils import get_db_name, getMongoDbUri

class MongoState(AgentState):
    mongo_uri: NotRequired[str]
    partner_id: NotRequired[str]
    app_client: NotRequired[str]
    node_env: NotRequired[str]

class MongoMiddleware(AgentMiddleware):
    state_schema = MongoState

    def before_model(self, state: MongoState, runtime, **kwargs):
        partner_id = state.get("partner_id")
        app_client = state.get("app_client")
        node_env = state.get("node_env", "development")

        if partner_id and app_client:
            # inject mongo URI
            mongo_uri = getMongoDbUri(node_env, app_client, partner_id)
            return {"mongo_uri": mongo_uri}

        return None
