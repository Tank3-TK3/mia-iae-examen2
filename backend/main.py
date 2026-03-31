# main.py
# FastAPI entry point for the graph pathfinding backend.
# Run from the backend/ directory with:
#   uvicorn main:app --reload --port 8000

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from graph import GRAPH
from algorithms import hill_climbing, hill_climbing_backtracking, decision_tree, beam_search, q_learning

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="Graph Pathfinding API")

# Allow all origins so the frontend served on localhost:5500 (or any other
# origin during development) can reach the API without CORS errors.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class RunRequest(BaseModel):
    algorithm: str        # e.g. "hill_climbing"
    start: str            # source node ID
    end: str              # destination node ID
    beam_width: int = 3   # solo usado por beam_search

# ---------------------------------------------------------------------------
# Supported algorithms registry
# ---------------------------------------------------------------------------

ALGORITHMS = {
    "hill_climbing":              hill_climbing.run,
    "hill_climbing_backtracking": hill_climbing_backtracking.run,
    "decision_tree":              decision_tree.run,
    "beam_search":                beam_search.run,
    "q_learning":                 q_learning.run,
}

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health_check():
    """Simple liveness probe."""
    return {"status": "ok"}


@app.post("/api/run")
def run_algorithm(body: RunRequest):
    """
    Execute the requested pathfinding algorithm on the graph.

    Returns the algorithm result plus the original input parameters.

    Raises 400 if:
      - The algorithm name is unknown.
      - The start or end node does not exist in the graph.
    """

    # --- validate algorithm ------------------------------------------------
    if body.algorithm not in ALGORITHMS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unknown algorithm '{body.algorithm}'. "
                f"Supported: {list(ALGORITHMS.keys())}"
            ),
        )

    # --- validate nodes ----------------------------------------------------
    if body.start not in GRAPH:
        raise HTTPException(
            status_code=400,
            detail=f"Start node '{body.start}' does not exist in the graph.",
        )

    if body.end not in GRAPH:
        raise HTTPException(
            status_code=400,
            detail=f"End node '{body.end}' does not exist in the graph.",
        )

    # --- run the algorithm -------------------------------------------------
    algo_fn = ALGORITHMS[body.algorithm]
    kwargs = dict(start=body.start, end=body.end, graph=GRAPH)
    if body.algorithm == "beam_search":
        kwargs["beam_width"] = body.beam_width
    result = algo_fn(**kwargs)

    # Echo back the input parameters alongside the algorithm result so the
    # frontend always knows which request produced this response.
    return {
        "algorithm": body.algorithm,
        "start": body.start,
        "end": body.end,
        **result,
    }
