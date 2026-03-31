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
│   │   └── logoMIA.png                      # Logo de la Maestría (favicon + header)
│   ├── libs/
│   │   └── vis-network.min.js               # vis.js v9.1.9 (vendorizado, sin CDN)
│   └── index.html                           # Aplicación principal
├── backend/
│   ├── algorithms/
│   │   ├── __init__.py
│   │   ├── hill_climbing.py                 # Hill Climbing greedy
│   │   └── hill_climbing_backtracking.py    # Hill Climbing con Backtracking
│   ├── venv/                                # Entorno virtual Python (no se commitea)
│   ├── graph.py                             # Grafo como lista de adyacencia
│   ├── main.py                              # API FastAPI
│   └── requirements.txt                     # fastapi, uvicorn[standard]
├── Lista_de_Adyacencia_Grafo_Examen.txt
├── logoMIA.png
├── .gitignore
├── CLAUDE.md
└── README.md
```

---

## Grafo

- **32 nodos:** 1–14, 15a, 15b, 16–31
- **39 aristas bidireccionales** con peso
- Único puente entre los dos subgrafos: arista `6 — 14` (peso 77)
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

Aplicación HTML/CSS/JS pura, sin framework ni bundler.

### Características

**Visualización del grafo**
- Renderizado interactivo con vis-network
- Arrastrar nodos — posición guardada automáticamente en `localStorage`
- Canvas acotado (sin paneo ni zoom infinito)

**Controles en el header**
- Slider tamaño de fuente — nodos
- Slider tamaño de fuente — pesos de aristas
- Slider tamaño de fuente — descripción del algoritmo

**Panel de control** (esquina superior izquierda del grafo)
- Selector de algoritmo con botón `ℹ` que despliega descripción y consideraciones
- Selector de nodo inicio → se pinta **verde** en el grafo
- Selector de nodo fin → se pinta **rojo** en el grafo
- Botón **Ejecutar** (habilitado solo con algoritmo + dos nodos distintos)
- Botón **Limpiar resultado**
- Cambiar nodo inicio/fin limpia el resultado anterior automáticamente

**Panel de estadísticas** (esquina superior derecha del grafo)
- Resultado (encontrado / no encontrado)
- Costo total, nodos visitados, longitud de ruta, tiempo de ejecución
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
POST /api/run   { "algorithm": "...", "start": "1", "end": "14" }
```

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

Los pasos de HC con Backtracking incluyen adicionalmente entradas con `"action": "backtrack"`.

---

## Algoritmos

| Algoritmo | Clave API | Estado | Garantiza ruta | Garantiza óptimo |
|-----------|-----------|--------|---------------|-----------------|
| Hill Climbing | `hill_climbing` | ✅ | No | No |
| Hill Climbing con Backtracking | `hill_climbing_backtracking` | ✅ | Sí | No |
| Beam Search | `beam_search` | 🔜 | No | No |
| Aprendizaje Supervisado | `supervised` | 🔜 | — | — |

### Notas sobre los algoritmos implementados

**Hill Climbing**
- Elige en cada paso el vecino no visitado con menor peso (greedy local)
- Puede quedarse atascado en nodos hoja o callejones sin salida
- No garantiza encontrar el destino ni la ruta de menor costo

**Hill Climbing con Backtracking**
- Misma estrategia greedy que HC puro
- Cuando se atasca, retrocede al nodo anterior y prueba el siguiente candidato
- Al retroceder deshace el costo — el costo siempre refleja solo la ruta activa
- Garantiza encontrar una ruta si existe; no garantiza que sea la de menor costo
