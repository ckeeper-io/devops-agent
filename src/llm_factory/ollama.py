from langchain_ollama import ChatOllama
from dotenv import load_dotenv
from llm_factory.llm_config import LLM_CONFIG


class OllamaGen():
    def __init__(self):
        load_dotenv()
        config = LLM_CONFIG["ollama"]
        self.llm = ChatOllama(model=config["model_name"], base_url=config["base_url"], temperature=0)
    
    def __call__(self, messages):
        response = self.llm.invoke(messages)
        return response