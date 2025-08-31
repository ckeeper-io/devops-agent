import json
from google.oauth2 import service_account
from langchain_google_vertexai import ChatVertexAI
from llm_factory.llm_config import LLM_CONFIG
import os


class VertexAIGen():
    def __init__(self):
        config = LLM_CONFIG["vertex_ai"]
        sa_key = os.getenv(config["SA_KEY"])
        credentials = service_account.Credentials.from_service_account_info(
            json.loads(sa_key)
        )
        self.llm = ChatVertexAI(
            model="gemini-2.5-pro",
            project=sa_key["project_id"],
            location="europe-west1",
            credentials=credentials,
        )
    def __call__(self, messages):
        response=self.llm.invoke(messages)
        return response