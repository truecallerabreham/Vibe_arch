---
title: Vibe Arch - Plan
type: feat
date: 2026-06-26
topic: vibe-arch-oss-comparison
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
product_contract_source: ce-brainstorm
execution: code
---

## Goal Capsule

- **Objective:** Build a tool that takes a plain-language description of what someone wants to build (or two URLs), discovers/extracts architectures from relevant open-source repos, renders them side-by-side on an interactive visual canvas, and lets the user compare and choose components deliberately — teaching system design through active comparison
- **Product authority:** ce-brainstorm
- **Open blockers:** None

## Product Contract

Product Contract unchanged from requirements-only phase.

### Summary

Vibe Arch inverts the AI-coding paradigm. Given a description of what someone wants to build, it discovers two top-tier open-source repositories that solve the same problem, extracts their architectures via a hybrid AST+LLM pipeline, renders them side-by-side on an interactive visual canvas, and forces the user to actively choose between components with understanding. The tool never outputs text diagrams, markdown, or Mermaid — architecture is spatial, and the canvas is the interface.

### Problem Frame

Entry and mid-level engineers lack exposure to real-world system design. When they need to build a project, they either accept a single brittle AI-generated architecture or have no tools to understand how established open-source projects solve the same problems. Existing tools (GitDiagram, Repomix) extract architecture from a single given repo but none discover, compare, or teach. The gap is not in architecture visualization — it's in architecture education through deliberate comparison.

### Key Decisions

- **Hybrid AST+LLM extraction over pure LLM** — tree-sitter provides deterministic ground truth on what exists (symbols, imports, class hierarchies); the LLM only interprets relationships between real symbols. Every extracted component references a real file path, eliminating hallucinated modules at the source.
- **Curated repo index over real-time GitHub search** — a daily-refreshed database of top repos by topic enables fast hybrid retrieval (BM25 + embeddings) without GitHub's 30 req/min rate limit. GitHub Search API supplements long-tail or niche queries.
- **Target entry/mid-level engineers, not seniors** — the comparison UX is an education tool first. "Popular = proven = well-documented" is a feature for learners who cannot yet judge architecture quality independently.
- **Canvas over text output** — architecture is spatial. Rendering two blueprints side-by-side forces the user to visually compare, trace dependencies, and engage in a way prose or static diagrams cannot achieve.
- **URL-first MVP, search later** — v0.1 accepts two GitHub URLs instead of natural language search. The discovery/search pipeline is built in v0.2 after the core extraction + canvas is proven. This avoids building two hard problems simultaneously.

### Requirements

**Discovery**

- R1. Accept a plain-language description of what the user wants to build
- R2. Discover two open-source repositories relevant to the description via a two-stage hybrid retrieval pipeline: BM25 + semantic embeddings over a pre-indexed repo corpus for recall, then LLM listwise reranking with engineer-quality signals for precision

**Architecture Extraction**

- R3. Extract each repo's architecture via a hybrid AST+LLM pipeline where tree-sitter produces deterministic facts (files, symbols, imports, call edges) and the LLM produces semantic interpretation of component roles — every node must reference a real path in the file tree
- R4. Validate every extracted component path against the actual file tree; reject any hallucinated path and retry with corrected constraints

**Comparison Canvas**

- R5. Render both architectures side-by-side on an interactive node-based canvas with pan/zoom, minimap, and component drill-down
- R6. Show confidence indicators on every inferred relationship: verified by import graph (green), strongly inferred by LLM (yellow), unverifiable (red)
- R7. Let the user click any component to see what it does, why it exists, and which files implement it
- R8. Let the user actively select individual components from either architecture to compose their own design

**Normalization**

- R9. Normalize both architectures into a shared component schema for fair side-by-side comparison (LLM-driven with user override — "handlers/" and "routes/" both map to "API Layer")

### Scope Boundaries

**Deferred for later**
- Multi-user collaboration, auth, team workspaces
- Direct code generation from selected components
- User-contributed custom repos for comparison

**Outside this product's identity**
- Being a code generation tool (output is a decision record, not a codebase)
- Being an AI architecture generator from scratch (the tool finds existing solutions)
- Being a generic diagramming tool (the canvas is specific to OSS comparison)

### Dependencies / Assumptions

