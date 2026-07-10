# 🛡️ Signal Hunter: Repository Audit & Consolidation Report

This document outlines the detailed architectural audit of the Signal Hunter repository, identifying structural defects, legacy debt, duplicate components, and detailing the consolidation actions taken to establish a single source of truth.

---

## 🔎 Repository Structural Audit

### 1. Duplicate & Overlapping Modules
*   **Defect**: The codebase had a complete functional split and duplication of memory persistence engines between `/backend/memory/json_store.py` and `/backend/knowledge_base/json_store.py`. Both contained similar implementations of `JSONMemoryStore`.
*   **Impact**: Any fixes to JSON serialization (like handling datetime fields or deep model dumps) implemented in one store would not carry over to the other, creating subtle runtime divergence.
*   **Resolution**: Deleted `/backend/memory` entirely. Unified all memory storage operations on `/signal-hunter/knowledge_base/json_store.py`, which is the superior implementation utilizing robust datetime conversions and safe JSON writing functions.

### 2. Ambiguous Directory Naming
*   **Defect**: The main codebase structure used `/backend/`, whereas the architectural specification demanded a singular `/signal-hunter/` folder namespace.
*   **Impact**: Led to developer confusion and inconsistent module/import tracking.
*   **Resolution**: Renamed `/backend` to `/signal-hunter`. All Python imports now resolve relative to the `signal-hunter/` path inside `sys.path`.

### 3. Entry Points & Invocation Slop
*   **Defect**: Confusing or overlapping developer run scripts in package configurations.
*   **Impact**: Potential to trigger old code paths or run outdated scripts.
*   **Resolution**: Hardened the `/main.py` entry point at the root to insert `signal-hunter/` into the system path and execute the centralized CLI manager.

### 4. Configuration and Environment Loaders
*   **Defect**: Environmental variables (like `NVIDIA_API_KEY`, `BOT_TOKEN`) could be referenced or defined across multiple places.
*   **Impact**: Fragile configurations and risk of secret exposure.
*   **Resolution**: Standardized on `.env.example` as the single source of environment definitions. Pydantic-based `AppConfig` strongly types all properties parsed from `/signal-hunter/config/settings.yaml`, lazily resolving secrets on demand.

### 5. Dead Code & Build Artifacts
*   **Defect**: Residual `.pyc` and `__pycache__` directories in the workspace.
*   **Impact**: Dirty git trees and cache pollution.
*   **Resolution**: Cleaned up all pycache directories. Configured `.gitignore` to prevent any future tracking of compiled assets.

---

## 📐 Canonical Codebase Blueprint

```
/
├── main.py                    # Unified Backend CLI Entry point
├── server.ts                  # Full-stack API & Asset Server Entry point
├── package.json               # Developer scripts and Node dependencies
├── vite.config.ts             # React build and pipeline asset configuration
├── metadata.json              # Platform capabilities and application metadata
├── reports/                   # Output target folder for Daily Briefings
├── data/                      # Local Knowledge Base store database
│   ├── items/*.json           # Saved Canonical ResearchItems
│   └── kb/*.json              # Semantic Indices & Graph Node State
├── signal-hunter/             # The SINGLE Backend Package Namespace
│   ├── main.py                # Main Python controller logic
│   ├── models/                # Unified data models (ResearchItem, etc.)
│   ├── config/                # Strongly-typed configuration system
│   ├── knowledge_base/        # Persistent semantic indexing & relationship graphs
│   ├── collectors/            # Dynamic source registry adapters (arXiv, etc.)
│   ├── normalizer/            # Inbound signal normalizers
│   ├── verifier/              # Decoupled verifiers & quality gates
│   ├── deduplicator/          # Duplicate item resolution
│   ├── scorer/                # Strategic capability evaluation scoring
│   ├── analyzers/             # LLM opportunity acceleration analysis
│   ├── delivery/              # Multi-channel publishers (Markdown, Telegram)
│   └── tests/                 # 47-file comprehensive unit test suite
└── frontend/                  # React Frontend Application
    └── src/                   # Layouts, Views, & Visualizers
```
