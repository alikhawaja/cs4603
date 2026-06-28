# pgvector + MLflow on Postgres — Student Setup Guide

This folder spins up a **single Podman pod** that runs two containers:

1. **pgvector** — PostgreSQL 18 with the `pgvector` extension. On first start it
   auto-creates all the databases this course needs.
2. **mlflow** — an MLflow tracking server that uses the same Postgres instance as
   its backend store. It waits for the database to be ready, then starts.

Because both containers live in the **same pod**, they share a network. MLflow
reaches Postgres at `localhost:5432`.

```mermaid
flowchart LR
    user["Your notebook / browser<br/>(host machine)"]

    subgraph pod["pgvector-pod (shared network)"]
        direction LR
        mlflow["mlflow<br/>tracking server<br/>:5000"]
        pg["pgvector<br/>PostgreSQL 18 + pgvector<br/>:5432"]
        mlflow -- "localhost:5432" --> pg
    end

    user -- "http :5000" --> mlflow
    user -- "psql :5432" --> pg
```

---

## Files in this folder

| File | Purpose |
|------|---------|
| `Dockerfile.mlflow` | Builds the MLflow image with the Postgres driver (`psycopg2-binary`). |
| `Dockerfile.pgvector` | Builds the pgvector image with the init SQL baked in. |
| `pgvector-mlflow.yaml` | The Podman pod spec that runs both containers. |
| `initdb/pgvector-mlflow-setup.sql` | Runs once on first DB init to create users/databases and enable pgvector. |

---

## Databases that get created

| Database | Owner / Password | pgvector enabled | Created by |
|----------|------------------|------------------|------------|
| `langchain_db` | `langchain` / `langchain!` | yes | `POSTGRES_*` env (db) + `initdb` script (extension) |
| `mlflow_db` | `mlflow` / `mlflow!` | yes | `initdb/pgvector-mlflow-setup.sql` |
| `analytics` | `analytics` / `analytics!` | yes | `initdb/pgvector-mlflow-setup.sql` |

> All three databases come up with the `vector` extension already enabled, so you
> can store embeddings immediately — no manual setup needed.

---

## Prerequisites

1. **Podman** installed and the Podman machine started:
   ```powershell
   podman machine start
   ```
2. A terminal opened **inside this folder** — every command below assumes it:
   ```powershell
   cd pgvector-mlflow-setup
   ```
   The build commands use this folder as their context.

---

## Step 1: Build the two images

The pod spec references two locally-built images, so build them first.

**pgvector** (Postgres + pgvector with the init SQL baked in):

```powershell
podman build -f Dockerfile.pgvector -t postgres-vector .
```

**mlflow** (official MLflow image + the `psycopg2-binary` Postgres driver):

```powershell
podman build -f Dockerfile.mlflow -t mlflow-postgres .
```

> The init SQL is **baked into the pgvector image** (copied into
> `/docker-entrypoint-initdb.d`) rather than mounted from disk, because
> `podman play kube` does not reliably mount relative host paths.

---

## Step 2: Run the pod

```powershell
podman play kube pgvector-mlflow.yaml
```

What happens, in order:

1. **pgvector** starts and initializes a fresh data directory in the `pgvector-pgdata`
   named volume.
2. Because the data dir is empty (first run), Postgres executes every script in
   `/docker-entrypoint-initdb.d` — the baked-in `pgvector-mlflow-setup.sql`,
   which enables `vector` on `langchain_db` and creates `mlflow_db`, the `mlflow`
   user, and the `analytics` database.
3. **mlflow** starts, loops until `mlflow_db` accepts connections, then launches
   the tracking server on port 5000 using
   `postgresql://mlflow:mlflow%21@localhost:5432/mlflow_db`
   (the `%21` is the URL-encoded `!` in the password).

---

## Step 3: Confirm both containers are up

```powershell
podman pod ps
podman ps --pod
```

You should see `pgvector-pod` running with the `pgvector` and `mlflow` containers.
To watch MLflow wait for and connect to Postgres:

```powershell
podman logs -f pgvector-pod-mlflow
```

---

## Step 4: Verify

**MLflow UI** — open in your browser:

```
http://localhost:5000
```

**Databases** — list them and confirm pgvector is enabled on `langchain_db`:

```powershell
podman exec -it pgvector-pod-pgvector psql -U langchain -d langchain_db
```

```sql
\l      -- langchain_db, mlflow_db, analytics listed
\dx     -- confirm the "vector" extension is installed
\q
```

---

## Connecting from your notebooks

**LangChain / pgvector** (vector store):

```python
CONNECTION_STRING = "postgresql+psycopg://langchain:langchain!@localhost:5432/langchain_db"
```

**MLflow** (tracking) — in your `.env` at the repo root:

```env
MLFLOW_TRACKING_URI=http://localhost:5000
```

or in code:

```python
import mlflow
mlflow.set_tracking_uri("http://localhost:5000")
```

---

## Stopping, restarting, and re-initializing

```powershell
# Tear the pod down (named volumes are kept)
podman play kube --down pgvector-mlflow.yaml

# Bring it back up (reuses existing data — initdb does NOT re-run)
podman play kube pgvector-mlflow.yaml
```

> **Important:** the `initdb` script only runs when the Postgres data directory is
> **empty**. The `pgvector-pgdata` named volume persists across restarts, so
> bringing the pod back up reuses the existing databases. If you change
> `pgvector-mlflow-setup.sql`, rebuild the pgvector image and remove the volume so
> the script runs again:
>
> ```powershell
> podman play kube --down pgvector-mlflow.yaml
> podman build -f Dockerfile.pgvector -t postgres-vector .
> podman volume rm pgvector-pgdata
> podman play kube pgvector-mlflow.yaml
> ```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `image not known: localhost/postgres-vector` or `localhost/mlflow-postgres` | Run Step 1 (build both images) before Step 2. |
| MLflow logs loop on "pgvector not ready" forever | `mlflow_db` wasn't created — the `initdb` script didn't run. Remove the `pgvector-pgdata` volume and re-up (see above). |
| You changed the init SQL but nothing changed | Rebuild the pgvector image **and** remove the `pgvector-pgdata` volume (see above). |
| Port 5000 already in use | Stop any local `mlflow ui` process, or change the mlflow container `hostPort` in the YAML. |
| Port 5432 already in use | Stop any local Postgres, or change the pgvector container `hostPort` in the YAML. |
| `vector` extension missing in a database | The `initdb` script didn't run (data dir wasn't empty). Remove the `pgvector-pgdata` volume and re-up (see above). |
