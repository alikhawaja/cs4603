# Week 1 — LLM Basics

Hands-on introduction to LLMs using Databricks model serving with an OpenAI-compatible API.

## Notebook Map

| Notebook | Topic |
|----------|-------|
| `0.endpoints.ipynb` | List Databricks serving endpoints to find your model endpoint. |
| `1.tokens.ipynb` | Chat completion calls and usage reporting (prompt/completion tokens). |
| `1.tokens.tiktoken.ipynb` | Tokenization with tiktoken, comparing encodings, and estimating costs. |
| `2.prompts.ipynb` | Zero-shot, few-shot, prompt chaining, and chain-of-thought prompting. |
| `3.openai-api-basics.ipynb` | System/persona prompts, multi-turn conversations, streaming, sampling parameters, and JSON output. |
| `4.openai-api-roles.ipynb` | `system`/`user`/`assistant` role experiments, including what wins in a system vs. user conflict. |
| `5.openai-api-func-1.ipynb` | Manual function calling: writing tool schemas and the tool-call loop. |
| `5.openai-api-func-2.ipynb` | Automatic tool schema generation from Python function signatures and type hints. |
| `6.openai-api-mlflow-1.ipynb` | MLflow basics: traces, spans, and terminology. |
| `6.openai-api-mlflow-2.ipynb` | Observability: tracing chat-completion calls with params, metrics, and artifacts. |

Run the notebooks in order. Each notebook starts with `%run shared_notebook_setup.py`, which loads your configuration and creates the API client.

## Prerequisites

- **Python packages**: `openai`, `python-dotenv`, `pprintpp`, `langchain-openai`, `tiktoken`, `mlflow`
- **`.env` file** in this folder (not committed) with:
  - `DATABRICKS_HOST` — your workspace URL
  - `DATABRICKS_TOKEN` — a personal access token with serving-endpoint access
  - `DATABRICKS_MODEL` — the serving endpoint name (see `0.endpoints.ipynb`)
- **MLflow tracking server** (for `6.openai-api-mlflow-1/2.ipynb` only). Start one locally, e.g.:

  ```powershell
  mlflow server --port 5000
  ```

  Override the URI if needed by setting the `MLFLOW_TRACKING_URI` environment variable.

## Study Material

- `study-guide.md` — 16 technical + 16 conceptual questions with brief answers, and the function-calling flow.
- `LLM - Function Call Flow.md` — how the LLM ↔ program function-calling loop works.
