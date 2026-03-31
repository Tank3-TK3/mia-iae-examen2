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
│   │   └── logoMIA.png              # Logo de la Maestría (favicon + header)
│   ├── libs/
│   │   └── vis-network.min.js       # vis.js v9.1.9 (vendorizado, sin CDN)
│   └── index.html                   # Aplicación principal
├── backend/
│   ├── algorithms/
│   │   ├── __init__.py
│   │   └── hill_climbing.py         # Hill Climbing implementado
│   ├── venv/                        # Entorno virtual Python (no se commitea)
│   ├── graph.py                     # Grafo como lista de adyacencia
│   ├── main.py                      # API FastAPI
│   └── requirements.txt             # fastapi, uvicorn[standard]
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
- Un único puente entre los dos subgrafos: arista `6 — 14` (peso 77)
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
- Botón **Ejecutar** (se habilita con algoritmo + dos nodos distintos seleccionados)
- Botón **Limpiar resultado**
- Cambiar nodo inicio/fin limpia el resultado anterior automáticamente

**Panel de estadísticas** (esquina superior derecha del grafo)
- Resultado (encontrado / no encontrado)
- Costo total, nodos visitados, longitud de ruta, tiempo de ejecución
- Camino completo con formato `nodo → nodo → ...`

**Visualización del resultado**
- Nodos del camino pintados en **amarillo**
- Aristas del camino resaltadas en **amarillo** (grosor mayor)
- Nodo atascado pintado en **naranja**
- Nodos inicio/fin mantienen su color verde/rojo

---

## Backend

API REST en Python con FastAPI.

### Endpoint principal

```
POST /api/run
Body: { "algorithm": "hill_climbing", "start": "1", "end": "14" }
```

**Respuesta:**
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

---

## Algoritmos

| Algoritmo | Estado | Tipo | Descripción |
|-----------|--------|------|-------------|
| Hill Climbing | ✅ Implementado | Local / Greedy | En cada paso elige el vecino no visitado con menor peso de arista |
| Beam Search | 🔜 Próximamente | Informado | Mantiene los k mejores candidatos en cada nivel |
| Aprendizaje Supervisado | 🔜 Próximamente | Supervisado | Modelo entrenado para predecir el siguiente nodo en la ruta óptima |

### Consideraciones de Hill Climbing
- Puede quedar atascado en nodos hoja que no sean el destino
- No garantiza encontrar la ruta óptima global
- Puede fallar si el camino exige pasar por aristas costosas localmente
- El único puente entre subgrafos es `6—14` (peso 77)
