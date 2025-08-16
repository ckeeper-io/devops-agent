from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, AIMessage

def raw_to_messages(raw_messages):
    def convert_message(m):
        if m["type"] == "system":
            return SystemMessage(
                content=m["content"],
                additional_kwargs=m.get("additional_kwargs", {}),
                response_metadata=m.get("response_metadata", {}),
                name=m.get("name"),
                id=m.get("id")
            )
        elif m["type"] == "human":
            return HumanMessage(
                content=m["content"],
                additional_kwargs=m.get("additional_kwargs", {}),
                response_metadata=m.get("response_metadata", {}),
                name=m.get("name"),
                id=m.get("id")
            )
        elif m["type"] == "ai":
            return AIMessage(
                content=m["content"],
                additional_kwargs=m.get("additional_kwargs", {}),
                response_metadata=m.get("response_metadata", {}),
                name=m.get("name"),
                id=m.get("id")
            )
        elif m["type"] == "tool":
            return ToolMessage(
                content=m["content"],
                tool_call_id=m["tool_call_id"],  # REQUIRED
                additional_kwargs=m.get("additional_kwargs", {}),
                response_metadata=m.get("response_metadata", {}),
                name=m.get("name"),
                id=m.get("id")
            )
        else:
            raise ValueError(f"Unknown message type: {m['type']}")

    langchain_messages = [convert_message(m) for m in raw_messages]
    return langchain_messages