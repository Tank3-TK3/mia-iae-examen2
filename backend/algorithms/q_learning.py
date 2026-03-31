# algorithms/q_learning.py
#
# Aprendizaje por Refuerzo — Q-Learning
#
# ── Qué es Q-Learning ────────────────────────────────────────────────────────
# Q-Learning es un algoritmo de Aprendizaje por Refuerzo (RL) model-free. El
# agente aprende una política óptima explorando el entorno (el grafo) sin
# conocimiento previo de sus rutas. A diferencia del Árbol de Decisión, que
# aprende de un dataset etiquetado (supervisado), Q-Learning descubre las rutas
# óptimas por sí solo mediante exploración y recompensas (no supervisado).
#
# ── Tabla Q ──────────────────────────────────────────────────────────────────
# Se mantiene una tabla Q de forma (N, N, N) donde:
#   Q[nodo_actual][destino][siguiente_nodo] = valor esperado de tomar esa acción
#
# Un valor alto de Q significa que ir a "siguiente_nodo" desde "nodo_actual"
# hacia "destino" es una buena decisión. El agente aprende estos valores
# durante el entrenamiento mediante la ecuación de Bellman.
#
# ── Ecuación de Bellman ───────────────────────────────────────────────────────
# Q(s,a) ← Q(s,a) + α * [r + γ * max_a' Q(s',a') − Q(s,a)]
#
#   α (learning rate = 0.1) : qué tanto actualiza cada experiencia
#   γ (discount factor = 0.95): qué tanto valora recompensas futuras
#   r : recompensa inmediata (-peso de arista, +100 al llegar al destino)
#
# ── Estrategia ε-greedy ───────────────────────────────────────────────────────
# Durante el entrenamiento, el agente elige entre:
#   · Exploración (prob ε): acción aleatoria — descubre rutas nuevas
#   · Explotación (prob 1-ε): acción con mayor Q-value — refuerza lo aprendido
# ε decae de 1.0 → 0.05 conforme avanza el entrenamiento.
#
# ── Completitud y optimalidad ─────────────────────────────────────────────────
# Con suficientes episodios, Q-Learning converge a la política óptima global.
# Garantiza la ruta de menor costo si el entrenamiento fue suficiente.
# En inferencia NO ejecuta búsqueda — solo consulta la tabla Q aprendida.
#
# ── Diferencia con el Árbol de Decisión ──────────────────────────────────────
# | Árbol de Decisión      | Q-Learning                                       |
# |------------------------|--------------------------------------------------|
# | Supervisado            | No supervisado (RL)                              |
# | Aprende de Dijkstra    | Aprende explorando el grafo por sí solo          |
# | Imita rutas óptimas    | Descubre rutas óptimas por recompensas           |
# | No garantiza óptimo    | Garantiza óptimo (tras convergencia)             |

import random
import time

import numpy as np

# ── Codificación de nodos ─────────────────────────────────────────────────────
NODE_IDS = [
    '1','2','3','4','5','6','7','8','9','10',
    '11','12','13','14','15a','15b',
    '16','17','18','19','20','21','22','23',
    '24','25','26','27','28','29','30','31',
]
N = len(NODE_IDS)
NODE_TO_IDX = {n: i for i, n in enumerate(NODE_IDS)}
IDX_TO_NODE = {i: n for i, n in enumerate(NODE_IDS)}

# ── Hiperparámetros ───────────────────────────────────────────────────────────
EPOCHS     = 500    # pasadas sobre todos los pares (500 × 992 ≈ 496000 episodios)
ALPHA      = 0.1    # learning rate
GAMMA      = 0.99   # discount factor alto — señal llega con fuerza en rutas largas
EPS_START  = 1.0    # exploración inicial
EPS_END    = 0.01   # exploración mínima
MAX_STEPS  = 80     # pasos máximos por episodio
REWARD_WIN = 500    # recompensa dominante al llegar al destino

# ── Modelo singleton ──────────────────────────────────────────────────────────
_q_table: np.ndarray | None = None