- Tree-sitter has parsers for the languages encountered in target repos (100+ languages supported)
- GitHub API permits indexing of public repo metadata at daily batch scale
- LLM accuracy for architecture interpretation reaches 85-95% with file-tree validation in place
- Entry/mid-level engineers find side-by-side architecture comparison more valuable than a single generated architecture
- A daily-refreshed index of top repos provides sufficient freshness for OSS discovery
- React Flow handles the canvas requirements (proven at 37.3k stars, used by Stripe/Typeform)

### Sources / Research

- GitDiagram (15.7k stars) proves single-repo LLM architecture extraction with file-tree validation works in production
- No existing tool does side-by-side architecture comparison (confirmed against Repomix, Gitingest, Gitvize, RepoMapr, CodeBoarding)
- Two-stage hybrid retrieval (BM25 + dense embeddings → cross-encoder reranker) is the industry consensus for code search (Sourcegraph, CoQuIR arXiv:2506.11066)
- ArchAgent paper (arXiv 2601.13007, 2026) validates LLM-based architecture recovery with statistical significance
- Qiu et al. (CSCW 2019) identifies README quality, recent activity, issue response time as top OSS selection signals
- "Building an Interactive Architecture Canvas with React Flow" (2026) confirms production viability for 8+ custom node types

---

## Planning Contract

### Key Technical Decisions

- **KTD1. React + Vite + TypeScript frontend** — React Flow requires React. Vite provides fast dev server and optimized builds. TypeScript catches canvas interaction bugs at compile time.
- **KTD2. Python FastAPI backend with async endpoints** — architecture extraction is I/O-bound (GitHub API calls, LLM API calls). Async handlers keep the server responsive during long-running extractions. Background tasks via `asyncio.create_task` or `BackgroundTasks`.
- **KTD3. tree-sitter Python bindings for AST** — the `tree_sitter` pip package provides deterministic parsing for 100+ languages. No hallucination on what exists. Output: JSON symbol graph with file paths.
- **KTD4. SQLite for local repo index** — no external database dependency for v0.1-v0.2. SQLite with FTS5 provides BM25 search out of the box. Embeddings stored as BLOBs. Upgrade to PostgreSQL/Pgvector when multi-user is needed.
- **KTD5. SSE (Server-Sent Events) for long extractions** — architecture extraction takes 10-60 seconds per repo. SSE streams progress updates to the frontend. Avoids WebSocket complexity for one-way progress streaming.
- **KTD6. React Flow for the canvas** — custom node types for each architecture component (service, database, API, queue, CLI). Edge routing for dependency relationships. Minimap for large-scale navigation. Proven at production scale.
- **KTD7. Claude API as primary LLM provider** — best-in-class for code understanding and structured JSON output (2026 benchmarks). Gemini as fallback. Configurable via `LLM_PROVIDER` env var.

### Technical Architecture

```
frontend/                    # React + Vite + TypeScript
  src/
    canvas/                  # React Flow components
    components/              # UI components (search, sidebar, details panel)
    api/                     # Backend API client
    types/                   # Shared TypeScript types

backend/                     # Python FastAPI
  app/
    api/                     # API routes
    services/                # Business logic
      fetcher.py             # GitHub repo fetching
      ast_extractor.py       # Tree-sitter extraction
      llm_interpreter.py     # LLM architecture interpretation
      validator.py           # File-tree validation
      normalizer.py          # Cross-repo normalization
      indexer.py             # Repo index building & search
    models/                  # Pydantic models
    config.py                # Settings (env vars)

cli/                         # Typer CLI (vibe-arch command)

scripts/
  index_repos.py             # Daily batch repo indexing
```

### Sequencing

The build is organized in three phases to ship value incrementally:

**Phase 1 — Core Extraction + Canvas (v0.1)**
- User pastes two GitHub URLs
- Backend fetches, extracts AST, runs LLM interpretation, validates
- Frontend renders side-by-side React Flow canvas
- User clicks components, sees details, selects components

**Phase 2 — Discovery & Indexing (v0.2)**
- Daily batch indexing of top repos
- Natural language search with BM25 + embeddings
- LLM reranking for precision
- Search UI in frontend

**Phase 3 — Normalization + Polish (v0.3)**
- Cross-repo normalization into shared schema
- Architecture decision record export
- Confidence scoring refinement
- UX polish and edge case hardening

