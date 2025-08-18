import sys
from workflow.planner.nodes import Nodes
from workflow.planner.state import PlannerState
import requests
from typing import Any
import json
from typing_extensions import Annotated
from langgraph.graph import START,END,StateGraph
from langgraph.prebuilt import ToolNode,tools_condition
from langgraph.checkpoint.memory import MemorySaver
from utlis.convert_raw_langchain_messages import raw_to_messages
import os
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
# from langfuse.langchain import CallbackHandler
current_dir = os.path.dirname(os.path.abspath(__file__))


def planner_tool_node(state):
    last_message = state['planner_messages'][-1]
    if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
        return {}

    tool_messages = []
    state_updates = {}

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
                # Filter out injected params
                filtered_args = {k: v for k, v in tool_args.items() if k != 'state'}
                result = tool_func(**filtered_args, state=state)

                # Handle Command-returning tools
                if isinstance(result, Command):
                    updates = result.update or {}
                    state_updates.update(updates)

                    tool_message = ToolMessage(
                        content=str(updates),   # you can use action_markdown_format if you want cleaner output
                        tool_call_id=tool_call['id'],
                        name=tool_name
                    )
                else:
                    tool_message = ToolMessage(
                        content=str(result),
                        tool_call_id=tool_call['id'],
                        name=tool_name
                    )

                tool_messages.append(tool_message)

            except Exception as e:
                error_message = ToolMessage(
                    content=f"Error executing {tool_name}: {str(e)}",
                    tool_call_id=tool_call['id'],
                    name=tool_name
                )
                tool_messages.append(error_message)

    # Merge tool messages + any state updates from Command
    return {
        "planner_messages": tool_messages,
        **state_updates
    }



def tools_condition_planner(state):
    messages = state.get("planner_messages", [])
    if not messages:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")
    
    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "planner_tool_node"
    return "final_state"

class WorkFlow():
    def __init__(self,request):
        nodes=Nodes()
        self.workflow=StateGraph(PlannerState)
        #NODES
        self.workflow.add_node('initiate_state',nodes.initiate_state)
        self.workflow.add_node('planner',nodes.planner)
        self.workflow.add_node('planner_tool_node',planner_tool_node)
        self.workflow.add_node('final_state',nodes.final_state)

        #EDGES
        self.workflow.add_edge(START,'initiate_state')
        self.workflow.add_edge('initiate_state',"planner")
        self.workflow.add_conditional_edges('planner',tools_condition_planner,{'planner_tool_node':'planner_tool_node','final_state':"final_state"})
        self.workflow.add_edge('planner_tool_node',"planner")

        memory=MemorySaver()
        self.workflow = self.workflow.compile(checkpointer=memory)
        # self.langfuse_handler = CallbackHandler()
        # self.config={'configurable':{'thread_id':request.session_id},"recursion_limit": 200,"callbacks": [self.langfuse_handler]}
        self.config={'configurable':{'thread_id':request.session_id},"recursion_limit": 10}
    def __call__(self,request):
        response=self.workflow.invoke({"query":request.query,
                                       "codebase":request.codebase,
                                       "session_id":request.session_id,
                                       "workspace_id":request.workspace_id,
                                       "githubapp_id":os.environ.get("GITHUBAPP_ID"),
                                       "githubapp_privatekey":os.environ.get("GITHUBAPP_PRIVATE_KEY"),
                                       "sa_key_bucket_link":request.sa_key_bucket_link,
                                       "current_repo_branch":request.state.get("current_repo_branch",[]),
                                       "planner_messages":raw_to_messages(request.state.get("planner_messages",[])),
                                       "current_plan":request.state.get("current_plan","")
                                       },self.config)
        return response
    def return_state_value(self,state_name):
        state_value_list=[]
        for m in self.workflow.get_state(self.config).values[state_name]:
            state_value_list.append(m)
        return state_value_list