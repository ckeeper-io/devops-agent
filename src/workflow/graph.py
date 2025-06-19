import sys
from workflow.nodes import Nodes
from workflow.state import State
import requests
from typing import Any
import json
from typing_extensions import Annotated
from langgraph.prebuilt import InjectedState
# from helper_functions.tools import *
from langgraph.graph import START,END,StateGraph
from langgraph.prebuilt import ToolNode,tools_condition
from langgraph.checkpoint.memory import MemorySaver
from tools.gcp_tools import *
import os

current_dir = os.path.dirname(os.path.abspath(__file__))

class WorkFlow():
    def __init__(self):
        nodes=Nodes()
        tools=[]

        self.workflow=StateGraph(State)
        #NODES
        self.workflow.add_node('initiate_state',nodes.initiate_state)
        self.workflow.add_node('prepare_prompt',nodes.prepare_prompt)
        self.workflow.add_node('agent',nodes.agent)
        self.workflow.add_node('tools',ToolNode(tools))
        self.workflow.add_node('final_state',nodes.final_state)

        #EDGES
        self.workflow.add_edge(START,'initiate_state')
        self.workflow.add_edge('initiate_state','prepare_prompt')
        self.workflow.add_edge('prepare_prompt','agent')
        self.workflow.add_conditional_edges('agent',tools_condition,{'tools':'tools','__end__':"final_state"})
        self.workflow.add_edge('tools','agent')
        memory=MemorySaver()
        self.workflow = self.workflow.compile(checkpointer=memory)
        self.config={'configurable':{'thread_id':'1'}}
    def __call__(self,issue):
        response=self.workflow.invoke({"query":issue['query'],"github_repositories":issue['github_repositories'],"github_token":issue['github_token']},self.config)
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