---

## Implementation Units

### U1. Project Scaffolding

**Goal:** Set up the project structure, install dependencies, and establish the dev loop for both frontend and backend.

**Files:**
- `pyproject.toml` — update dependencies (add `tree-sitter`, `httpx`, `openai`, `anthropic`, `pydantic-settings`)
- `frontend/package.json` — create with React + Vite + TypeScript + React Flow + Tailwind
- `frontend/vite.config.ts`
- `frontend/tsconfig.json`
- `frontend/tailwind.config.js`
- `frontend/src/main.tsx` — React entry point
- `backend/app/__init__.py`
- `backend/app/config.py` — settings via `pydantic-settings` (GITHUB_TOKEN, LLM_PROVIDER, API keys)
- `backend/app/models/` — Pydantic models for API contracts
- `Makefile` or `scripts/dev.sh` — unified dev command (backend + frontend)

**Test scenarios:**
- U1-T1. Dev server starts and frontend loads at localhost:5173
- U1-T2. Backend starts at localhost:8000 and `/health` returns 200
- U1-T3. Frontend can call backend via proxy (CORS configured)

**Patterns to follow:**
- `pyproject.toml` uses hatchling as build backend (existing convention)
- `.env.example` convention for required env vars (existing convention)

---

### U2. GitHub Fetcher Service

**Goal:** Fetch repository metadata, file tree, and file contents from GitHub API. Handle rate limiting and pagination.

**Files:**
- `backend/app/services/fetcher.py`
- `backend/app/models/repo.py` — `RepoMetadata`, `FileNode`, `FileTree`
- `backend/tests/test_fetcher.py`

**Details:**
- Accept a GitHub URL and parse `owner/repo`
- Fetch repo metadata (description, stars, topics, language, last commit date, contributors count)
- Fetch the full file tree via GitHub Contents API or Git Trees API
- Fetch key files: README, `package.json`/`Cargo.toml`/`pyproject.toml`, config files
- Cache fetched data in memory with TTL (avoid re-fetching same repo in same session)
- Handle rate limits with exponential backoff

**Test scenarios:**
- U2-T1. Fetch a known public repo returns valid metadata
- U2-T2. File tree contains expected top-level directories
- U2-T3. Invalid URL returns 400 error
- U2-T4. Rate-limited request retries with backoff
- U2-T5. README is parsed and returned as text

---

### U3. AST Extraction Engine

**Goal:** Parse repository source files with tree-sitter and produce a deterministic symbol graph (classes, functions, imports, call edges).

**Files:**
- `backend/app/services/ast_extractor.py`
- `backend/app/models/ast.py` — `SymbolGraph`, `SymbolNode`, `ImportEdge`, `ClassHierarchy`
- `backend/tests/test_ast_extractor.py`
- `backend/tests/fixtures/sample_repo/` — small test repos for deterministic testing

**Details:**
- Detect language for each file based on extension
- Load the correct tree-sitter parser for each language
- Extract: function/class definitions, import/require statements, function calls within same file
- Build a symbol graph: nodes = symbols (with file path + line number), edges = import relationships + call relationships
- Handle incremental parsing for large files (parse by top-level blocks)
- Exit gracefully when a language has no parser available (log warning, skip file)
- Core languages first: Python, JavaScript, TypeScript, Go, Rust, Java

**Test scenarios:**
- U3-T1. Parse a Python file extracts classes, functions, and imports correctly
- U3-T2. Parse a TypeScript file extracts interfaces, types, and imports
- U3-T3. Symbol graph edges match actual import statements
- U3-T4. File with syntax errors is partially parsed without crashing
- U3-T5. Language detection by extension works for .py, .ts, .js, .go, .rs, .java
- U3-T6. Unknown language is skipped gracefully

---

### U4. LLM Architecture Interpreter

**Goal:** Take the AST symbol graph + file tree + README and produce a structured architecture interpretation — components, roles, and relationships. This is the core AI pipeline.

**Files:**
- `backend/app/services/llm_interpreter.py`
- `backend/app/services/validator.py`
- `backend/app/models/architecture.py` — `Architecture`, `Component`, `Relationship`, `ConfidenceLevel`
- `backend/app/prompts/architecture_prompt.txt` — the system prompt for architecture extraction
- `backend/tests/test_llm_interpreter.py`
- `backend/tests/test_validator.py`

