from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, AIMessage

def raw_to_messages(raw_messages):
    # Keep track of tool_calls by ID → name
    tool_call_lookup = {}

    # First pass: collect tool call mappings from AI messages
    for m in raw_messages:
        if m["type"] == "ai" and "tool_calls" in m:
            for tc in m["tool_calls"]:
                tool_call_lookup[tc["id"]] = tc["name"]

    def convert_message(m):
        if m["type"] == "system":
            return SystemMessage(
                content=m["content"],
                additional_kwargs=m.get("additional_kwargs", {}),
                response_metadata=m.get("response_metadata", {}),
                name=m.get("name"),
                id=m.get("id"),
            )
        elif m["type"] == "human":
            return HumanMessage(
                content=m["content"],
                additional_kwargs=m.get("additional_kwargs", {}),
                response_metadata=m.get("response_metadata", {}),
                name=m.get("name"),
                id=m.get("id"),
            )
        elif m["type"] == "ai":
            return AIMessage(
                content=m["content"],
                additional_kwargs=m.get("additional_kwargs", {}),
                response_metadata=m.get("response_metadata", {}),
                name=m.get("name"),
                id=m.get("id"),
                tool_calls=m.get("tool_calls", []),
            )
        elif m["type"] == "tool":
            tool_call_id = m["tool_call_id"]
            tool_name = tool_call_lookup.get(tool_call_id)
            return ToolMessage(
                content=m["content"],
                tool_call_id=tool_call_id,
                name=tool_name,  # 👈 ensure name is set
                additional_kwargs=m.get("additional_kwargs", {}),
                response_metadata=m.get("response_metadata", {}),
                id=m.get("id"),
            )
        else:
            raise ValueError(f"Unknown message type: {m['type']}")

    return [convert_message(m) for m in raw_messages]
