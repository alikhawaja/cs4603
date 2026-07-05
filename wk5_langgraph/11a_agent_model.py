"""
LangGraph agent model definition for MLflow models-from-code logging.

This file defines the agent graph so MLflow can serialize it independently.
"""

import os
import mlflow
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI


# ─── Tools ───────────────────────────────────────────────────────────────────

def multiply(a: int, b: int) -> int:
    """Multiply a and b.

    Args:
        a: first int
        b: second int
    """
    return a * b


def add(a: int, b: int) -> int:
    """Adds a and b.

    Args:
        a: first int
        b: second int
    """
    return a + b


# ─── Build graph ─────────────────────────────────────────────────────────────

tools = [multiply, add]

llm = ChatOpenAI(
    model=os.environ.get("DATABRICKS_MODEL", "databricks-qwen35-122b-a10b"),
    api_key=os.environ.get("DATABRICKS_TOKEN", ""),
    base_url=os.environ.get("DATABRICKS_HOST", "").rstrip("/") + "/serving-endpoints",
    reasoning_effort="none",
    temperature=0,
)

llm_with_tools = llm.bind_tools(tools)


def assistant(state: MessagesState):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}


def route_tools(state: MessagesState):
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END


builder = StateGraph(MessagesState)
builder.add_node("assistant", assistant)
builder.add_node("tools", ToolNode(tools))
builder.add_edge(START, "assistant")
builder.add_conditional_edges("assistant", route_tools, ["tools", END])
builder.add_edge("tools", "assistant")

graph = builder.compile()

mlflow.models.set_model(graph)
