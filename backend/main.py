"""FastAPI entrypoint for the SAP Order to Cash graph and chat services."""

from __future__ import annotations

from contextlib import asynccontextmanager
import os
from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from database import load_all_data
from graph import build_graph, get_graph, get_neighbors
from llm import ask


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[startup] Loading dataset into SQLite...")
    load_all_data()
    print("[startup] Dataset load complete.")

    print("[startup] Building graph...")
    build_graph()
    print("[startup] Graph build complete.")

    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.api_route("/health", methods=["GET", "HEAD"])
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/graph")
async def graph_endpoint():
    return get_graph()


@app.get("/expand/{node_id}")
async def expand_node(node_id: str):
    return get_neighbors(node_id)


@app.post("/chat")
async def chat(payload: Dict[str, str]):
    message = payload.get("message", "") if payload else ""
    result = ask(message)
    if result == "OFFTOPIC":
        return {
            "answer": "This system is designed to answer questions related to the provided dataset only."
        }
    return {"answer": result}


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
