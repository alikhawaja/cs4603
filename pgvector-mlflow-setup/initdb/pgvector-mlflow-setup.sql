-- mlflow-postgres: initdb script for pgvector + mlflow setup
-- Runs once, on first DB init, connected to the default database (langchain_db).

-- Enable pgvector on the primary langchain_db (created from POSTGRES_* env).
CREATE EXTENSION IF NOT EXISTS vector;

-- mlflow user + database (backend store for the MLflow tracking server).
CREATE USER mlflow WITH PASSWORD 'mlflow!';
CREATE DATABASE mlflow_db OWNER mlflow;
GRANT ALL PRIVILEGES ON DATABASE mlflow_db TO mlflow;
\connect mlflow_db
CREATE EXTENSION IF NOT EXISTS vector;

-- Example: third user + database
CREATE USER analytics WITH PASSWORD 'analytics!';
CREATE DATABASE analytics OWNER analytics;
GRANT ALL PRIVILEGES ON DATABASE analytics TO analytics;
\connect analytics
CREATE EXTENSION IF NOT EXISTS vector;
