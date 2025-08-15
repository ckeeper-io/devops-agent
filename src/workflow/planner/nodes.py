from tools.planner.execute_plan_tool import execute_plan
from utilis.gcp.get_sakey import download_save_sakey
from utilis.gcp.get_sandbox import download_codebase
from utilis.gcp.save_sandbox import upload_codebase
import re
from llm_factory.google import GoogleGen
from langchain_core.messages import AIMessage,HumanMessage,SystemMessage,ToolMessage,RemoveMessage
import time
import os

import  logging
from jinja2 import Environment, FileSystemLoader

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
current_dir = os.path.dirname(os.path.abspath(__file__))

def load_prompt(template_name, **kwargs):
    env = Environment(loader=FileSystemLoader(os.path.join(current_dir, '..', 'prompts', 'templates')))
    template = env.get_template(template_name)
    return template.render(**kwargs)


class Nodes():
    def __init__(self):
        self.llm_obj=GoogleGen()
        self.tools=[execute_plan]
        self.tool_names=[func.__name__ for func in self.tools]
        self.llm_obj.llm_with_tools=self.llm_obj.llm.bind_tools(self.tools)
    def initiate_state(self,state):
        logger.info('entering Planner initial state')
        ## Download current session sandbox from  GCS bucket (if it does not exist then create a new bucket with session_id)
        download_codebase(state=state)
        ## save sa_key
        download_save_sakey(state=state)
        ## prepare planner prompt:
        system_prompt= load_prompt("planner_prompt.jinja",
            codebase=state['codebase'],
            tool_names=self.tool_names)
        ## Create messages for the planner
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"User Query: {state['query']}\n")
        ]
        return {"planner_messages":messages}
    def planner(self, state):
        """
        Planner node that analyzes the query and creates a plan for execution.
        Uses the LLM to generate a step-by-step plan based on the user query.
        """
        logger.info('entering planner node')
        response=[self.llm_obj.llm_with_tools.invoke(state['planner_messages'])]
        pattern = r"\*\*Plan\*\*.*\*\*Reasoning\*\*.*\*\*step\d+\*\*"
        if re.search(pattern, response["planner_messages"][-1].content, re.DOTALL | re.IGNORECASE):
            return {"planner_messages":response,"current_plan":response["planner_messages"][-1].content}
        return {"planner_messages":response}
    
    def final_state(self,state):
        # USED to clean cache if ANY
        logger.info('entering Planner final state')
        # Upload the current session box into bucket
        upload_codebase(state=state)
        return {}