# algorithms/hill_climbing.py
# Hill Climbing pathfinding on a weighted graph.
#
# Heuristic: at each step, greedily move to the unvisited neighbor with the
# MINIMUM edge weight.  This is a local, greedy strategy — it does not
# guarantee an optimal (or even complete) solution.

import time


def run(start: str, end: str, graph: dict) -> dict:
    """
    Run Hill Climbing from `start` to `end` on `graph`.

    Parameters
    ----------
    start : str
        ID of the starting node.
    end : str
        ID of the goal node.
    graph : dict
        Adjacency list mapping node_id -> list of (neighbor_id, weight).

    Returns
    -------
    dict with keys:
        found          – True if the goal was reached.
        path           – Ordered list of node IDs visited.
        cost           – Accumulated edge cost along the path.
        steps          – List of decision records (one per move).
        visited_count  – Number of distinct nodes visited.
        time_ms        – Wall-clock time taken in milliseconds.
        stuck_reason   – None, or "no_unvisited_neighbors" if the search
                         terminated early because no move was available.
    """
    t_start = time.perf_counter()

    # --- trivial case ---------------------------------------------------
    if start == end:
        return {
            "found": True,
            "path": [start],
            "cost": 0,
            "steps": [],
            "visited_count": 1,
            "time_ms": round((time.perf_counter() - t_start) * 1000, 3),
            "stuck_reason": None,
        }

    # --- initialise search state ----------------------------------------
    visited: set[str] = {start}
    path: list[str] = [start]
    cost: int = 0
    steps: list[dict] = []
    current: str = start
    stuck_reason: str | None = None

    # --- main loop -------------------------------------------------------
    while current != end:
        neighbors = graph[current]

        # Build the list of unvisited neighbors, sorted by edge weight (asc).
        candidates: list[tuple[str, int]] = sorted(
            [(nbr, w) for nbr, w in neighbors if nbr not in visited],
            key=lambda x: x[1],
        )

        if not candidates:
            # Dead end — no unvisited neighbours to move to.
            stuck_reason = "no_unvisited_neighbors"
            break

        # Greedy choice: pick the neighbour with the smallest edge weight.
        best_node, best_weight = candidates[0]

        # Record this decision step.
        steps.append({
            "from": current,
            "to": best_node,
            "weight": best_weight,
            # Expose all candidates as plain lists so they serialise to JSON
            # arrays (e.g. ["2", 28]) rather than tuples.
            "candidates": [[n, w] for n, w in candidates],
        })

        # Move to the chosen neighbour.
        cost += best_weight
        current = best_node
        visited.add(current)
        path.append(current)

    # --- build result ----------------------------------------------------
    elapsed_ms = round((time.perf_counter() - t_start) * 1000, 3)

    return {
        "found": current == end,
        "path": path,
        "cost": cost,
        "steps": steps,
        "visited_count": len(visited),
        "time_ms": elapsed_ms,
        "stuck_reason": stuck_reason,
    }
