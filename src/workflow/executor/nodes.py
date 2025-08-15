import sys
from tools.executor.edit_tool import edit
from tools.executor.pr_tool import create_pull_request
from tools.executor.view_tool import view
from tools.executor.search_tool import search
from tools.executor.gcloud_command_tool import run_gcloud_command
from tools.executor.terraform_tool import terraform_command_executor
from tools.executor.create_file_tool import create_file
from tools.executor.list_directory_contents_tool import list_directory_contents
from tools.executor.retrieve_log_tool import retrieve_logs
from tools.executor.git_commands_tool import run_git_command
from tools.executor.push_github_tool import push_changes
import re
from llm_factory.google import GoogleGen
from langchain_core.messages import AIMessage,HumanMessage,SystemMessage,ToolMessage,RemoveMessage
import time
import subprocess
import os
from pathlib import Path
import shutil
import json
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
        self.tools=[edit,
        create_pull_request,
        view,
        terraform_command_executor,
        create_file,
        list_directory_contents,
        retrieve_logs,
        run_gcloud_command,
        run_git_command,
        push_changes]
        self.tool_names=[func.__name__ for func in self.tools]
        self.llm_obj.llm_with_tools=self.llm_obj.llm.bind_tools(self.tools)
    def initiate_state(self,state):
        logger.info('entering Executor initial state')
        system_prompt= load_prompt("executor_prompt.jinja",
            codebase=state['codebase'],
            tool_names=self.tool_names,
            plan=state["current_plan"])
        return {"executor_messages":[SystemMessage(content=system_prompt),HumanMessage(content=".")]}
    
    def executor(self, state):
        """
        Executor node that takes the plan and executes the necessary tools.
        Uses the LLM with tools to execute the planned actions.
        """
        logger.info('entering executor node')
        response=[self.llm_obj.llm_with_tools.invoke(state['executor_messages'])]
        logger.info(f'executor agent thought: {response[0].content}\n')
        logger.info(f'executor agent call tools: {response[0].additional_kwargs}\n\n') 
        logger.info('Agent sleeping')
        # time.sleep(6)
        logger.info('Wake up')
        return {"executor_messages":response}
    def final_state(self,state):
        # USED to clean cache if ANY
        logger.info('entering Executor final state')
        return {}