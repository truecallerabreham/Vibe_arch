# Vibe_Arch — Comprehensive Feasibility Research Report

**Date:** June 26, 2026
**Scope:** Full-spectrum feasibility analysis for a tool that extracts, renders, and compares open-source project architectures on an interactive visual canvas.

---

## A) Existing Similar Tools

### A.1 — Architecture Extraction from GitHub Repos

| Tool | Description | Stars | Architecture |
|------|-------------|-------|-------------|
| **[GitDiagram](https://gitdiagram.com/)** ([repo](https://github.com/ahmedkhaleel2004/gitdiagram)) | Converts any GitHub repo into an interactive Mermaid.js architecture diagram. Two-stage AI pipeline: plain-English explanation → structured graph → validated against file tree. | 15.7k | Next.js + FastAPI + Cloudflare R2 + GPT-5/Claude |
| **[Gitvize](https://gitvize.com/)** | AI-powered interactive architecture diagrams, file trees, contributor networks. | — | Proprietary |
| **[RepoMapr](https://repomapr.com/)** | AI-generated interactive repo maps with clickable nodes and AI chat. | — | Proprietary |
| **[CodeBoarding](https://github.com/CodeBoarding/CodeBoarding)** | Combines static analysis + LLM reasoning to generate architecture diagrams, component docs inside IDE/CI. Supports 8 languages. | — | Python, VSCode extension |
| **[Eraser DiagramGPT](https://www.eraser.io/git-diagrammer)** | Generate architecture/sequence/ER diagrams from git repos via prompts. DSL-based editing. | — | Proprietary (OpenAI) |
| **[code2flow](https://github.com/scottrogowski/code2flow)** (classic) | Static call graph generation via AST parsing. Python/JS/Ruby/PHP. No LLM involved. Deterministic. | 2.8k | AST-based, deterministic |
| **[GitBuster](https://gitbuster.com/)** | Analyze any GitHub repo with AI — chat with the codebase. | — | Proprietary |
| **[ExplainGitHub](https://explaingithub.com/)** | Chat with any GitHub repo. Architecture explanations, PR summaries, CI failure analysis. | — | Proprietary API |
| **[CodeGraph](https://github.com/colbymchenry/codegraph)** | Pre-indexed code knowledge graph using tree-sitter AST extraction + SQLite + MCP server. ~58% fewer tool calls for agents. | — | tree-sitter AST → SQLite FTS5 |

### A.2 — Side-by-Side Comparison Tools

**No tool currently does side-by-side architecture comparison of two open-source projects.**

The closest approximations:
- **[repo-analyzer](https://pypi.org/project/repo-analyzer)** (PyPI) — CLI tool with `repo-analyzer compare <url1> <url2>` — compares health metrics, not architecture.
- **[OpenApps](https://openapps.sh/compare/)** — Side-by-side feature comparison of open-source apps (feature tables, not architecture).
- **IcePanel / Structurizr / Archi** — C4 modeling tools where you *manually* build models; no auto-extraction from repos.

**Key gap identified:** No existing tool extracts architecture from *two* repos and lays them out side-by-side for component-level comparison. This is an open space.

### A.3 — Repo Ingestion for LLM Context

| Tool | Function |
|------|----------|
| **[Repomix](https://repomix.com/)** (23.1k stars) | Packs entire repo into a single AI-friendly file (XML/MD/JSON/Plain). Tree-sitter code compression. Secretlint security. |
| **[Gitingest](https://gitingest.com/)** | Turn any git repo into a prompt-friendly text digest for LLMs. Replace `hub` with `ingest` in URL. |

These are foundational for vibe_arch — they solve the "how do I get the codebase into the LLM's context window" problem.

---

## B) Technical Feasibility of Architecture Extraction from Repos

### B.1 — Current State of LLM Code Understanding

**Very strong and improving rapidly.** Key evidence:

- **GitDiagram** (15.7k stars, since Dec 2024) already proves the core concept works: extract file tree → LLM generates architecture explanation → converts to Mermaid diagram.
- **Claude Fable 5 / GPT-5.5** now score 59-63% on Terminal-Bench Hard (complex coding tasks). Coding benchmarks improve ~20-30% YoY.
- **SWE-Adept** ([arXiv 2603.01327](https://arxiv.org/abs/2603.01327), 2026) — LLM agents now do deep codebase analysis with structured issue resolution.
- **ArchAgent** ([arXiv 2601.13007](https://arxiv.org/html/2601.13007v1), 2026) — specifically tackles *legacy software architecture recovery* using LLMs. Achieves statistically significant accuracy improvements when including dependency context (p < 0.001).

### B.2 — Systematic Literature Review

A **2025 Systematic Literature Review** ([arXiv 2505.16697](https://arxiv.org/html/2505.16697)) on "Software Architecture Meets LLMs" analyzed 18 research articles and found:

> *"LLMs are increasingly applied to a variety of software architecture tasks and often outperform baselines… areas such as generating source code from architectural design, cloud-native computing and architecture, and checking conformance remain underexplored."*

Key findings: LLMs are used for classification of design decisions, detection of design patterns, and generation of software architecture design from requirements. Most approaches still use simple prompting, but advanced techniques are emerging.

### B.3 — The Accuracy Problem

**Hallucination rates by domain** (source: Lakera AI, 2026):
- Well-known entities: 3-5% hallucination
- Niche technical domains: 15-30%
- Medical/legal: 10-20%

For *architecture extraction*, the risk profile is moderate — hallucinated components are verifiable against actual file trees.

**Mitigation strategies applicable to vibe_arch:**
1. **Validation against file tree** — GitDiagram already does this (diagram is checked against actual repo paths before rendering)
2. **RAG with AST-derived graphs** — CodeGraph proves tree-sitter graphs produce clean, non-hallucinated symbol relationships
3. **Structured prompting with multi-stage pipeline** — GitDiagram's 2-stage approach (explain → diagram → validate) is a proven pattern
4. **Self-consistency checks** — Generate multiple architecture interpretations and vote

### B.4 — Architecture Extraction Approaches (Ranked by Reliability)

1. **AST-based static analysis** (code2flow, CodeGraph) — **Most reliable**, deterministic. Extracts call graphs, imports, class hierarchies. No hallucination. Limited to syntactic relationships.
2. **LLM-pipeline with validation** (GitDiagram approach) — **Good for semantic understanding**. Cross-checks against real paths. Hallucination risk on inferred relationships.
3. **Pure LLM extraction** — **Riskier**. No ground truth validation. Hallucination of non-existent modules.
4. **Hybrid: AST graph → LLM enhancement** — **Best of both**. Extract real symbols/edges via AST, then use LLM to describe architecture *in terms of* the known graph.

### B.5 — Multi-Language Support

- **CodeGraph** supports: Python, JS/TS, Java, Go, Rust, C, C++, Ruby, PHP, C#, Swift, Kotlin, Scala (via tree-sitter grammars)
- **code2flow** supports: Python, JavaScript, Ruby, PHP
- **CodeBoarding** supports: Python, JS/TS, Java, Go, Rust, PHP, C#

Tree-sitter has parsers for **100+ languages**, making broad multi-language support feasible.

---

## C) Visual Canvas / Interactive Diagram Tools

### C.1 — Library Landscape

| Library | Stars | Best For | Notes |
|---------|-------|----------|-------|
| **[React Flow](https://reactflow.dev/)** (xyflow) | 37.3k | Node-based editors, architecture diagrams | Custom React component nodes, pan/zoom/minimap, TypeScript, MIT license |
| **[tldraw](https://tldraw.dev/)** | 48.1k | Whiteboarding, freeform canvas, infinite canvas SDK | Shapes, tools, multiplayer, persistence, React SDK |
| **[Excalidraw](https://excalidraw.com/)** | 125.9k | Hand-drawn style diagrams | Real-time collaboration, open source, MIT |
| **[Mermaid](https://github.com/mermaid-js/mermaid)** | 75k+ | Text-to-diagram (not interactive canvas) | Great for export/embed, not interactive node manipulation |
| **[Strudel Flow](https://xyflow.com/strudel-flow)** (new) | — | Merges React Flow + tldraw | Structured nodes + freeform whiteboard in one canvas |
| **[Diagrams.net](https://www.diagrams.net/)** (draw.io) | — | Traditional drag-and-drop diagramming | Free, open source, desktop + web |

### C.2 — Recommended Approach: React Flow + tldraw Hybrid

React Flow is the **clear winner** for structured architecture diagrams because:
- Every node is a React component
- Pan/zoom/selection/keyboard shortcuts built-in
- TypeScript support is excellent
- 9.73M weekly npm installs
- Proven in production at Stripe, Typeform, Zapier

tldraw is better for the *freeform brainstorming/annotation layer*.

**Strudel Flow** (2025) explicitly combines both — React Flow for precise node diagrams + tldraw for collaborative whiteboarding. This is the ideal foundation for vibe_arch.

### C.3 — Building an Interactive Architecture Canvas

A detailed technical walkthrough ("Building an Interactive Architecture Canvas with React Flow," March 2026) by a solo developer who built a production canvas with 8 custom node types reports:

> *React Flow made it possible without building a rendering engine from scratch. Every node is a React component — full access to hooks, state, context.*

Key implementation considerations:
- Custom node types for different architecture components (services, databases, APIs, queues)
- Edge routing for complex dependency graphs
- Minimap for large-scale navigation
- Side panel for component details

---

## D) Market / User Research

### D.1 — The "Vibe Coding" Phenomenon

- **Term coined** by Andrej Karpathy (Feb 2025). **Collins Word of the Year 2025**.
- **92% of US developers** have adopted AI-assisted coding practices (2026).
- **60% of all new code** in 2026 is AI-generated.
- **25% of YC Winter 2025 cohort** had codebases that were **95%+ AI-generated**.
- **Global AI coding market: $8.5B** (2026).
- **Lovable AI** reached $100M ARR in 8 months.

### D.2 — The Counter-Movement ("Architecture First")

A growing counter-narrative: *"Vibe coding creates a mess; we need architecture-first tools."*

- **Vibe Kanban** (YC S21) — "Plan and review AI generated code." Integrates with Claude Code and Codex. Explicitly addresses the "plan + review" gap.
- **"AI Coding Tools Architecture-First Guide 2026"** (zoer.ai) — dedicated guide on architecture-first approaches.
- The "architecture-first" philosophy is gaining traction precisely *because* vibe coding produces code without structural oversight.

### D.3 — YC/Startup Activity in This Space

| Startup | Batch | Focus |
|---------|-------|-------|
| **[Vibe](https://www.ycombinator.com/companies/vibe)** (vibe.codes) | S24 | Everyone a software engineer — conversational app building |
| **[Vibe Kanban](https://www.workatastartup.com/companies/24616)** | S21 | Plan and review AI-generated code |
| **Bitrig** | S25 | Vibe coding in Swift for iOS apps |
| **Floot** | S25 | Web app builder with 14k users |
| **Okibi** | S25 | AI coding tool |

**No YC startup is specifically focused on architecture extraction + comparison.** This remains an open space.

### D.4 — What Engineers Currently Use for System Design

From Cerbos (2025) and IcePanel (2025) surveys of software architects:

| Tool | Type | Usage |
|------|------|-------|
| **Mermaid** | Diagram-as-code | Very high — embedded in docs, PRs |
| **Diagrams.net** | Drag-and-drop | High — free, universal |
| **Excalidraw** | Whiteboarding | High — quick sketches |
| **PlantUML** | Diagram-as-code | Moderate — legacy |
| **Structurizr** | C4 model-as-code | Growing — architecture modeling |
| **Archi** | ArchiMate modeling | Enterprise architects |
| **IcePanel** | C4 modeling SaaS | Growing — agile teams |

**The pain point:** None of these auto-extract from code. Engineers manually create and maintain architecture diagrams, which immediately become stale.

---

## E) Key Challenges and Risks

### E.1 — Architecture Extraction Reliability

| Challenge | Severity | Mitigation |
|-----------|----------|------------|
| Repos with minimal documentation | **High** | Combine README analysis + AST scanning + file naming heuristics |
| Monorepos with multiple projects | **Medium** | Detect project boundaries via package.json, Cargo.toml, etc. |
| Multi-language repos | **Medium** | Tree-sitter supports 100+ languages; per-language extractors |
| Deeply nested/huge repos | **Medium** | Prioritize by centrality; offer "focus mode" on subdirectories |
| Non-standard project structures | **Medium** | LLMs handle arbitrary structures better than rigid parsers |
| False positives / hallucinated components | **High** | **Must validate every node against actual file tree** (GitDiagram pattern) |
| Spaghetti / untestable architectures | **Low** | The tool should surface this honestly — it's a feature, not a bug |

### E.2 — The Validation Loop (Critical Architecture Decision)

The single most important finding from GitDiagram's success: **validation against the real file tree eliminates hallucinated paths**.

For vibe_arch, the pipeline should be:
1. Fetch file tree + README (via GitHub API)
2. Feed into LLM with structured prompt: "Explain this repo's architecture"
3. Extract components as structured data (JSON nodes + edges)
4. Validate every node path exists in the real file tree
5. Only then render the diagram
6. If validation fails → retry with corrected constraints

### E.3 — Scaling: Large Repo Processing

- **GitDiagram** uses Cloudflare R2 for diagram caching + Upstash Redis for quotas
- **CodeGraph** achieves fast queries by building a SQLite symbol database with FTS5 full-text search
- **Repomix** uses tree-sitter code compression to reduce token count by ~70%
- **Critical insight:** Don't process the *entire* repo. Focus on: README, directory structure, key config files, and a representative sample of source files.

### E.4 — Multi-Model Comparison (The Core Differentiator)

The comparison feature introduces unique challenges:
1. **Normalization problem** — Two repos solving the same problem may use completely different terminology, naming, and structure
2. **Abstraction level mismatch** — One may be a library, another a full framework
3. **Granularity mismatch** — Different levels of decomposition

**Approach:** Use LLM to normalize both architectures into a shared schema (e.g., "API layer," "data layer," "auth module," "CLI interface"). Then map each repo's components onto this shared schema for side-by-side display.

### E.5 — LLM Hallucination Risk Management

Recent research (2025-2026) shows effective mitigation strategies:

- **RAG with verified sources** — Sage (Storia AI) achieves high accuracy by forcing LLM to base answers on retrieved code
- **SelfCheckGPT** — Zero-resource black-box hallucination detection
- **Multi-agent debate** — Have two LLM instances produce architectures and reconcile differences
- **Confidence calibration** — New reward schemes penalize overconfidence; models can signal uncertainty

**For vibe_arch, the recommended approach:**
- Use deterministic AST extraction for *facts* (files, classes, functions, imports)
- Use LLM only for *interpretation* (what does this module do? how do these parts relate?)
- Always enable user override — let engineers correct the AI
- Show confidence scores on inferred relationships

---

## F) Synthesis: Opportunity Assessment

### F.1 — Why This Is Feasible Now

1. **GitDiagram (15.7k stars) proves single-repo extraction works** at production scale
2. **LLM coding benchmarks improve 20-30%/year** — quality trajectory is steep
3. **ArchAgent research paper** (2026) validates architecture recovery with statistical significance
4. **React Flow + tldraw** provides battle-tested canvas infrastructure
5. **tree-sitter** enables multi-language AST extraction for 100+ languages
6. **Repomix/Gitingest** solve the ingestion problem
7. **No competitor does side-by-side architecture comparison** — open white space

### F.2 — Core Value Proposition

> *"Stop guessing which open-source project fits your needs. See their architectures side-by-side. Choose each component deliberately."*

### F.3 — Recommended MVP Architecture

```
User Input: "I want to build a <description>"
    ↓
GitHub Search for 2 top OSS projects
    ↓
Repomix-style ingestion of both repos
    ↓
tree-sitter AST extraction (deterministic facts)
    ↓
LLM architecture interpretation (with validation)
    ↓
Normalize both into shared component schema
    ↓
Side-by-side React Flow canvas rendering
    ↓
User selects component-by-component
    ↓
Export as architecture decision record
```

### F.4 — Key Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| LLM hallucinates components | High | Medium | File-tree validation gate |
| Users don't trust AI architecture | Medium | Medium | Show confidence, enable manual edit |
| Large repos overwhelm context window | Medium | Medium | Prioritize, compress, cache |
| Comparison normalization is hard | High | Medium | LLM-driven normalization with UI correction |
| Competition catches up | Medium | Low | First-mover in comparison UX |

---

## G) Sources & References

1. GitDiagram — https://github.com/ahmedkhaleel2004/gitdiagram
2. Gitvize — https://gitvize.com/
3. RepoMapr — https://repomapr.com/
4. CodeBoarding — https://github.com/CodeBoarding/CodeBoarding
5. Eraser DiagramGPT — https://www.eraser.io/git-diagrammer
6. code2flow — https://github.com/scottrogowski/code2flow
7. CodeGraph — https://github.com/colbymchenry/codegraph
8. Repomix — https://repomix.com/ (23.1k stars)
9. Gitingest — https://gitingest.com/
10. ExplainGitHub — https://explaingithub.com/
11. ArchAgent paper — https://arxiv.org/html/2601.13007v1 (2026)
12. Software Architecture Meets LLMs SLR — https://arxiv.org/html/2505.16697 (2025)
13. SWE-Adept paper — https://arxiv.org/abs/2603.01327 (2026)
14. React Flow — https://reactflow.dev/ (37.3k stars)
15. tldraw — https://tldraw.dev/ (48.1k stars)
16. Excalidraw — https://excalidraw.com/ (125.9k stars)
17. Strudel Flow — https://xyflow.com/strudel-flow
18. Archi — https://www.archimatetool.com/
19. C4 Model — https://c4model.com/
20. C4 Model Tools — https://c4model.tools/
21. Building an Interactive Canvas with React Flow — https://mosharif.me/blog/react-flow-interactive-canvas (2026)
22. YC Vibe Coding coverage — Business Insider, Sept 2025
23. Vibe Kanban (YC S21) — https://www.workatastartup.com/companies/24616
24. Vibe (YC S24) — https://vibe.codes
25. JP Morgan "Vibe Coding Guide" — Nov 2025
26. LLM Hallucination Survey — https://arxiv.org/html/2510.06265v1 (2025)
27. Lakera AI Hallucination Guide — https://www.lakera.ai/blog/guide-to-hallucinations-in-large-language-models
28. repo-analyzer (compare feature) — https://pypi.org/project/repo-analyzer
29. IcePanel Top 9 Architecture Tools — https://icepanel.io/blog/2025-08-26-top-9-software-architecture-tools
30. Cerbos "Best Open Source Tools for Architects" — https://www.cerbos.dev/blog/best-open-source-tools-software-architects
31. Best LLM for Coding 2026 — https://whatllm.org/best-llm-for-coding
32. Vibe Coding Developer Guide — https://lushbinary.com/blog/vibe-coding-developer-guide-ai-first-development (2026)
33. Top Vibe Coding Tools 2025 — https://www.greengeeks.com/blog/best-vibe-coding-tools/
