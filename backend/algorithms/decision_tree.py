# algorithms/decision_tree.py
#
# Aprendizaje Supervisado — DecisionTreeClassifier
#
# ── Por qué Classifier y no Regressor ────────────────────────────────────────
# En el Examen 1 se propuso un DecisionTreeRegressor, pero un regressor predice
# valores numéricos continuos (ej. "nodo 3.7"), lo cual no tiene sentido cuando
# la tarea es elegir el siguiente nodo entre un conjunto discreto de opciones.
# DecisionTreeClassifier es el modelo correcto: predice una clase (el siguiente
# nodo) entre las 32 posibles etiquetas del grafo.
#
# ── Dataset y Data Leaking ────────────────────────────────────────────────────
# El dataset se genera automáticamente a partir del propio grafo usando Dijkstra
# para calcular las rutas óptimas entre todos los pares de nodos. Cada paso de
# cada ruta produce una muestra etiquetada:
#
#   Features : [nodo_actual_codificado, nodo_destino_codificado]
#   Label    : nodo_siguiente_óptimo_codificado
#
# Esto implica que el modelo conoce el dominio (las rutas de este grafo), lo que
# técnicamente constituye data leaking. Sin embargo, es académicamente válido
# porque:
#   1. El dataset representa conocimiento del dominio, no del conjunto de prueba.
#   2. En inferencia el árbol NO ejecuta Dijkstra — aplica reglas if/then
#      aprendidas. Si el grafo cambiara, el modelo fallaría.
#   3. Este enfoque es análogo al aprendizaje supervisado en navegación real:
#      se entrena con rutas históricas conocidas.
#
# ── Cómo decide el árbol ─────────────────────────────────────────────────────
# El árbol aprende reglas del tipo:
#   "Si estoy en el nodo 6 y mi destino es 14 → ir a 14"
#   "Si estoy en el nodo 1 y mi destino es 10 → ir a 2"
# En inferencia recorre esas reglas hasta encontrar la hoja correspondiente.
#
# ── Limitaciones ─────────────────────────────────────────────────────────────
# - Si la predicción no es un vecino válido o ya fue visitado, se usa fallback
#   (vecino no visitado de menor peso) para evitar quedar atascado.
# - Puede quedar atascado si todos los vecinos ya fueron visitados.
# - No garantiza la ruta de menor peso en todos los casos.

import heapq
import time

import numpy as np
from sklearn.tree import DecisionTreeClassifier

# ── Codificación de nodos ─────────────────────────────────────────────────────
NODE_IDS = [
    '1','2','3','4','5','6','7','8','9','10',
    '11','12','13','14','15a','15b',
    '16','17','18','19','20','21','22','23',
    '24','25','26','27','28','29','30','31',
]
NODE_TO_IDX = {n: i for i, n in enumerate(NODE_IDS)}
IDX_TO_NODE = {i: n for i, n in enumerate(NODE_IDS)}

# ── Modelo entrenado (singleton — se entrena una vez al importar) ─────────────
_model: DecisionTreeClassifier | None = None


def _dijkstra(start: str, end: str, graph: dict) -> list[str] | None:
    """Ruta de menor costo entre start y end. Retorna None si no existe."""
    dist = {start: 0}
    prev: dict[str, str] = {}
    pq = [(0, start)]

    while pq:
        cost, u = heapq.heappop(pq)
        if u == end:
            break
        if cost > dist.get(u, float('inf')):
            continue
        for v, w in graph[u]:
            new_cost = cost + w
            if new_cost < dist.get(v, float('inf')):
                dist[v] = new_cost
                prev[v] = u
                heapq.heappush(pq, (new_cost, v))

    if end not in prev and start != end:
        return None

    path, node = [], end
    while node != start:
        path.append(node)
        node = prev[node]
    path.append(start)
    return list(reversed(path))


def _generate_dataset(graph: dict) -> tuple[np.ndarray, np.ndarray]:
    """
    Genera el dataset de entrenamiento recorriendo todas las rutas óptimas
    (Dijkstra) entre todos los pares de nodos del grafo.

    Cada paso de cada ruta produce una muestra:
      X[i] = [nodo_actual_idx, destino_idx]
      y[i] = siguiente_nodo_idx
    """
    X, y = [], []
    nodes = list(graph.keys())

    for start in nodes:
        for end in nodes:
            if start == end:
                continue
            path = _dijkstra(start, end, graph)
            if path is None:
                continue
            for i in range(len(path) - 1):
                X.append([NODE_TO_IDX[path[i]], NODE_TO_IDX[end]])
                y.append(NODE_TO_IDX[path[i + 1]])

    return np.array(X), np.array(y)


def _get_model(graph: dict) -> DecisionTreeClassifier:
    """Entrena el modelo la primera vez y lo reutiliza en llamadas posteriores."""
    global _model
    if _model is None:
        X, y = _generate_dataset(graph)
        _model = DecisionTreeClassifier(random_state=42)
        _model.fit(X, y)
    return _model


# ── Función principal ─────────────────────────────────────────────────────────

def run(start: str, end: str, graph: dict) -> dict:
    """
    Ejecuta pathfinding usando DecisionTreeClassifier.

    En cada paso el árbol predice el siguiente nodo basándose en
    [nodo_actual, destino]. Si la predicción no es válida (no adyacente
    o ya visitado), se aplica fallback al vecino no visitado más barato.

    Retorna el mismo formato que los demás algoritmos del proyecto.
    """
    # ── Caso trivial ─────────────────────────────────────────────────────────
    if start == end:
        return {
            "found": True,
            "path": [start],
            "cost": 0,
            "steps": [],
            "visited_count": 1,
            "time_ms": 0.0,
            "stuck_reason": None,
        }

    model = _get_model(graph)
    t_start = time.perf_counter()

    path: list[str] = [start]
    visited: set[str] = {start}
    cost: int = 0
    steps: list[dict] = []
    current: str = start
    stuck_reason: str | None = None

    # ── Bucle de inferencia ───────────────────────────────────────────────────
    while current != end:
        # Vecinos no visitados disponibles
        valid = {n: w for n, w in graph[current] if n not in visited}

        if not valid:
            stuck_reason = "no_unvisited_neighbors"
            break

        # Predicción del árbol
        x = np.array([[NODE_TO_IDX[current], NODE_TO_IDX[end]]])
        predicted_idx  = int(model.predict(x)[0])
        predicted_node = IDX_TO_NODE[predicted_idx]

        # Validar predicción — si no es válida, usar fallback greedy
        used_fallback = predicted_node not in valid
        if used_fallback:
            chosen = min(valid, key=lambda n: valid[n])
        else:
            chosen = predicted_node

        chosen_weight = valid[chosen]

        steps.append({
            "action":        "move",
            "from":          current,
            "to":            chosen,
            "weight":        chosen_weight,
            "predicted":     predicted_node,
            "used_fallback": used_fallback,
            "candidates":    sorted([[n, w] for n, w in valid.items()], key=lambda x: x[1]),
        })

        cost    += chosen_weight
        current  = chosen
        visited.add(chosen)
        path.append(chosen)

    # ── Resultado ─────────────────────────────────────────────────────────────
    found      = current == end
    elapsed_ms = round((time.perf_counter() - t_start) * 1000, 3)

    return {
        "found":         found,
        "path":          path,
        "cost":          cost,
        "steps":         steps,
        "visited_count": len(visited),
        "time_ms":       elapsed_ms,
        "stuck_reason":  stuck_reason,
    }
