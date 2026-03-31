# Examen 2 — Inteligencia Artificial y su Ética

**Maestría en Inteligencia Artificial**
**Roberto Cruz Lozano**

Visualizador interactivo de grafo con implementación de algoritmos de búsqueda para el Examen 2 de la materia IAE.

---

## Estructura del proyecto

```
mia-iae-examen2/
├── frontend/
│   ├── assets/
│   │   └── logoMIA.png                           # Logo de la Maestría (favicon + header)
│   ├── libs/
│   │   └── vis-network.min.js                    # vis.js v9.1.9 (vendorizado, sin CDN)
│   └── index.html                                # Aplicación principal
├── backend/
│   ├── algorithms/
│   │   ├── __init__.py
│   │   ├── hill_climbing.py                      # Hill Climbing greedy
│   │   ├── hill_climbing_backtracking.py         # Hill Climbing con Backtracking
│   │   ├── decision_tree.py                      # Aprendizaje Supervisado — Árbol de Decisión
│   │   └── beam_search.py                        # Beam Search con ancho de haz configurable
│   ├── venv/                                     # Entorno virtual Python (no se commitea)
│   ├── graph.py                                  # Grafo como lista de adyacencia
│   ├── main.py                                   # API FastAPI
│   └── requirements.txt                          # fastapi, uvicorn, scikit-learn, numpy
├── Lista_de_Adyacencia_Grafo_Examen.txt
├── .gitignore
├── CLAUDE.md
└── README.md
```

---

## Grafo

- **32 nodos:** 1–14, 15a, 15b, 16–31
- **39 aristas bidireccionales** con peso
- Único puente entre los dos subgrafos: arista `6 — 14` (peso 77)
- Los nodos 15a y 15b son distintos (ambos etiquetados "15" en la imagen original)
- No existe arista directa entre 15a y 15b
- Referencia completa: `Lista_de_Adyacencia_Grafo_Examen.txt`

---

## Ejecutar el proyecto

### Backend

```bash
cd backend
venv/bin/uvicorn main:app --reload --port 8000
```

> Primera vez: `python3 -m venv venv && venv/bin/pip install -r requirements.txt`

### Frontend

```bash
cd frontend
python3 -m http.server 5500
```

Abrir **http://localhost:5500**

---

## Frontend

Aplicación HTML/CSS/JS pura, sin framework ni bundler. Tema visual: Catppuccin Mocha.

### Características

**Visualización del grafo**
- Renderizado interactivo con vis-network (vendorizado, sin CDN)
- Arrastrar nodos — posición guardada automáticamente en `localStorage`
- Canvas acotado (sin paneo ni zoom infinito)

**Controles en el header**
- Slider tamaño de fuente — nodos
- Slider tamaño de fuente — pesos de aristas
- Slider tamaño de fuente — descripción del algoritmo

**Panel de control** (esquina superior izquierda)
- Selector de algoritmo con botón `ℹ` que despliega descripción y consideraciones
- Slider β — ancho de haz (1–5), visible solo al seleccionar Beam Search
- Selector de nodo inicio → se pinta **verde** en el grafo
- Selector de nodo fin → se pinta **rojo** en el grafo
- Botón **Ejecutar** (habilitado solo con algoritmo + dos nodos distintos)
- Botón **Limpiar resultado**
- Cambiar algoritmo, nodo inicio o nodo fin limpia el resultado anterior automáticamente

**Panel de estadísticas** (esquina superior derecha)
- Resultado (encontrado / no encontrado)
- Costo total, nodos visitados, longitud de ruta, tiempo de ejecución
- Ancho β utilizado (solo para Beam Search)
- Camino completo con formato `nodo → nodo → ...`

**Visualización del resultado en el grafo**
- Nodos del camino pintados en **amarillo**
- Aristas del camino resaltadas en **amarillo** (grosor mayor)
- Nodo atascado pintado en **naranja**
- Nodos inicio/fin mantienen su color verde/rojo

