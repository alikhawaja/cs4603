"""
11a. Databricks Deployment Setup Script

Run this script in a Databricks notebook or from a terminal with
the Databricks CLI configured. It creates all the prerequisites
needed for the deployment notebook (11.deployment.ipynb):

  1. MLflow experiment on Databricks
  2. Logs the LangGraph agent as an MLflow model
  3. Registers the model in Unity Catalog
  4. Creates a Model Serving endpoint

Prerequisites:
  - Databricks CLI configured (`databricks auth login`) OR
  - Running inside a Databricks notebook with workspace auth
  - .env file with DATABRICKS_TOKEN, DATABRICKS_HOST, DATABRICKS_MODEL

Usage (from repo root):
    python wk5_langgraph/11a.deploy_setup.py

    # Or with custom model name:
    python wk5_langgraph/11a.deploy_setup.py --model-name my_agent

    # Skip endpoint creation (just register model):
    python wk5_langgraph/11a.deploy_setup.py --skip-endpoint
"""

import argparse
import sys
import time

sys.path.insert(0, "..")

# ─── Parse arguments ─────────────────────────────────────────────────────────

parser = argparse.ArgumentParser(description="Set up Databricks prerequisites for LangGraph deployment")
parser.add_argument("--model-name", default="main.default.cs4603_langgraph_agent", help="Unity Catalog model path (default: main.default.cs4603_langgraph_agent)")
parser.add_argument("--endpoint-name", default="cs4603-langgraph-agent", help="Serving endpoint name (default: cs4603-langgraph-agent)")
parser.add_argument("--skip-endpoint", action="store_true", help="Skip creating the serving endpoint")
args = parser.parse_args()

MODEL_REGISTRY_NAME = args.model_name

# ─── Bootstrap ───────────────────────────────────────────────────────────────

print("=" * 60)
print("  LangGraph Agent — Databricks Deployment Setup")
print("=" * 60)

from langchain_common import bootstrap_notebook

DATABRICKS_TOKEN, DATABRICKS_HOST, DATABRICKS_MODEL, (llm, llm_noreason), embeddings = bootstrap_notebook()
print(f"\n  Databricks host: {DATABRICKS_HOST}")
print(f"  Model endpoint:  {DATABRICKS_MODEL}")

# Check for Databricks SDK availability (used for serving endpoint creation)
try:
    from databricks.sdk import WorkspaceClient
    w = WorkspaceClient(host=DATABRICKS_HOST, token=DATABRICKS_TOKEN)
    HAS_SDK = True
except ImportError:
    HAS_SDK = False

# ─── Step 1: Define the LangGraph agent ──────────────────────────────────────

print(f"\n{'─'*60}")
print(f"  Step 1: Define the LangGraph agent")
print(f"{'─'*60}")

from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage


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


tools = [multiply, add]
llm_with_tools = llm_noreason.bind_tools(tools)


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

# Sanity check
result = graph.invoke({"messages": [HumanMessage(content="Multiply 3 by 2.")]})
answer = result["messages"][-1].content
print(f"  ✓ Agent compiled and tested (3×2 = {answer})")

# ─── Step 2: Log to MLflow ───────────────────────────────────────────────────

print(f"\n{'─'*60}")
print(f"  Step 2: Log agent to MLflow")
print(f"{'─'*60}")

import mlflow
import os

# Point MLflow at the Databricks workspace from .env (not local sqlite)
os.environ["DATABRICKS_HOST"] = DATABRICKS_HOST
os.environ["DATABRICKS_TOKEN"] = DATABRICKS_TOKEN
mlflow.set_tracking_uri("databricks")

print(f"  MLflow tracking: {mlflow.get_tracking_uri()}")
print(f"  Target host:     {DATABRICKS_HOST}")

# Resolve the current user's home folder for the experiment
import requests
try:
    resp = requests.get(
        f"{DATABRICKS_HOST.rstrip('/')}/api/2.0/preview/scim/v2/Me",
        headers={"Authorization": f"Bearer {DATABRICKS_TOKEN}"},
    )
    db_username = resp.json().get("userName", "unknown")
except Exception:
    db_username = "unknown"

experiment_path = f"/Users/{db_username}/wk5-deployment"
print(f"  Experiment:      {experiment_path}")

mlflow.set_experiment(experiment_path)

# Write model code path for models-from-code logging
model_code_path = os.path.join(os.path.dirname(__file__), "11a_agent_model.py")
print(f"  Model code:      {model_code_path}")

