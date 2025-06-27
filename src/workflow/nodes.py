import sys
from tools.edit_tool import *
from tools.pr_tool import *
from tools.view_tool import *
from tools.search_tool import *
from tools.terraform_tool import *
from tools.create_file_tool import *
from tools.list_directory_contents_tool import *
from tools.clone_repository_tool import *
from utilis.gcp.get_sakey import download_save_sakey
from llm_factory.google_gen import GoogleGen
from llm_factory.openrouter_gen import OpenrouterGen
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
class Nodes():
    def __init__(self):
        self.llm_obj=GoogleGen()
        self.tools=[edit,create_pull_request,view,search,terraform_command_executor,create_file,list_directory_contents,clone_repository]
        self.tool_names=[func.__name__ for func in self.tools]
        self.llm_obj.llm_with_tools=self.llm_obj.llm.bind_tools(self.tools)
    def initiate_state(self,state):
        logger.info('entering initial state')
        ## save sa_key
        download_save_sakey(state["sa_key_bucket_link"],user_dir=state['user_dir'])
        return {}
    def get_category(self,state):

        env = Environment(loader=FileSystemLoader(os.path.join(current_dir, "..", "prompts","templates")))
        tmpl = env.get_template("category_router_system_prompt.jinja")
        system_prompt=tmpl.render({})

        prompt="""
        query: {query}
        """.format(query=state['query'])

        prompt=[SystemMessage(content=system_prompt),HumanMessage(content=prompt)]
        response=self.llm_obj.llm.invoke(prompt)
        if response.content[0]=="`":
            response.content=response.content[7:-4]
        response = json.loads(response.content)
        logger.info(response['query_category'])
        return {'query_category':response['query_category']}

    def prepare_prompt(self,state):
        logger.info("preparing the prompt//////")
        env = Environment(loader=FileSystemLoader(os.path.join(current_dir, "..", "prompts","templates")))
        tmpl = env.get_template("main_agent_system_prompt.jinja")
        system_prompt=tmpl.render({"query_category":state['query_category'],"tool_names":self.tool_names,"codebase":state['codebase']})

        prompt="""
        query: {query}
        """.format(query=state['query'])

        prompt=[SystemMessage(content=system_prompt),HumanMessage(content=prompt)]
        logger.info("the prompt is prepared")
        return {'messages':prompt}


    def agent(self,state):
        logger.info('We are in the agent node////')
        response=[self.llm_obj.llm_with_tools.invoke(state['messages'])]
        logger.info(f'Agent thought: {response[0]}') 
        logger.info('Agent sleeping')
        time.sleep(10)
        logger.info('Wake up')
        return {"messages":response}
    

    
    def final_state(self,state):
        # USED to clean cache if ANY
        logger.info('entering final state')
        return {}