---

## Backend

API REST en Python con FastAPI.

### Endpoints

```
GET  /api/health
POST /api/run   { "algorithm": "...", "start": "1", "end": "14", "beam_width": 3 }
```

> `beam_width` es opcional (default 3), solo usado por `beam_search`.

**Respuesta de `/api/run`:**
```json
{
  "algorithm": "hill_climbing",
  "start": "1",
  "end": "14",
  "found": true,
  "path": ["1", "2", "3", "5", "6", "14"],
  "cost": 206,
  "steps": [
    {
      "action": "move",
      "from": "1",
      "to": "2",
      "weight": 28,
      "candidates": [["2", 28], ["4", 28], ["8", 61]]
    }
  ],
  "visited_count": 6,
  "time_ms": 0.016,
  "stuck_reason": null
}
```

- HC con Backtracking incluye además entradas con `"action": "backtrack"` y campo `cost_undone`.
- Decision Tree incluye campos `predicted` y `used_fallback` en cada paso.
- Beam Search incluye campo `beam_width` en la respuesta y pasos con `"action": "expand"`.

---

## Algoritmos

| Algoritmo | Clave API | Estado | Garantiza ruta | Garantiza óptimo |
|-----------|-----------|--------|---------------|-----------------|
| Hill Climbing | `hill_climbing` | ✅ | No | No |
| Hill Climbing con Backtracking | `hill_climbing_backtracking` | ✅ | Sí | No |
| Aprendizaje Supervisado — Árbol de Decisión | `decision_tree` | ✅ | No | No |
| Beam Search | `beam_search` | ✅ | No | No |

### Hill Climbing

Elige en cada paso el vecino no visitado con menor peso (greedy local). Puede quedarse atascado en nodos hoja o callejones sin salida. No garantiza encontrar el destino ni la ruta de menor costo.

### Hill Climbing con Backtracking

Misma estrategia greedy que HC puro. Cuando se atasca, retrocede al nodo anterior y prueba el siguiente candidato. Al retroceder deshace el costo — el costo siempre refleja solo la ruta activa. Garantiza encontrar una ruta si existe; no garantiza que sea la de menor costo.

### Aprendizaje Supervisado — Árbol de Decisión

`DecisionTreeClassifier` entrenado con rutas óptimas generadas por Dijkstra sobre el propio grafo. Aprende reglas del tipo: *"si estoy en el nodo X y mi destino es Y → ir a Z"*. En inferencia aplica esas reglas sin ejecutar ningún algoritmo de búsqueda.

- **Classifier, no Regressor:** predice el siguiente nodo como clase discreta. Un Regressor predice valores continuos ("nodo 3.7"), lo cual no tiene sentido aquí.
- **Data leaking transparente:** el dataset se genera con Dijkstra sobre el mismo grafo. Si el grafo cambiara, el modelo fallaría. Es académicamente válido: representa conocimiento del dominio, no del conjunto de prueba.
- **Fallback greedy:** si la predicción no es un vecino válido o ya fue visitado, se elige el vecino no visitado de menor peso.
- **Tiempo reportado:** solo inferencia — el entrenamiento ocurre una vez al arrancar el servidor (singleton).

### Beam Search

Búsqueda heurística que explora el grafo nivel por nivel manteniendo las β rutas parciales de menor costo acumulado. En cada iteración expande todas las rutas del haz, genera sus sucesores y conserva solo los β mejores — podando el resto. No se permite repetición de nodos dentro de una misma ruta.

- **β configurable (1–5)** desde el panel de control del frontend.
- **β=1** equivale a Hill Climbing greedy.
- **No es completo:** un β pequeño puede descartar la única ruta al destino. Si no encuentra solución, incrementar β.
- **No es óptimo:** puede conservar rutas baratas al inicio que terminan en callejones sin salida.
- **Heurística:** costo acumulado (el grafo no tiene coordenadas espaciales para usar distancia euclidiana).
