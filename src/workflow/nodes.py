import sys
from tools.edit_tool import edit
from tools.pr_tool import create_pull_request
from tools.view_tool import view
from tools.search_tool import search
from tools.gcloud_command_tool import run_gcloud_command
from tools.terraform_tool import terraform_command_executor
from tools.create_file_tool import create_file
from tools.list_directory_contents_tool import list_directory_contents
from tools.retrieve_log_tool import retrieve_logs
from tools.git_commands_tool import run_git_command
from tools.push_github_tool import push_changes
from utilis.gcp.get_sakey import download_save_sakey
from utilis.gcp.get_sandbox import download_codebase
from utilis.gcp.save_sandbox import upload_codebase
from utilis.get_chathistory import get_chat_history
from utilis.step_action_markdown import step_action_markdown
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
        logger.info('entering initial state')
        ## Download current session sandbox from  GCS bucket (if it does not exist then create a new bucket with session_id)
        download_codebase(workspace_id=state["workspace_id"],session_id=state["session_id"],current_repo_branch=state["current_repo_branch"],codebase=state["codebase"],state=state)
        ## save sa_key
        download_save_sakey(state["sa_key_bucket_link"],session_id=state["session_id"])
        ## Get chat history
        chat_history= get_chat_history(session_id=state["session_id"])
        logger.info(f"Chat history: {chat_history}")
        return {"chat_history": chat_history}
    def router(self, state):
        """
        LLM-based router node that decides whether to send the query to the planner or to a simple chatbot.
        """

        logger.info('entering router node')
        if state["ask_step_approval"]== True:
            return "executor"
        system_prompt= load_prompt("router_prompt.jinja", chat_history=state["chat_history"])
        messages = [SystemMessage(content=system_prompt),
                    HumanMessage(content=f"User Query: {state['query']}\n")]
        response = self.llm_obj.llm.invoke(messages)
        decision = response.content.strip().lower()
        logger.info(f"Router decision: {decision}")
        if decision == "code":
            return "planner"
        else:
            return "chatbot"

    def chatbot(self, state):
        """
        Simple chatbot node for general conversation.
        """
        logger.info('entering chatbot node')
        system_prompt= load_prompt("chatbot_prompt.jinja", chat_history=state["chat_history"])
        messages = [SystemMessage(content=system_prompt),
                    HumanMessage(content=f"User Query: {state['query']}\n")]
        response = self.llm_obj.llm.invoke(messages)
        return {"agent_response": response.content,
                "input_tokens":response.usage_metadata["input_tokens"]+state.get('input_tokens',0),
                "output_tokens":response.usage_metadata["output_tokens"]+state.get('output_tokens',0)}
    def preplanner(self,state):
        trajectory = []
        for msg in state['executor_messages']:
            if isinstance(msg, (HumanMessage, SystemMessage)):
                continue
            elif isinstance(msg, AIMessage):
                trajectory.append({"from":"AI Executor", "content":msg.content})
                tool_calls = getattr(msg, 'tool_calls', None)
                if tool_calls:
                    for tool_call in msg.tool_calls:
                        trajectory.append({"from":"Tool Call", "name":tool_call["name"], "args": tool_call["args"], "id":tool_call["id"]})
            elif isinstance(msg, ToolMessage):
                tool_call_id = getattr(msg, 'tool_call_id', None)
                if tool_call_id:
                    trajectory.append({"from":"Tool Response", "content":msg.content,"id":tool_call_id})
        # previous_steps_actions=[]
        # tool_call_ids=[]
        # for step_action in state["previous_steps_actions"][:-3]:
        #     if step_action["from"] == "Tool Call" and step_action["name"] not in ["run_gcloud_command","retrieve_logs"]:
        #         tool_call_ids.append(step_action["id"])
        #         continue
        #     elif step_action["from"] == "Tool Call":
        #         previous_steps_actions.append(step_action)
        #     if step_action["from"] == "Tool Response" and step_action["id"] in tool_call_ids:
        #         previous_steps_actions.append(step_action)
        #     elif step_action["from"] == "Tool Response":
        #         continue
        #     if step_action["from"] in ["AI Executor","AI Planner"]:
        #         previous_steps_actions.append(step_action)
        #         tool_call_ids=[]
        # for step_action in state["previous_steps_actions"][-3:]:
        #     previous_steps_actions.append(step_action)

        # return {"previous_steps_actions":previous_steps_actions+trajectory}
        return {"previous_steps_actions":state.get("previous_steps_actions",[])+trajectory}
    def planner(self, state):
        """
        Planner node that analyzes the query and creates a plan for execution.
        Uses the LLM to generate a step-by-step plan based on the user query.
        """
        logger.info('entering planner state')
        step_action_markdown_format=step_action_markdown(state.get('previous_steps_actions',[]))
        ### PLANNER
        # Load the system prompt template
        system_prompt= load_prompt("planner_prompt.jinja",
            chat_history=state["chat_history"],
            codebase=state['codebase'],
            previous_steps_actions=step_action_markdown_format,
            tool_names=self.tool_names)
        # Create messages for the planner
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"User Query: {state['query']}\n")
        ]
        
        # Get response from LLM
        response = self.llm_obj.llm.invoke(messages)
        logger.info(f"CURRENT TASK\n {response.content}\n\n")

        ### EXECUTOR
        # Load the system prompt template
        system_prompt= load_prompt("executor_prompt.jinja",
            codebase=state['codebase'],
            tool_names=self.tool_names,
            previous_steps_actions=step_action_markdown_format,
            current_step=response.content)
        # logger.info(f"Executor SYSTEM PROMPT\n {system_prompt}\n\n")
        executor_messages= [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"User Query: {state['query']}\n")
        ]
        clear_messages = [RemoveMessage(id=msg.id) for msg in state['executor_messages']]
        # time.sleep(6)
        return {"executor_messages": clear_messages + executor_messages,
                "previous_steps_actions":state.get('previous_steps_actions',[])+[{"from":"AI Planner","content":response.content}],
                "step_action_markdown_format":step_action_markdown_format,
                "current_step":response.content,
                "plan":state.get('plan',[])+[response.content],
                "current_cycle":0,
                "current_recursion":state.get("current_recursion",0) + 1,
                "input_tokens":response.usage_metadata["input_tokens"]+state.get('input_tokens',0),
                "output_tokens":response.usage_metadata["output_tokens"]+state.get('output_tokens',0)}
    
    def executor(self, state):
        """
        Executor node that takes the plan and executes the necessary tools.
        Uses the LLM with tools to execute the planned actions.
        """
        logger.info('entering executor state')
        logger.info(f'{len(state["executor_messages"])}')
        logger.info(f'{len(state["messages_for_evaluation"])}')
        logger.info("------------------------------------------")
        logger.info(f"INPUT_TOKENS:-------->{state.get('input_tokens',0)}")
        logger.info(f"OUTPUT_TOKENS:------->{state.get('output_tokens',0)}")
        if isinstance(state['executor_messages'][-1], ToolMessage):
            logger.info(f"TOOL RESPONSE: {state['executor_messages'][-1].content}")
        if state["current_cycle"]<state["max_cycle_executor"]:
            response=[self.llm_obj.llm_with_tools.invoke(state['executor_messages'])]
        else:
            response=[AIMessage(content="Alright, What do you think?")]
            return {"executor_messages":response,"messages_for_evaluation":response,"current_cycle":state['current_cycle']+1}
        logger.info(f'executor agent thought: {response[0].content}\n')
        logger.info(f'executor agent call tools: {response[0].additional_kwargs}\n\n') 
        if len(state['executor_messages'])>2 and state['executor_messages'][-2].additional_kwargs==response[0].additional_kwargs:
            logger.info(f'Same call tool!')
            response=[AIMessage(content="Alright, What do you think?")]
            return {"executor_messages":response,"messages_for_evaluation":response,"current_cycle":state['current_cycle']+1}
        logger.info('Agent sleeping')
        # time.sleep(6)
        logger.info('Wake up')
        return {"executor_messages":response,
                "messages_for_evaluation":response,
                "current_cycle":state['current_cycle']+1,
                "current_recursion":state.get("current_recursion",0) + 1,
                "input_tokens":response[0].usage_metadata["input_tokens"]+state.get('input_tokens',0),
                "output_tokens":response[0].usage_metadata["output_tokens"]+state.get('output_tokens',0)}
    
    

    def planner_decision(self, state):
        """
        Decision function for the planner node.
        Determines whether to continue to executor or end the workflow.
        Checks if the current step indicates that the task is already completed or cannot be completed.
        """
        logger.info('making planner decision')

        current_step = state.get('current_step', '').strip().lower()

        # Check for structured completion response
        pattern = r"^reasoning:\s*(.+?)\s*step:\s*done$"
        if re.match(pattern, current_step, re.IGNORECASE | re.DOTALL):
            return 'summarizer'

        return "ask_step_approval_node"
    def summarizer(self, state):
        """
        Summarizer node that provides a user-friendly summary of what the planner did.
        """
        logger.info('entering summarizer node')
        system_prompt= load_prompt("summarizer_prompt.jinja",user_query=state['query'])
        messages = [SystemMessage(content=system_prompt),
                    HumanMessage(content=f"Planner Actions and Decisions:\n{state.get('step_action_markdown_format', '')}\n")] 
        response = self.llm_obj.llm.invoke(messages)
        return {"agent_response": response.content,
                "input_tokens":response.usage_metadata["input_tokens"]+state.get('input_tokens',0),
                "output_tokens":response.usage_metadata["output_tokens"]+state.get('output_tokens',0),
                "ask_step_approval":False}
    

    def ask_step_approval_node(self, state):
        return {"ask_step_approval":True}
    def final_state(self,state):
        # USED to clean cache if ANY
        logger.info('entering final state')
        # Upload the current session box into bucket
        upload_codebase(session_id=state["session_id"],current_repo_branch=state["current_repo_branch"])
        return {}