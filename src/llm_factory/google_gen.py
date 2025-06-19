from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv


class GoogleGen():
    def __init__(self):
        load_dotenv()
        self.llm=ChatGoogleGenerativeAI(model='gemini-2.0-flash')
    
    def __call__(self, messages):
        response=self.llm.invoke(messages)
        return response
    