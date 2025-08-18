from tools.planner.execute_plan_tool import execute_plan
import re
from llm_factory.google import GoogleGen
from langchain_core.messages import AIMessage,HumanMessage,SystemMessage,ToolMessage,RemoveMessage
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
    env = Environment(loader=FileSystemLoader(os.path.join(current_dir,'..', '..', 'prompts', 'templates')))
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
        ## prepare planner prompt:
        system_prompt= load_prompt("planner_prompt.jinja",
            codebase=state['codebase'])
        ## Create messages for the planner
        if len(state["planner_messages"])>1:
            messages = [
                HumanMessage(content=f"User Query: {state['query']}\n")
            ]
        else:
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
        logger.info(f'planner agent thought: {response[0].content}\n')
        logger.info(f'planner agent call tools: {response[0].additional_kwargs}\n\n') 
        pattern = r"\*\*Plan\*\*.*\*\*Reasoning\*\*.*\*\*step\d+\*\*"
        if re.search(pattern, response[0].content, re.DOTALL | re.IGNORECASE):
            return {"planner_messages":response,"current_plan":response[0].content,"agent_response":response[0].content}
        return {"planner_messages":response,"agent_response":response[0].content}
    
    def final_state(self,state):
        # USED to clean cache if ANY
        logger.info('entering Planner final state')
        logger.info(f'This is the current repository branch {state["current_repo_branch"]}')
        return {}