# algorithms/beam_search.py
#
# Beam Search — Búsqueda con haz
#
# ── Qué es Beam Search ────────────────────────────────────────────────────────
# Beam Search es una búsqueda informada que mantiene un conjunto de β rutas
# parciales (el "haz") en cada iteración. En cada paso expande todas las rutas
# del haz, genera sus sucesores y conserva solo las β mejores según la función
# de evaluación (aquí: costo acumulado — menor es mejor).
#
# ── Por qué costo acumulado como heurística ───────────────────────────────────
# El grafo no tiene coordenadas espaciales, por lo que no disponemos de una
# heurística admisible como la distancia euclidiana (usada en A*). Ordenar por
# costo acumulado convierte Beam Search en una variante de BFS ponderado que
# favorece rutas más baratas sin necesidad de información adicional.
#
# ── Completitud y optimalidad ─────────────────────────────────────────────────
# Beam Search NO es completo: con un β pequeño puede descartar la única ruta
# al destino. Tampoco es óptimo: puede retener rutas baratas al inicio que no
# llevan al destino y descartar la ruta óptima.
#
# ── Efecto del parámetro β ───────────────────────────────────────────────────
# β=1  →  equivale a Hill Climbing greedy (una sola ruta, sin backtracking)
# β=3  →  balancea exploración y eficiencia (valor base del Examen 1)
# β=5+ →  mayor exploración, puede encontrar rutas que β pequeño descarta
# β=n  →  cuando n ≥ branching factor máximo, equivale a BFS ponderado
#
# ── Sin repetición de nodos ───────────────────────────────────────────────────
# Cada estado del haz rastrea sus propios nodos visitados para evitar ciclos
# dentro de una misma ruta (comportamiento definido en el Examen 1).

import time


def run(start: str, end: str, graph: dict, beam_width: int = 3) -> dict:
    """
    Ejecuta Beam Search con el ancho de haz indicado.

    Cada estado del haz es (costo_acumulado, ruta, nodos_visitados).
    En cada iteración se expanden todos los estados, se generan sus sucesores
    y se conservan los β de menor costo acumulado.

    No realiza auto-incremento de β — si no encuentra solución retorna
    found=False para que el usuario pueda ajustar β desde la interfaz.

    Retorna el mismo formato que los demás algoritmos del proyecto.
    """
    t_start = time.perf_counter()

    # ── Caso trivial ──────────────────────────────────────────────────────────
    if start == end:
        return {
            "found":         True,
            "path":          [start],
            "cost":          0,
            "steps":         [],
            "visited_count": 1,
            "time_ms":       0.0,
            "stuck_reason":  None,
            "beam_width":    beam_width,
        }

    # ── Estado inicial ────────────────────────────────────────────────────────
    # Cada elemento: (costo, ruta, frozenset de visitados)
    beam: list[tuple[int, list[str], frozenset]] = [
        (0, [start], frozenset({start}))
    ]

    steps: list[dict] = []
    iteration = 0

    while beam:
        iteration += 1

        # ── Comprobar si alguna ruta llegó al destino ─────────────────────────
        for cost, path, _ in beam:
            if path[-1] == end:
                elapsed_ms = round((time.perf_counter() - t_start) * 1000, 3)
                all_visited: set[str] = set()
                for _, p, _ in beam:
                    all_visited.update(p)
                return {
                    "found":         True,
                    "path":          path,
                    "cost":          cost,
                    "steps":         steps,
                    "visited_count": len(all_visited),
                    "time_ms":       elapsed_ms,
                    "stuck_reason":  None,
                    "beam_width":    beam_width,
                }

        # ── Expandir todos los estados del haz ───────────────────────────────
        candidates: list[tuple[int, list[str], frozenset]] = []

        for cost, path, visited in beam:
            current = path[-1]
            for neighbor, weight in graph[current]:
                if neighbor not in visited:
                    candidates.append((
                        cost + weight,
                        path + [neighbor],
                        visited | {neighbor},
                    ))

        if not candidates:
            break

        # ── Ordenar por costo acumulado y retener los β mejores ──────────────
        candidates.sort(key=lambda x: x[0])
        kept   = candidates[:beam_width]
        pruned = candidates[beam_width:]

        steps.append({
            "action":      "expand",
            "iteration":   iteration,
            "beam_before": [p[-1] for _, p, _ in beam],
            "beam_after":  [p[-1] for _, p, _ in kept],
            "pruned":      [p[-1] for _, p, _ in pruned],
            "costs_kept":  [c for c, _, _ in kept],
        })

        beam = kept

    # ── No se encontró solución ───────────────────────────────────────────────
    elapsed_ms = round((time.perf_counter() - t_start) * 1000, 3)
    all_visited_f: set[str] = set()
    for _, p, _ in beam:
        all_visited_f.update(p)

    best_path = beam[0][1] if beam else [start]
    best_cost = beam[0][0] if beam else 0

    return {
        "found":         False,
        "path":          best_path,
        "cost":          best_cost,
        "steps":         steps,
        "visited_count": len(all_visited_f),
        "time_ms":       elapsed_ms,
        "stuck_reason":  "beam_exhausted",
        "beam_width":    beam_width,
    }