**Details:**
- Stage 1: Build a compact repo summary (README summary, directory structure, key config files, top 20 most important files by centrality)
- Stage 2: Send to LLM with structured prompt asking for architecture as JSON
- Prompt constraints: every component path MUST exist in the file tree; output must be valid JSON matching a schema
- Stage 3: Validate output — every node path checked against the real file tree; any hallucinated path triggers a retry with corrected constraints (max 3 retries)
- Stage 4: Assign confidence levels to relationships: VERIFIED (import graph confirms edge), INFERRED (directory structure or naming suggests edge), UNVERIFIABLE (LLM guessed, no evidence)
- Return `Architecture` model with components, relationships, confidence scores

**Prompt design:**
```
You are an expert software architect analyzing a GitHub repository.
Given the file tree, README, and key source files below, produce a JSON architecture diagram.

Rules:
- Every component MUST have a "path" that exists in the file tree above
- Group related files into components (e.g., "src/auth/" → "Authentication Module")
- Describe the role of each component in 1-2 sentences
- Show relationships between components (depends_on, contains, communicates_with)
- Be conservative — only include relationships you have evidence for
```

**Test scenarios:**
- U4-T1. LLM produces valid JSON matching the required schema
- U4-T2. Every component path in output is validated against the actual file tree
- U4-T3. Hallucinated path is caught by validator, triggers retry
- U4-T4. After 3 failed retries, returns error gracefully
- U4-T5. Confidence levels are correctly assigned based on AST evidence
- U4-T6. Well-documented repo produces higher confidence scores than undocumented repo

---

### U5. Backend API Layer

**Goal:** FastAPI endpoints that connect the fetcher → AST extractor → LLM interpreter → validator pipeline and expose results via REST API + SSE.

**Files:**
- `backend/app/api/routes.py`
- `backend/app/api/schemas.py` — request/response Pydantic schemas
- `backend/app/main.py` — FastAPI app creation
- `backend/tests/test_api.py`

**Endpoints:**
- `POST /api/extract` — Accept `{repo_url: string}` or `{repo_urls: [string, string]}`, returns architecture(s) with streaming progress via SSE
- `GET /api/architecture/{id}` — Poll for completed architecture
- `GET /api/health` — Health check

**Details:**
- `/api/extract` creates a background task, returns immediately with `task_id`
- SSE endpoint `/api/extract/stream/{task_id}` streams progress events: `parsing`, `analyzing`, `validating`, `complete`, `error`
- Architecture result is cached in memory for the session
- CORS configured for frontend dev server

**Test scenarios:**
- U5-T1. POST to `/api/extract` with valid URL returns 202 and task_id
- U5-T2. SSE stream delivers all expected progress events
- U5-T3. Invalid URL returns 400 with validation message
- U5-T4. Health endpoint returns 200 with version info

---

### U6. Frontend Foundation

**Goal:** React + Vite + TypeScript app with routing, API client, and component library setup.

**Files:**
- `frontend/src/api/client.ts` — API client with fetch wrapper
- `frontend/src/types/architecture.ts` — TypeScript types matching backend models
- `frontend/src/App.tsx` — Main app with routing
- `frontend/src/pages/LandingPage.tsx` — URL input form
- `frontend/src/pages/ComparisonPage.tsx` — Canvas comparison view
- `frontend/src/components/LoadingState.tsx` — Progress bar during extraction
- `frontend/src/components/ErrorState.tsx` — Error display
- `frontend/tests/` — Vitest tests

**Details:**
- Landing page: two URL input fields + "Compare" button
- Loading state: SSE-driven progress bar showing extraction stage
- Error state: friendly error with retry option
- API client: typed fetch wrapper with error handling
- Routing: `/` (landing), `/compare/:id` (comparison view)

**Test scenarios:**
- U6-T1. Landing page renders with two URL inputs and a Compare button
- U6-T2. Clicking Compare with empty inputs shows validation error
- U6-T3. Loading state shows progress messages from SSE stream
- U6-T4. Error state renders friendly message with retry button
- U6-T5. API client calls backend and handles errors

---

### U7. Canvas — Architecture Rendering

