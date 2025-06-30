import sys
from tools.edit_tool import *
from tools.pr_tool import *
from tools.view_tool import *
from tools.search_tool import *
from tools.terraform_tool import *
from tools.create_file_tool import *
from tools.list_directory_contents_tool import *
from workflow.nodes import Nodes
from workflow.state import State
import requests
from typing import Any
import json
from typing_extensions import Annotated
from langgraph.graph import START,END,StateGraph
from langgraph.prebuilt import ToolNode,tools_condition
from langgraph.checkpoint.memory import MemorySaver
import os

current_dir = os.path.dirname(os.path.abspath(__file__))

class WorkFlow():
    def __init__(self,user_dir):
        nodes=Nodes()
        self.workflow=StateGraph(State)
        #NODES
        self.workflow.add_node('initiate_state',nodes.initiate_state)
        self.workflow.add_node('get_category',nodes.get_category)
        self.workflow.add_node('prepare_prompt',nodes.prepare_prompt)
        self.workflow.add_node('agent',nodes.agent)
        self.workflow.add_node('tools',ToolNode(nodes.tools))
        self.workflow.add_node('final_state',nodes.final_state)

        #EDGES
        self.workflow.add_edge(START,'initiate_state')
        self.workflow.add_edge('initiate_state','get_category')
        self.workflow.add_edge('get_category','prepare_prompt')
        self.workflow.add_edge('prepare_prompt','agent')
        self.workflow.add_conditional_edges('agent',tools_condition,{'tools':'tools','__end__':"final_state"})
        self.workflow.add_edge('tools','agent')

        memory=MemorySaver()
        self.workflow = self.workflow.compile(checkpointer=memory)
        self.config={'configurable':{'thread_id':user_dir},"recursion_limit": 50}
    def __call__(self,issue,user_dir):
        response=self.workflow.invoke({"query":issue['query'],
                                       "codebase":issue['codebase'],
                                       "githubapp_id":"1472998",
                                       "githubapp_installation_id":issue['github_app_installation_id'],
                                       "githubapp_privatekey_link":os.environ.get("GITHUBAPP_PRIVATE_KEY_LINK"),
                                       "sa_key_bucket_link":issue['sa_key_bucket_link'],
                                       "query_category":"",
                                       "user_dir":user_dir
                                       },self.config)
        return response
    def start_specific_node(self,state,starting_node):        
        self.workflow.set_entry_point(starting_node)
        response=self.workflow.invoke(state)
        return response
    def show_state(self):
        for m in self.workflow.get_state(self.config).values['messages']:
            m.pretty_print()
    def return_state_value(self,state_name):
        state_value_list=[]
        for m in self.workflow.get_state(self.config).values[state_name]:
            state_value_list.append(m)
        return state_value_list