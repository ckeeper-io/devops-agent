from langgraph.prebuilt import InjectedState
from workflow.executor.graph import WorkFlow
from typing import Annotated
from langchain_core.messages import AIMessage,HumanMessage,SystemMessage,ToolMessage,RemoveMessage


def action_markdown(messages):
    trajectory = []
    for msg in messages:
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
    action_markdown_format="\n"
    for action in trajectory:
        action_markdown_format+=f"## {action['from']}\n"
        if action["from"] in ["AI Executor","AI Planner"]:
            action_markdown_format+=f"{action['content']}\n"
        if action["from"] == "Tool Call":
            action_markdown_format+=f"name: {action['name']}\n"
            action_markdown_format+=f"args: {action['args']}\n"
        if action["from"] == "Tool Response":
            action_markdown_format+=f"response: {action['content']}\n"
    return action_markdown_format

def execute_plan(state: Annotated[dict, InjectedState]):
    """
        This tool execute the last plan approved by the user.
        It returns the action trajectory of the executor
    """
    work_flow = WorkFlow(request=state)
    response=work_flow(request=state)
    action_markdown_format=action_markdown(response["executor_messages"])
    print(f"The executor trajectory:\n {action_markdown_format}")
    return action_markdown_format