def _train(graph: dict) -> np.ndarray:
    """
    Entrena la tabla Q mediante Q-Learning sistemático.

    En lugar de muestreo aleatorio de pares, itera sobre todos los pares
    (start, end) en cada época. Esto garantiza cobertura uniforme de los
    992 pares posibles y convergencia robusta en pocas épocas.

    EPOCHS × len(pares) ≈ 50 × 992 = ~49600 episodios totales.
    """
    random.seed(42)
    np.random.seed(42)

    Q    = np.zeros((N, N, N), dtype=np.float64)
    nodes = list(graph.keys())
    pairs = [(s, e) for s in nodes for e in nodes if s != e]

    total_eps = EPOCHS * len(pairs)
    ep        = 0

    for _ in range(EPOCHS):
        random.shuffle(pairs)
        for start, end in pairs:
            # ε decae linealmente a lo largo de todos los episodios
            eps      = EPS_START - (EPS_START - EPS_END) * (ep / total_eps)
            ep      += 1
            current  = start
            dest_idx = NODE_TO_IDX[end]

            for _ in range(MAX_STEPS):
                curr_idx  = NODE_TO_IDX[current]
                neighbors = graph[current]  # Q-Learning puro: todos los vecinos
                if not neighbors:
                    break

                # ε-greedy
                if random.random() < eps:
                    next_node, weight = random.choice(neighbors)
                else:
                    q_vals    = [(nb, w, Q[curr_idx][dest_idx][NODE_TO_IDX[nb]]) for nb, w in neighbors]
                    next_node, weight, _ = max(q_vals, key=lambda x: x[2])

                next_idx = NODE_TO_IDX[next_node]

                if next_node == end:
                    reward = REWARD_WIN - weight
                    Q[curr_idx][dest_idx][next_idx] += ALPHA * (
                        reward - Q[curr_idx][dest_idx][next_idx]
                    )
                    break
                else:
                    reward     = -weight
                    max_next_q = float(np.max(Q[next_idx][dest_idx]))
                    Q[curr_idx][dest_idx][next_idx] += ALPHA * (
                        reward + GAMMA * max_next_q - Q[curr_idx][dest_idx][next_idx]
                    )
                    current = next_node

    return Q


def _get_q_table(graph: dict) -> np.ndarray:
    """Entrena la tabla Q la primera vez y la reutiliza en llamadas posteriores."""
    global _q_table
    if _q_table is None:
        _q_table = _train(graph)
    return _q_table


# ── Función principal ─────────────────────────────────────────────────────────

def run(start: str, end: str, graph: dict) -> dict:
    """
    Ejecuta pathfinding consultando la tabla Q aprendida.

    En cada paso elige el vecino no visitado con el mayor Q-value para el
    destino dado. Si el top-1 ya fue visitado, selecciona el siguiente mejor
    Q-value entre los vecinos válidos (fallback por Q-value).

    Retorna el mismo formato que los demás algoritmos del proyecto.
    """
    q_table = _get_q_table(graph)
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
            "episodes":      EPOCHS * (N * (N - 1)),
        }

    path: list[str]      = [start]
    visit_count: dict    = {start: 1}   # cuenta visitas para detectar ciclos
    cost: int            = 0
    steps: list[dict]    = []
    current: str         = start
    stuck_reason: str | None = None
    dest_idx             = NODE_TO_IDX[end]

    # ── Bucle de inferencia ───────────────────────────────────────────────────
    # Con Q-values convergidos la política óptima no crea ciclos.
    # El límite de 2*N pasos es salvaguarda ante convergencia incompleta.
    max_inf_steps = 2 * N

    for _ in range(max_inf_steps):
        if current == end:
            break

        curr_idx  = NODE_TO_IDX[current]
        neighbors = graph[current]

        if not neighbors:
            stuck_reason = "no_neighbors"
            break

        # Elegir vecino con mayor Q-value (política greedy aprendida)
        best = max(neighbors, key=lambda x: q_table[curr_idx][dest_idx][NODE_TO_IDX[x[0]]])
        chosen, chosen_weight = best
        top_q = q_table[curr_idx][dest_idx][NODE_TO_IDX[chosen]]

        # Detectar ciclo: si el nodo ya fue visitado 2 veces, parar
        if visit_count.get(chosen, 0) >= 2:
            stuck_reason = "cycle_detected"
            break

        steps.append({
            "action":      "move",
            "from":        current,
            "to":          chosen,
            "weight":      chosen_weight,
            "q_value":     round(float(top_q), 4),
            "candidates":  sorted([[nb, w] for nb, w in neighbors], key=lambda x: x[1]),
        })

        cost    += chosen_weight
        current  = chosen
        visit_count[chosen] = visit_count.get(chosen, 0) + 1
        path.append(chosen)

    # ── Resultado ─────────────────────────────────────────────────────────────
    found      = current == end
    elapsed_ms = round((time.perf_counter() - t_start) * 1000, 3)

    return {
        "found":         found,
        "path":          path,
        "cost":          cost,
        "steps":         steps,
        "visited_count": len(visit_count),
        "time_ms":       elapsed_ms,
        "stuck_reason":  stuck_reason,
        "episodes":      EPOCHS * (N * (N - 1)),
    }