with mlflow.start_run(run_name="langgraph-agent-setup") as run:
    model_info = mlflow.langchain.log_model(
        lc_model=model_code_path,
        artifact_path="langgraph_agent",
        input_example={"messages": [{"role": "user", "content": "Add 2 and 3."}]},
    )
    run_id = run.info.run_id

print(f"  ✓ Model logged: {model_info.model_uri}")
print(f"  ✓ Run ID: {run_id}")

# ─── Step 3: Register in Unity Catalog ────────────────────────────────────

print(f"\n{'─'*60}")
print(f"  Step 3: Register model in Unity Catalog")
print(f"  Name: {MODEL_REGISTRY_NAME}")
print(f"{'─'*60}")

try:
    mlflow.set_registry_uri("databricks-uc")

    registered = mlflow.register_model(
        model_uri=model_info.model_uri,
        name=MODEL_REGISTRY_NAME,
    )
    model_version = registered.version
    print(f"  ✓ Registered version {model_version}")

except Exception as e:
    print(f"  ✗ Registration failed: {e}")
    sys.exit(1)

# ─── Step 5: Create serving endpoint ─────────────────────────────────────────

if args.skip_endpoint:
    print(f"\n{'─'*60}")
    print(f"  Step 4: Skipped (--skip-endpoint)")
    print(f"{'─'*60}")
else:
    print(f"\n{'─'*60}")
    print(f"  Step 4: Create Model Serving endpoint")
    print(f"  Endpoint: {args.endpoint_name}")
    print(f"{'─'*60}")

    if not HAS_SDK:
        print("  ⚠ databricks-sdk not available — cannot create endpoint automatically.")
        print(f"    Create it manually in the Databricks UI:")
        print(f"    - Go to Serving → New → select '{MODEL_REGISTRY_NAME}' version {model_version}")
        print(f"    - Name it '{args.endpoint_name}'")
        print(f"    - Enable 'Scale to zero'")
    else:
        try:
            from databricks.sdk.service.serving import (
                EndpointCoreConfigInput,
                ServedEntityInput,
            )

            # Check if endpoint already exists
            existing = None
            try:
                existing = w.serving_endpoints.get(args.endpoint_name)
            except Exception:
                pass

            if existing:
                print(f"  Endpoint '{args.endpoint_name}' already exists (state: {existing.state.ready})")
                print(f"  Updating to model version {model_version}...")
                w.serving_endpoints.update_config(
                    name=args.endpoint_name,
                    served_entities=[
                        ServedEntityInput(
                            entity_name=MODEL_REGISTRY_NAME,
                            entity_version=str(model_version),
                            workload_size="Small",
                            scale_to_zero_enabled=True,
                        )
                    ],
                )
                print(f"  ✓ Endpoint updated")
            else:
                print(f"  Creating endpoint '{args.endpoint_name}'...")
                w.serving_endpoints.create(
                    name=args.endpoint_name,
                    config=EndpointCoreConfigInput(
                        served_entities=[
                            ServedEntityInput(
                                entity_name=MODEL_REGISTRY_NAME,
                                entity_version=str(model_version),
                                workload_size="Small",
                                scale_to_zero_enabled=True,
                            )
                        ]
                    ),
                )
                print(f"  ✓ Endpoint '{args.endpoint_name}' created")
                print(f"    It may take a few minutes to become READY.")

            print(f"\n  Endpoint URL: {DATABRICKS_HOST}/serving-endpoints/{args.endpoint_name}/invocations")

        except Exception as e:
            print(f"  ⚠ Could not create endpoint: {e}")
            print(f"    Create it manually in the Databricks UI.")

# ─── Summary ─────────────────────────────────────────────────────────────────

print(f"\n{'='*60}")
print(f"  Setup Complete!")
print(f"{'='*60}")
print(f"""
  Model:     {MODEL_REGISTRY_NAME} (version {model_version})
  Endpoint:  {args.endpoint_name}
  Run ID:    {run_id}

  To test the endpoint (once READY):

    import openai
    client = openai.OpenAI(
        api_key="<your-token>",
        base_url="{DATABRICKS_HOST}/serving-endpoints",
    )
    resp = client.chat.completions.create(
        model="{args.endpoint_name}",
        messages=[{{"role": "user", "content": "Multiply 3 by 2."}}],
    )
    print(resp.choices[0].message.content)
""")
