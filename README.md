# 🏹 Signal Hunter: Opportunity & Signal Intelligence Engine

Signal Hunter is an offline-first, pipeline-driven opportunity intelligence and signal monitoring platform. It is engineered to automatically ingest raw academic and technical data, filter out noise, resolve duplicate entries, score signals against strategic trust vectors, enrich them using advanced AI models, and build long-term trend intelligence.

---

## 🎨 System Architecture Overview

Signal Hunter utilizes a clean, decoupled monorepo architecture divided into a React frontend and a Python pipeline backend:

```
├── frontend/             # React (Vite, Tailwind, Lucide Icons) dashboard application
│   ├── src/              # App components, visualizations, and static asset code data
│   └── index.html        # Entry page
├── signal-hunter/        # The SINGLE consolidated Python processing pipeline and intelligence engine
│   ├── collectors/       # Dynamic collectors registry and data ingestion adapters
│   ├── analyzers/        # AI enrichment engines (Gemini and NVIDIA LLM providers)
│   ├── verifier/         # Confidence checking, quality validation, and strict mode gating
│   ├── normalizer/       # Input sanitation, date alignment, and field validation
│   ├── deduplicator/     # Semantic title/URL deduplication algorithms
│   ├── scorer/           # Strategic opportunity scoring logic
│   ├── knowledge_base/   # Compact JSON-graph database with 6-month auto-compression
│   ├── trend_engine/     # Research trend tracking and breakthrough detection
│   └── tests/            # High-coverage Python unit test suite
├── main.py               # Root Python CLI Entrypoint (orchestration gateway)
├── server.ts             # Backend-for-Frontend server proxying API endpoints & serving web assets
├── package.json          # Root configuration for building and running the Vite frontend + server
└── vite.config.ts        # Vite configuration supporting sub-directory project roots
```

---

## 🚀 Key Architectural Improvements

This platform has undergone a professional architectural refactor to guarantee maximum stability, modularity, and scalability:

1. **Clean Directory Separation**: Segregated frontend elements completely into `frontend/` and backend assets into `signal-hunter/` to prevent directory coupling.
2. **Eliminated Module Duplication**: Safely removed redundant implementations like `backend/memory`, unifying all memory storage engines onto the robust, JSON-serializable `signal-hunter/knowledge_base/json_store.py`.
3. **Centralized Configuration**: Upgraded system parameters using strongly-typed Pydantic schemas in `signal-hunter/config/config_loader.py`. Fully supports Tracked Topics, Collector Weights, Enabled Sources, NVIDIA Models, Time Windows, Retry limits, Telegram bindings, and Knowledge Base compression parameters.
4. **Decoupled SourceRegistry**: Replaced hardcoded pipelines with a dynamic registration engine. Enables on-the-fly registration, custom weighting, and priority sorting for academic, social, and developer signal sources.
5. **Knowledge Base Relationship Graph**: Fully integrated `enabled_by_technology` edge relationship mappings between raw opportunities and emerging technological categories to support trend clustering.
6. **No-Flicker Visual Dashboard**: Built a gorgeous, responsive, and fluid client-side dashboard with clean Inter typography, JetBrains Mono data monitors, dynamic chart pipelines, and detailed card dialogs.

---

## 🛠️ Installation & Execution

### 1. Full-Stack Development Server

To run the unified Node.js/TypeScript server which automatically compiles and serves the React frontend alongside backend API execution endpoints:

```bash
# Install dependencies
npm install

# Start the development server (Binds to http://localhost:3000)
npm run dev

# Build for production (Produces compiled assets under /dist)
npm run build
```

### 2. Consolidated Backend CLI

To execute the Python pipeline CLI orchestration helper directly:

```bash
# Get status information on the stored knowledge base and configurations
python3 main.py --status

# Trigger a manual execution of the pipeline collectors and AI analyzers
python3 main.py --run
```

### 3. Backend Test Suite

To execute the Python pipeline unit tests:

```bash
# Run the complete unit test suite with PYTHONPATH mapped
PYTHONPATH=signal-hunter python3 -m unittest discover -s signal-hunter/tests
```

All 47 tests run completely offline and mock external APIs to ensure zero-friction execution.

---

## 📊 Pipeline Processing Stages

1. **CollectorStage**: Ingests raw publications or code repositories from registered adapters via `SourceRegistry`.
2. **NormalizerStage**: Cleans input strings, strips padding, and aligns timezones.
3. **VerifierStage**: Evaluates signals against minimum confidence thresholds.
4. **DeduplicatorStage**: Performs cross-reference grouping based on matching titles or URLs.
5. **ScorerStage**: Computes viability, strategic fit, and technical scores.
6. **AIAnalyzerStage**: Enhances signals with LLM summaries, key-phrase tags, and category classifications.
7. **KnowledgeBaseStage**: Saves records to compact local JSON files with automated monthly archival rules.
8. **ReporterStage**: Emits briefings and technical trend reports.