**Goal:** Interactive side-by-side React Flow canvas that renders two architectures with custom node types, edges, minimap, and component detail panel.

**Files:**
- `frontend/src/canvas/ComparisonCanvas.tsx` — Main canvas with two React Flow instances side by side
- `frontend/src/canvas/ArchitectureGraph.tsx` — Single repo's architecture rendered as React Flow graph
- `frontend/src/canvas/nodes/ServiceNode.tsx` — Custom node for service/API components
- `frontend/src/canvas/nodes/StorageNode.tsx` — Custom node for databases/storage
- `frontend/src/canvas/nodes/QueueNode.tsx` — Custom node for message queues
- `frontend/src/canvas/nodes/CLINode.tsx` — Custom node for CLI/interface components
- `frontend/src/canvas/nodes/GenericNode.tsx` — Fallback node type
- `frontend/src/canvas/edges/ConfidenceEdge.tsx` — Custom edge with confidence color coding
- `frontend/src/canvas/minimap.tsx` — Minimap configuration
- `frontend/src/components/ComponentDetails.tsx` — Side panel showing component details
- `frontend/tests/test_canvas.tsx`

**Details:**
- ArchitectureGraph: receives `Architecture` data, creates React Flow nodes and edges
- Node positioning: layered layout algorithm (topological sort by dependency level)
- Custom node types visually distinguish: services (rounded rectangle), databases (cylinder icon), queues (hexagon), CLI (terminal icon)
- Edge colors: green (verified), yellow (inferred), red (unverifiable)
- Clicking a node opens ComponentDetails panel on the right
- ComponentDetails shows: component name, role description, file paths, confidence level, dependency list
- Minimap for navigation
- Two graphs rendered side by side in a flex container

**Test scenarios:**
- U7-T1. Architecture data renders as nodes and edges on the canvas
- U7-T2. Custom node types render with correct visual styling
- U7-T3. Edge confidence colors match the data (green/yellow/red)
- U7-T4. Clicking a node opens the details panel
- U7-T5. Minimap renders and is interactive
- U7-T6. Side-by-side layout renders both graphs without overlap

---

### U8. Canvas — Component Selection

**Goal:** Let users click components on either architecture to select/deselect them, building their own hybrid design. Selected state is visually distinct and exportable.

**Files:**
- `frontend/src/canvas/SelectionOverlay.tsx` — Selection state management
- `frontend/src/canvas/nodes/SelectedNode.tsx` — Selected node styling (highlighted border, checkmark)
- `frontend/src/components/SelectionSummary.tsx` — Panel showing selected components from both architectures
- `frontend/src/components/ExportButton.tsx` — Export selection as architecture decision record

**Details:**
- Click toggles selection state on a component
- Selected nodes get green highlight border + checkmark overlay
- SelectionSummary panel lists all selected components grouped by source repo
- User can remove selections from the summary panel
- Export produces a structured JSON summary: user description, selected components per source, rationale template
- Export format: JSON (default), with option to copy to clipboard

**Test scenarios:**
- U8-T1. Clicking a node toggles selection state visually
- U8-T2. Selected nodes appear in the SelectionSummary panel
- U8-T3. Removing a selection from the summary deselects the node
- U8-T4. Export produces valid JSON with all selected components
- U8-T5. Selecting a component on one side does not affect the other side

---

### U9. Repo Indexing Pipeline (v0.2)

**Goal:** Daily batch process that builds and refreshes a searchable index of top open-source repositories.

**Files:**
- `scripts/index_repos.py` — Daily batch indexing script
- `backend/app/services/indexer.py` — Index building and search
- `backend/app/models/index.py` — Index entry model
- `backend/tests/test_indexer.py`

**Details:**
- Fetch top repos by stars per topic from GitHub API (top 500 for each of ~50 topics)
- Index pipeline: fetch repo metadata + README → chunk README → generate embeddings → store in SQLite FTS5 + embedding column
- Embedding model: `text-embedding-3-small` (OpenAI) or local `all-MiniLM-L6-v2`
- Search: BM25 (FTS5) + cosine similarity (embeddings) merged via Reciprocal Rank Fusion
- LLM reranker: on user query, retrieve top 50 candidates, send to LLM for listwise reranking with quality signals
- Incremental refresh: only fetch repos updated since last index
- CLI endpoint: `/api/search?q=real-time+collaborative+editor` returns top repos with relevance scores

