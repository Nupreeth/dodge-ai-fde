Live Demo: https://dodge-ai-fde-frontend.vercel.app

## Preview

![Graph View](docs/screenshots/Screenshot%202026-03-23%20161036.png)
![Chat Interface](docs/screenshots/Screenshot%202026-03-23%20165522.png)

## Project Overview
This project is a context graph system built on top of a SAP Order to Cash (O2C) dataset. It ingests JSONL data across 19 entity types, loads them into SQLite, builds an in-memory NetworkX graph of business relationships, visualizes that graph in an interactive React UI, and lets users query the data in natural language through a chat interface powered by an LLM that generates SQL on the fly.

## Architecture
- Data ingestion: JSONL part files are read from the 19 entity folders and loaded into SQLite at startup.
- Graph construction: NetworkX builds a directed graph in memory from the SQLite tables using defined entity relationships (sales orders, deliveries, billing documents, journal entries, payments, customers, products, etc.).
- API layer (FastAPI): `GET /graph` returns the full graph (nodes + edges), `GET /expand/{node_id}` returns neighbors for a specific node, and `POST /chat` accepts a user question and returns a natural language answer.
- Frontend (React + Vite): `react-force-graph-2d` renders the graph and a chat panel calls `POST /chat` for natural language questions.
- LLM workflow: The model receives the full table schema and the user question, returns a raw SQL query, and the backend executes it against SQLite before returning a clear, plain language response.

## Why SQLite Over a Graph Database
SQLite was chosen because the dataset is small enough to fit comfortably in memory, query latency is negligible at this scale, and it avoids the operational overhead of running and maintaining a separate graph database like Neo4j. NetworkX handles the in-memory graph structure for visualization and neighbor lookups, while SQLite handles analytical queries. This keeps the architecture simple, fast, and easy to deploy.

## LLM Prompting Strategy
The system uses Groq with the `llama-3.3-70b-versatile` model. The system prompt includes the full schema (column names) for the 10 core tables. The user question is appended as input. The model is instructed to return only a raw SQLite SQL query with no markdown, no explanation, and no backticks. If the question is unrelated to the dataset, the model must return exactly `OFFTOPIC`, which the backend detects and replaces with a safe response.

## Guardrails
Off-topic questions are handled by explicitly instructing the LLM to return the string `OFFTOPIC` when a question is not related to the dataset. The backend checks for this string before executing any SQL and returns a fixed safe message instead. This prevents accidental misuse and reduces hallucinations.

## Dataset
The dataset is a SAP Order to Cash dataset with 19 entity types, including:
- sales order headers
- sales order items
- billing document headers
- billing document items
- outbound delivery headers
- outbound delivery items
- payments accounts receivable
- journal entry items (accounts receivable)
- business partners
- products
- and more

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI, NetworkX, SQLite, python-dotenv |
| LLM | Groq, llama-3.3-70b-versatile |
| Frontend | React, Vite, react-force-graph-2d |
| Deployment | Render (backend), Vercel (frontend) |

## Setup Instructions
1. Clone the repository.
2. Backend setup:
   - `cd backend`
   - `python -m venv venv`
   - Activate the venv:
     - Windows: `venv\Scripts\activate`
     - macOS/Linux: `source venv/bin/activate`
   - `pip install -r requirements.txt`
   - Create a `.env` file in `backend/` with:
     - `GROQ_API_KEY=your_key_here`
   - Start the API server:
     - `uvicorn main:app --reload`
3. Frontend setup (new terminal):
   - `cd frontend`
   - `npm install`
   - Create a `.env` file in `frontend/` with:
     - `VITE_API_URL=http://localhost:8000`
   - Start the frontend:
     - `npm run dev`
4. Open `http://localhost:5173` in your browser.

## Example Queries
- Which products are associated with the highest number of billing documents?
- Which customer has the highest total payment amount?
- How many sales orders are there in total?
- What is the total net amount across all sales orders?
- Which billing document has the highest total net amount?
- Identify sales orders that have been delivered but not billed
