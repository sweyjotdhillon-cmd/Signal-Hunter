# 🎯 Signal Hunter

An AI-powered research intelligence pipeline designed to discover early tech opportunities, emerging engineering breakthroughs, startup concepts, and hidden scientific discoveries before they become mainstream.

---

## 📌 Mission

Most research summarization tools focus on condensing information. **Signal Hunter** is different. Its mission is to **detect signals of breakthrough potential**. 

It systematically monitors, crawls, and filters technical feeds to extract actionable insights, early-stage opportunities, and scientific breakthroughs. The output is a highly structured, prioritized **Daily Intelligence Report** curated for software engineers, research scientists, founders, and investors.

---

## 🧩 System Architecture

Signal Hunter is built on a clean, decoupled, event-ready modular pipeline. Below is the data flow topology:

```
[ External Sources ] (arXiv, Engineering Blogs, GitHub Trending)
        │
        ▼
┌────────────────────────┐
│  Collectors            │ (BaseCollector: Fetches raw Candidates)
└──────────┬─────────────┘
           │ (ResearchItem - raw)
           ▼
┌────────────────────────┐
│  Analyzers             │ (BaseAnalyzer: Cognitive AI Summary & Opportunity Extraction)
└──────────┬─────────────┘
           │ (ResearchItem - analyzed)
           ▼
┌────────────────────────┐
│  Signal Verifier       │ (SignalVerifier: Confirms thresholds, applies filters)
└──────────┬─────────────┘
           ├─────────────────────────┐
           │ (Verified)              │ (Unverified Noise)
           ▼                         ▼
┌────────────────────────┐     ┌───────────┐
│  Memory Storage        │     │  Filtered │ (Discarded or logged)
│  (JSON Store database) │     └───────────┘
└──────────┬─────────────┘
           │
           ▼
┌────────────────────────┐
│  Delivery Reporter     │ (BaseDelivery: Markdown briefings, notifications)
└────────────────────────┘
```

---

## 📂 Project Structure

```
signal-hunter/
├── config/                  # Configuration Schema and Loaders
│   ├── __init__.py
│   ├── config_loader.py     # Pydantic Configuration Model
│   └── settings.yaml        # Default pipeline settings
├── collectors/              # Raw data crawlers and feeds ingestors
│   ├── __init__.py
│   └── base.py              # BaseCollector abstract base class
├── analyzers/               # Cognitive processors and LLM extractors
│   ├── __init__.py
│   └── base.py              # BaseAnalyzer abstract base class
├── verifier/                # Validation and signal grading rules
│   ├── __init__.py
│   └── verifier.py          # SignalVerifier core class
├── memory/                  # Persistence and historic caches
│   ├── __init__.py
│   └── json_store.py        # JSON-based transactional persistence
├── delivery/                # Report compiles and publishers
│   ├── __init__.py
│   └── reporter.py          # MarkdownReporter delivery service
├── models/                  # Shared structured objects
│   ├── __init__.py
│   └── research_item.py     # ResearchItem data model (Pydantic)
├── utils/                   # Shared utility helpers
│   ├── __init__.py
│   ├── exceptions.py        # Pipeline custom error hierachy
│   ├── helpers.py           # Atomic JSON, hashing, text cleaners
│   └── logger.py            # Central logging config
├── tests/                   # Regression and unit test suite
│   ├── __init__.py
│   └── test_pipeline.py     # Component test assertions
├── main.py                  # Pipeline central entrypoint
├── requirements.txt         # Minimum external dependencies
└── README.md                # System documentation
```

---

## 🚀 Installation & Setup

### Requirements
- **Python 3.12+**
- No external heavy databases required (persistence is fully JSON-based out-of-the-box).

### 1. Clone & Environment Set Up
```bash
git clone https://github.com/yourusername/signal-hunter.git
cd signal-hunter
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Local Configuration Override (Optional)
If you wish to override standard settings without altering tracked files, create a file named `config/local_settings.yaml`. It is automatically prioritized and merged by the loader:
```yaml
# config/local_settings.yaml
log_level: "DEBUG"
verifier:
  min_confidence_score: 0.85
```

---

## 📱 Running on Android (via Termux)

Signal Hunter is fully optimized to run efficiently inside **Termux** on Android devices, making it perfect for off-grid edge execution or daily mobile briefings.

### Termux Setup Instructions:
1. **Install Termux** from F-Droid (avoid Google Play as it's outdated).
2. **Bootstrap Packages & Python**:
   ```bash
   pkg update && pkg upgrade -y
   pkg install python python-pip git libyaml -y
   ```
3. **Setup Filesystem Storage**:
   ```bash
   termux-setup-storage
   ```
4. **Install Signal Hunter**:
   ```bash
   git clone https://github.com/yourusername/signal-hunter.git
   cd signal-hunter
   pip install -r requirements.txt
   ```
5. **Run the Pipeline**:
   ```bash
   python main.py --dry-run
   ```

---

## ⚙️ Usage & CLI Arguments

Execute the central coordinator using the standard Python interpreter:

```bash
# Execute standard run with mock/demo feed crawlers
python main.py --dry-run

# Run using a custom configuration file path
python main.py --config config/local_settings.yaml
```

The run triggers a full cycle:
1. Loads settings from `config/settings.yaml`.
2. Sets up logging in console stdout and writes records to `logs/signal_hunter.log`.
3. Simulates/gathers breakthrough indicators.
4. enriches records with summaries and opportunities using active Analyzers.
5. Filters results against confidence scores inside `SignalVerifier`.
6. Commits verified results to `data/items/{item_id}.json`.
7. Compiles and publishes the Markdown Briefing under `reports/daily_intelligence_brief_{date}.md`.

---

## 🧪 Testing

Execute the test suite using Python's standard discovery runner:

```bash
python -m unittest discover -s tests
```

---

## 🔌 Extensibility: How to Add a Collector

Adding a new collector (e.g. Substack, HackerNews, or custom API) is extremely straightforward:

1. Create a file inside `collectors/` (e.g., `collectors/hn_collector.py`).
2. Implement a class inheriting from `BaseCollector`:
   ```python
   from typing import List
   from collectors.base import BaseCollector
   from models.research_item import ResearchItem
   from utils.helpers import generate_id
   from utils.exceptions import CollectionError

   class HackerNewsCollector(BaseCollector):
       @property
       def name(self) -> str:
           return "HackerNews"

       def collect(self) -> List[ResearchItem]:
           self.logger.info("Starting HackerNews crawl...")
           results = []
           try:
               # Fetch API content...
               # Parse and instantiate ResearchItems
               item = ResearchItem(
                   id=generate_id("https://news.ycombinator.com/item?id=123"),
                   title="Show HN: A new compiler in Rust",
                   url="https://news.ycombinator.com/item?id=123",
                   source_type="engineering_blog",
                   raw_content="Show HN description text...",
               )
               results.append(item)
           except Exception as e:
               raise CollectionError(self.name, f"Request failed: {e}")
           
           return results
   ```
3. Register the collector in `config/settings.yaml` and initialize it inside `main.py`'s runtime loop.
