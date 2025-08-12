

def step_action_markdown(previous_steps_actions):
    step_action_markdown_format="\n"
    for step_action in previous_steps_actions:
        step_action_markdown_format+=f"## {step_action['from']}\n"
        if step_action["from"] in ["AI Executor","AI Planner"]:
            step_action_markdown_format+=f"{step_action['content']}\n"
        if step_action["from"] == "Tool Call":
            step_action_markdown_format+=f"name: {step_action['name']}\n"
            step_action_markdown_format+=f"args: {step_action['args']}\n"
        if step_action["from"] == "Tool Response":
            step_action_markdown_format+=f"response: {step_action['content']}\n"
    return step_action_markdown_format