**Test scenarios:**
- U9-T1. Index script fetches and stores repos from GitHub API
- U9-T2. BM25 search returns relevant results for keyword query
- U9-T3. Embedding search returns relevant results for semantic query
- U9-T4. Hybrid search (BM25 + embeddings) outperforms either alone
- U9-T5. LLM reranker improves precision of top 3 results
- U9-T6. Incremental refresh only processes updated repos

---

### U10. Architecture Normalization (v0.3)

**Goal:** Map two independently-extracted architectures onto a shared component schema so the user sees "API Layer" for both repos, even if one calls it "handlers/" and the other "routes/".

**Files:**
- `backend/app/services/normalizer.py`
- `backend/app/models/normalized.py` — `SharedSchema`, `NormalizedArchitecture`
- `backend/tests/test_normalizer.py`

**Details:**
- LLM receives both architectures (component names, paths, roles) and produces a shared schema
- Shared schema entries: common architectural layers (API Layer, Data Layer, Auth Module, CLI, Core Logic, etc.)
- Each component from each repo is mapped to the appropriate shared layer
- User can override the mapping (drag a component to a different layer)
- Normalized view rendered on the canvas with shared layer labels spanning both graphs

**Test scenarios:**
- U10-T1. Two different architectures are merged into a shared schema
- U10-T2. Components from both repos map to correct shared layers
- U10-T3. User override persists and re-renders correctly
- U10-T4. Empty/unmatched components go to an "Other" category

---

## Verification Contract

### Test Commands

| Command | What it covers |
|---------|---------------|
| `pytest backend/tests/ -v` | All backend unit tests |
| `pytest backend/tests/ -v -k "ast"` | AST extraction tests (U3) |
| `pytest backend/tests/ -v -k "llm"` | LLM interpreter tests (U4) |
| `pytest backend/tests/ -v -k "api"` | API endpoint tests (U5) |
| `pytest backend/tests/ -v -k "fetcher"` | Fetcher tests (U2) |
| `pytest backend/tests/ -v -k "validator"` | Validator tests (U4) |
| `pytest backend/tests/ -k "normalizer"` | Normalizer tests (U10) |
| `pytest backend/tests/ -k "indexer"` | Indexer tests (U9) |
| `cd frontend && npx vitest run` | Frontend unit tests |
| `cd frontend && npx vitest run --coverage` | Frontend with coverage |
| `ruff check backend/` | Python linting |
| `cd frontend && npx tsc --noEmit` | TypeScript type checking |

### Quality Gates

- All backend tests pass before merging
- All frontend tests pass before merging
- TypeScript compiles with no errors
- Ruff linter passes with no errors
- No hallucinated paths in architecture output (validator must catch all)
- Test coverage >= 70% for extraction pipeline (U2 + U3 + U4)

---

## Definition of Done

### Phase 1 (v0.1) — Core Pipeline

- [ ] User can paste two GitHub URLs and get architectures rendered side-by-side
- [ ] AST extraction produces symbol graph for Python, JS/TS, Go, Rust, Java
- [ ] LLM interpreter produces component breakdown with confidence scores
- [ ] Validator catches hallucinated paths and rejects them
- [ ] React Flow canvas renders custom node types with edge colors
- [ ] Clicking a component shows its details in a side panel
- [ ] Components are selectable and summary panel shows selections
- [ ] SSE streams progress during extraction
- [ ] Unit tests for fetcher, AST extractor, interpreter, validator pass
- [ ] Frontend tests for rendering and interaction pass

### Phase 2 (v0.2) — Search & Discovery

- [ ] Index script runs daily and builds searchable repo database
- [ ] BM25 + embedding hybrid search returns relevant repos from plain-language query
- [ ] LLM reranker improves top-3 precision
- [ ] Search endpoint integrated into frontend as alternative to URL input
- [ ] Incremental refresh updates only changed repos

### Phase 3 (v0.3) — Normalization & Polish

- [ ] Two architectures can be normalized onto shared schema
- [ ] User can override normalization mappings
- [ ] Export produces structured decision record JSON
- [ ] Edge case handling for monorepos, undocumented repos, empty repos
- [ ] Error states for all failure modes (rate limited, LLM down, no matching repos)
