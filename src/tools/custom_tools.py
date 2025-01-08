from typing import Annotated
from langchain_core.tools import tool
from langgraph.types import Command
from langgraph.prebuilt.tool_node import InjectedState, InjectedToolArg

class InjectedToolCallId(InjectedToolArg):
    """Annotation for a Tool arg that is meant to be populated with the tool call ID.

    Any Tool argument annotated with InjectedToolCallId will be hidden from a tool-calling
    model, so that the model doesn't attempt to generate the argument. If using
    ToolNode, the tool call ID will be automatically injected into the tool args.
    """
    def __init__(self) -> None:
        super().__init__()

@tool
def make_handoff_tool(agent_name: str):
    """Crea un tool che effettua l'handoff a un altro agente."""
    tool_name = f"transfer_to_{agent_name}"

    @tool(tool_name)
    def handoff_to_agent(
        state: Annotated[dict, InjectedState] = None,
        tool_call_id: Annotated[str, InjectedToolCallId] = None,
    ):
        """Effettua l'handoff a un altro agente."""
        if not state:
            raise ValueError("Il campo 'state' è obbligatorio per l'handoff.")
        if not tool_call_id:
            raise ValueError("Il campo 'tool_call_id' è obbligatorio per l'handoff.")

        tool_message = {
            "role": "tool",
            "content": f"Successfully transferred to {agent_name}",
            "name": tool_name,
            "tool_call_id": tool_call_id,
        }
        return Command(
            goto=agent_name,
            graph=Command.PARENT,
            update={"messages": state["messages"] + [tool_message]},
        )

    return handoff_to_agent
