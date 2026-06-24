# AGENTS.md

Guide for AI coding agents (and humans) working on **vibe_arch**.
Read this before making any change.

---

## 1. What this project is

Vibe_arch fights "vibe coding" — developers blindly accepting AI-generated
architecture without understanding it. It inverts the paradigm: the AI does **not**
give you an architecture. It discovers two real open-source repos that solve your
problem, animates their blueprints, and forces you to actively choose between them
component by component. What you build is yours, grounded in how real engineers ship.

### THE cardinal rule

> **Architecture is spatial. NEVER output text files, Markdown, or Mermaid.js as the
> deliverable.** The UX MUST be a highly interactive, node-based visual canvas
> (React Flow) in the browser. Diagrams-as-text are a hard failure of intent.

## 2. Repository layout

```
Vibe_arch/
├── backend/         # FastAPI "brain" — discovery, scoring, analysis, archguard, scaffold
│   └── app/
│       ├── main.py          # FastAPI app + route registration
│       ├── config.py        # env loading (Settings)
│       ├── models.py        # Pydantic schemas
│       ├── llm/             # provider-pluggable LLM layer (GLM default)
│       ├── discovery/       # GitHub client, quality scoring, tree extractor
│       ├── analyzer/        # blueprint, comparator, archguard generators
│       └── routes/          # REST endpoints
├── cli/             # Typer CLI — interrogation + one-command launcher
│   ├── vibe_arch.py         # entrypoint (python -m vibe_arch)
│   └── interrogator.py      # vague-idea -> scale/constraint Q&A loop
├── frontend/        # React + Vite + @xyflow/react (TypeScript)
│   └── src/
│       ├── canvas/          # reusable React Flow canvas, custom node/edge, timeline
│       ├── stages/          # DiffStage (3 canvases), DecisionPanel, FinalMap
│       ├── layout/          # elkjs auto-layout hook
│       └── export/          # PNG/PDF/scaffold/archguard exporters
├── pyproject.toml   # uv-managed Python deps (backend + CLI in one project)
├── uv.lock
└── AGENTS.md        # this file
```

## 3. Environment variables

Copy `.env.example` to `.env` and fill in:

| Var | Purpose |
|-----|---------|
| `GITHUB_TOKEN` | GitHub PAT — required (avoids 60 req/hr anonymous limit) |
| `LLM_PROVIDER` | `glm` (default) \| `gemini` \| `groq` |
| `GLM_API_KEY` | Zhipu/GLM key (default provider) |
| `GEMINI_API_KEY` | Google Gemini key (if provider=gemini) |
| `GROQ_API_KEY` | Groq key (if provider=groq) |

## 4. Commands

All Python commands run through **`uv`** (do NOT use bare `pip`/`python` — use
`uv run` so the locked environment is used).

### Install / sync deps
```bash
uv sync                      # backend + CLI deps from pyproject.toml / uv.lock
cd frontend && npm install   # frontend deps
```

### Run the backend (dev)
```bash
uv run uvicorn backend.app.main:app --reload --port 8000
```

### Run the frontend (dev)
```bash
cd frontend && npm run dev
```

### One-command launch (production of the MVP flow)
```bash
uv run python -m vibe_arch "your idea here"
# starts the FastAPI backend, opens the browser UI
```

### Lint / format / typecheck
```bash
uv run ruff check .          # lint
uv run ruff format .         # format
cd frontend && npm run lint  # frontend lint (eslint)
cd frontend && npm run build # frontend typecheck (tsc) via vite build
```

### Tests
```bash
uv run pytest                # backend tests
cd frontend && npm run test  # frontend tests (when added)
```

> **Always run lint + typecheck after non-trivial changes.** If you add a new
> command, document it here.

## 5. Commit convention (IMPORTANT)

**Push every single complete, self-contained component individually — never a whole
feature at once.** The user reviews each commit to understand how each piece works.

- One logical, complete, runnable unit per commit.
- Clear, intent-revealing message in the form
  `<area>: <what>`, e.g. `backend: repo quality scoring`, `frontend: 3-canvas visual diff stage`.
- Push to `main` after each commit.
- Do NOT bundle unrelated changes; if a commit needs a fixup, make a new commit
  (don't rewrite history once pushed).

## 6. Architecture & conventions

### Backend (Python)
- FastAPI + Pydantic v2. Async everywhere (`httpx.AsyncClient`).
- LLM layer is **provider-pluggable**: `llm/base.py` defines the interface;
  `glm.py` is the default. Switch via `LLM_PROVIDER` env. Never hardcode a provider.
- GitHub discovery ranks by **engineering quality**, not stars. See
  `discovery/scoring.py` for the weighted formula (maintenance, ownership, bus
  factor, release cadence, tests, CI, arch cleanliness). Disqualifiers: archived,
  fork, no license.
- The dependency graph in `archguard.json` is **closed-world**: `depends_on` is the
  *entire* allowed edge set — any edge not present is a violation.

### Frontend (TypeScript)
- `@xyflow/react` v12. `nodeTypes`/`edgeTypes` MUST be defined at module scope
  (or `useMemo`) — inline objects remount nodes. This is a hard gotcha.
- One `ReactFlowProvider` per canvas (left / center / right are independent).
- Run **elkjs layout once** over the full graph, then reveal nodes/edges
  incrementally via the timeline hook — never re-layout per animation frame.
- Stable node ids across canvases (never let React Flow auto-generate ids for nodes
  that move between canvases).
- Dark theme via `colorMode="dark"` + `--xy-*` CSS var overrides.

### General
- No comments unless asked.
- Follow existing style; mimic neighboring code.
- Never commit secrets. `.env` is gitignored.

## 7. The 6-stage UX flow (spec)

1. **CLI input + strict constraints** — vague ideas trigger scale/constraint Q&A.
2. **Smart discovery** — find two top-tier OS repos; rank by engineering quality.
3. **Visual diff** — dark UI, 3 React Flow canvases; left/right animate the blueprints
   like a time-lapse.
4. **Active decision gates** — same approach → auto-add to center; critical diff →
   freeze UI, slide-up trade-off panel, user must accept/reject.
5. **Final map** — left/right fade away; center = polished map; hover tooltips show
   "why" + "what was rejected."
6. **Exports** — PDF/Image of diagram; scaffold base folder structure; strict
   `archguard.json` constraining future AI agents.

## 8. archguard.json schema (6 sections)

`meta` · `layers` + `layer_policy` · `components[]` · `rules[]` · `decisions[]` ·
`tech_stack[]` + `scaffold_manifest{}`. See `backend/app/analyzer/archguard.py` for
the generator. Closed-world dependency edges; 26 validation invariants.
