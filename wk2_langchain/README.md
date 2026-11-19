# Week 2 — LangChain

Building LLM applications with LangChain: model calls, prompt templates, Runnables/LCEL, embeddings, vector stores, RAG, and record-manager indexing.

## Notebook Map

| Notebook | Topic |
|----------|-------|
| `1.langchain.basics.ipynb` | `ChatOpenAI` against Databricks, disabling reasoning output, and a first LCEL chain (`prompt \| llm \| parser`). |
| `2.langchain.prompt.templates.ipynb` | `PromptTemplate`, multiple variables, `ChatPromptTemplate` roles, `.partial()`, and `.batch()`. |
| `3.langchain.runnable.ipynb` | `RunnablePassthrough`, custom `Runnable`, `RunnablePassthrough.assign`, and `RunnableSequence`. |
| `4.langchain.embeddings.ipynb` | Embeddings, `PGVector.from_texts` / `from_documents`, similarity search with scores, retrievers, and `add_documents`. |
| `5.langchain.rag.ipynb` | End-to-end RAG: web loading, token-based splitting, FAISS, a RAG chain, and an LCEL retrieval pipeline. |
| `6.langchain.recordmgr.ipynb` | `SQLRecordManager` and `index()` with `None`, `incremental`, and `full` cleanup. |

Supporting files: `langchain_common_notebook.py` (shared setup via `%run`), `llm_notes.txt` (sample corpus for notebook 4).

## Prerequisites

- Week 1 setup (`.env` with `DATABRICKS_HOST`, `DATABRICKS_TOKEN`, `DATABRICKS_MODEL`).
- `PGVECTOR_DSN` optionally overrides the local PGVector connection string used by notebooks 4 and 6.
- Packages: `langchain-openai`, `langchain-community`, `langchain-postgres`, `langchain-classic`, `langchain-text-splitters`, `faiss-cpu`, `psycopg`, `pandas`, `pprintpp`.
- A PGVector database (notebooks 4 and 6); see `../pgvector-mlflow-setup`.
- Notebook 5 uses a browser-like default `User-Agent`; set `USER_AGENT` to override it.

## Study Material

- `study-guide.md` — technical and conceptual questions with brief answers, and the RAG flow diagram.
