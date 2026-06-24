# Vibe_arch

**Stop vibe-coding. Build the architecture yourself — with real open-source patterns as your standard of truth.**

Vibe_arch inverts the AI-coding paradigm: the AI does *not* hand you an architecture.
It discovers two top-tier open-source repos that solve your problem, animates their
blueprints side-by-side, and forces you to actively choose between them component by
component. What you build is *yours* — and it's grounded in how real engineers
actually ship.

> **Architecture is spatial.** This tool never outputs text diagrams, Markdown, or
> Mermaid. The UX is a highly interactive, node-based visual canvas
> ([React Flow](https://reactflow.dev/)) in the browser.

## The flow

1. **CLI interrogation** — You type your idea. If it's vague, the CLI asks
   scale/constraint questions so a personal project never gets a production-grade
   architecture (and vice versa).
2. **Smart discovery** — The backend finds two high-quality OS repos solving the same
   problem, ranked by *engineering quality* (not raw stars): maintenance, trusted
   ownership, bus factor, release cadence, tests, CI, architecture cleanliness.
3. **Visual diff** — A dark UI opens with three React Flow canvases. The left and right
   canvases **animate drawing** the two repos' blueprints like a time-lapse.
4. **Active decision gates** — Where both repos did something the same way, it's
   assumed standard practice and auto-added to the center. Where they differ
   critically (e.g. message queue vs. direct DB), the UI **freezes** and a panel
   slides up explaining the trade-off. You must accept or reject before the chosen
   node drops into your center canvas.
5. **Final map** — Left/right repos fade away. The center canvas is your polished
   architecture map. Hovering any node shows *why* it's there and *what was rejected*.
6. **Exports** — Three buttons: export the diagram as PDF/Image, scaffold the base
   project folder structure, and generate a strict `archguard.json` that constrains
   future AI coding agents from breaking the design.

## Tech stack

| Component | Tech |
|-----------|------|
| Backend   | Python · FastAPI · `httpx` (managed with [`uv`](https://docs.astral.sh/uv/)) |
| CLI       | Python · Typer (managed with `uv`) |
| Frontend  | TypeScript · React · Vite · `@xyflow/react` · `elkjs` |
| LLM       | GLM 5.2 (Zhipu) default; Gemini / Groq configurable |

## Quick start

```bash
# 1. Python deps (backend + CLI) via uv
uv sync

# 2. Frontend deps
cd frontend && npm install && cd ..

# 3. Configure secrets
cp .env.example .env   # then fill in GITHUB_TOKEN + LLM key

# 4. One-command launch (starts backend, opens the browser UI)
uv run python -m vibe_arch "a real-time collaborative whiteboard app"
```

See [AGENTS.md](./AGENTS.md) for the full developer guide, commands, and conventions.

## Status

MVP — under active development.
