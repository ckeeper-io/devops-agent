import sys
from workflow.executor.nodes import Nodes
from workflow.executor.state import ExecutorState
import requests
from typing import Any
import json
from typing_extensions import Annotated
from langgraph.graph import START,END,StateGraph
from langgraph.prebuilt import ToolNode,tools_condition
from langgraph.checkpoint.memory import MemorySaver
import os
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
# from langfuse.langchain import CallbackHandler
current_dir = os.path.dirname(os.path.abspath(__file__))


def executor_tool_node(state):
    last_message = state['executor_messages'][-1]
    
    if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
        return {}
    
    tool_messages = []
    for tool_call in last_message.tool_calls:
        tool_name = tool_call['name']
        tool_args = tool_call['args']
        
        tool_func = None
        for tool in Nodes().tools:
            if tool.__name__ == tool_name:
                tool_func = tool
                break
        
        if tool_func:
            try:
                filtered_args = {k: v for k, v in tool_args.items() if k != 'state'}
                result = tool_func(**filtered_args, state=state)
                tool_message = ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call['id']
                )
                tool_messages.append(tool_message)
            except Exception as e:
                error_message = ToolMessage(
                    content=f"Error executing {tool_name}: {str(e)}",
                    tool_call_id=tool_call['id']
                )
                tool_messages.append(error_message)
    
    return {"executor_messages": tool_messages,"messages_to_planner":tool_messages}

def tools_condition_executor(state):
    messages = state.get("executor_messages", [])
    if not messages:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")
    
    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "executor_tool_node"
    return "final_state"

class WorkFlow():
    def __init__(self,request):
        nodes=Nodes()
        self.workflow=StateGraph(ExecutorState)
        self.workflow.add_node('initial_state',nodes.initiate_state)
        self.workflow.add_node('executor_agent',nodes.executor)
        self.workflow.add_node('executor_tool_node',executor_tool_node)
        self.workflow.add_node('final_state',nodes.final_state)

        self.workflow.add_edge(START,'initial_state')
        self.workflow.add_edge("initial_state",'executor_agent')
        self.workflow.add_conditional_edges('executor_agent',tools_condition_executor,{'executor_tool_node':'executor_tool_node','final_state':"final_state"})
        self.workflow.add_edge("executor_tool_node",'executor_agent')

        memory=MemorySaver()
        self.workflow = self.workflow.compile(checkpointer=memory)
        # self.langfuse_handler = CallbackHandler()
        # self.config={'configurable':{'thread_id':request.session_id},"recursion_limit": 200,"callbacks": [self.langfuse_handler]}
        self.config={'configurable':{'thread_id':f'{request["session_id"]}executor'},"recursion_limit": 200}
    def __call__(self,request,user_goal):
        response=self.workflow.invoke({
                                       "current_plan":f'User goal: {user_goal}\n{request.get("current_plan","")}',
                                       "codebase":request["codebase"],
                                       "session_id":request["session_id"],
                                       "workspace_id":request["workspace_id"],
                                       "githubapp_id":os.environ.get("GITHUBAPP_ID"),
                                       "githubapp_privatekey":os.environ.get("GITHUBAPP_PRIVATE_KEY"),
                                       "sa_key_bucket_link":request["sa_key_bucket_link"],
                                       "current_repo_branch":request["current_repo_branch"],
                                       "max_recursion_limit": 30,
                                       "current_recursion":0,
                                       "executor_messages":(request.get("executor_state",{})).get("executor_messages",[])
                                       },self.config)
        return response
    def return_state_value(self,state_name):
        state_value_list=[]
        for m in self.workflow.get_state(self.config).values[state_name]:
            state_value_list.append(m)
        return state_value_list