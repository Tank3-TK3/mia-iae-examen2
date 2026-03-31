# algorithms/hill_climbing_backtracking.py
#
# Hill Climbing con Backtracking.
#
# Extiende el Hill Climbing greedy básico con un mecanismo de recuperación:
# cuando el algoritmo llega a un callejón sin salida (ningún vecino válido),
# retrocede al nodo anterior y prueba el siguiente candidato en su lista.
# Al retroceder, el costo de la arista recorrida se deshace, de modo que el
# costo total siempre refleja únicamente la ruta activa en ese momento.
#
# Garantías:
#   - Encuentra una ruta si existe (es completo).
#   - NO garantiza la ruta de menor peso (encuentra la primera ruta viable
#     siguiendo preferencia greedy por menor peso de arista).
#
# Diferencia clave respecto a HC básico:
#   - HC básico:             se atasca → termina sin solución.
#   - HC con Backtracking:   se atasca → retrocede y sigue intentando.

import time


def run(start: str, end: str, graph: dict) -> dict:
    """
    Ejecuta Hill Climbing con Backtracking de `start` a `end` sobre `graph`.

    Retorna
    -------
    dict con:
        found          – True si se alcanzó el destino.
        path           – Ruta final (nodos en orden).
        cost           – Costo acumulado de la ruta encontrada.
        steps          – Decisiones tomadas (avances y retrocesos).
        visited_count  – Nodos distintos visitados (incluyendo retrocesos).
        time_ms        – Tiempo de ejecución en milisegundos.
        stuck_reason   – None si found, "no_path_exists" si se agotaron
                         todos los caminos posibles.
    """
    t_start = time.perf_counter()

    # ── Caso trivial ─────────────────────────────────────────────────────────
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

    # ── Estado de la búsqueda ─────────────────────────────────────────────────
    # Cada frame del stack: (nodo_actual, candidatos_restantes, costo_arista_entrada)
    # candidatos_restantes: lista ordenada por peso de los vecinos aún no intentados.
    # costo_arista_entrada: costo de la arista que nos trajo a este nodo
    #                       (necesario para deshacer el costo al retroceder).

    path: list[str] = [start]
    in_path: set[str] = {start}          # nodos en la ruta activa → evita ciclos
    cost: int = 0
    steps: list[dict] = []
    all_visited: set[str] = {start}      # para visited_count en estadísticas

    def sorted_candidates(node: str) -> list[tuple[str, int]]:
        """Vecinos ordenados por peso ascendente (heurística greedy HC)."""
        return sorted(graph[node], key=lambda x: x[1])

    # Stack inicial: arrancamos en `start` con todos sus vecinos como candidatos
    stack: list[tuple[str, list[tuple[str, int]], int]] = [
        (start, sorted_candidates(start), 0)
    ]

    # ── Bucle principal ───────────────────────────────────────────────────────
    while stack:
        current, candidates, arrival_cost = stack[-1]

        # ¿Llegamos al destino?
        if current == end:
            break

        # Buscar el próximo candidato válido (no está en la ruta activa)
        chosen: str | None = None
        chosen_weight: int = 0

        while candidates:
            n, w = candidates.pop(0)
            if n not in in_path:
                chosen = n
                chosen_weight = w
                break
            # Si está en in_path lo descartamos: no tiene sentido intentarlo
            # ahora; si hacemos backtrack y ya no está en in_path, este frame
            # ya habrá sido eliminado del stack de todas formas.

        if chosen is None:
            # ── Backtrack ────────────────────────────────────────────────────
            # No quedan candidatos válidos en este nodo → retrocedemos.
            stack.pop()
            removed = path.pop()
            in_path.discard(removed)
            cost -= arrival_cost          # deshacemos el costo de llegada

            steps.append({
                "action": "backtrack",
                "from": removed,
                "to": path[-1] if path else start,
                "cost_undone": arrival_cost,
            })
        else:
            # ── Avanzar ──────────────────────────────────────────────────────
            # Registramos el paso con todos los candidatos que quedaban + el elegido
            all_candidates_snapshot = sorted(
                [(chosen, chosen_weight)] + list(candidates),
                key=lambda x: x[1],
            )
            steps.append({
                "action": "move",
                "from": current,
                "to": chosen,
                "weight": chosen_weight,
                "candidates": [[n, w] for n, w in all_candidates_snapshot],
            })

            cost += chosen_weight
            path.append(chosen)
            in_path.add(chosen)
            all_visited.add(chosen)
            stack.append((chosen, sorted_candidates(chosen), chosen_weight))

    # ── Resultado ─────────────────────────────────────────────────────────────
    found = bool(path) and path[-1] == end
    elapsed_ms = round((time.perf_counter() - t_start) * 1000, 3)

    return {
        "found": found,
        "path": path,
        "cost": cost,
        "steps": steps,
        "visited_count": len(all_visited),
        "time_ms": elapsed_ms,
        "stuck_reason": None if found else "no_path_exists",
    }
