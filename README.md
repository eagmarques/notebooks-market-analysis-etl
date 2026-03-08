# 📊 Notebook Market ETL

An end-to-end data pipeline for competitive analysis of the notebook market on Mercado Livre.

> This portfolio project simulates a real-world consulting scenario: a company hiring a data team to evaluate the competitive landscape of the Brazilian notebook market.

---

## 🎯 Business Context

A technology company needs to analyze the notebook category on Mercado Livre to understand:

- Competitor positioning and brand dominance
- Pricing distribution and discount trends
- Seller behaviour
- Customer perception (ratings & reviews)

---

## 🏗️ Architecture

```text
Mercado Livre (Web)
        ↓
[EXTRACT] Scrapy Spider → data/raw/notebooks_{timestamp}.jsonl
        ↓
[TRANSFORM] Pandas ETL  → data/analytics/mercadolivre.db
                          data/processed/notebooks.jsonl
        ↓
[LOAD] SQLite + Views    ← vw_brand_summary, vw_price_buckets, vw_top_sellers
        ↓
[DASHBOARD] Streamlit    ← src/dashboard/app.py
```

---

## 📁 Project Structure

```
notebook-market-analysis-etl/
├── config/
│   └── settings.yaml         # Central configuration (price range, table name, paths)
├── data/
│   ├── raw/                  # Raw JSONL files from Scrapy (one per crawl run)
│   ├── processed/            # Cleaned JSONL output from ETL
│   └── analytics/            # SQLite analytical database + SQL views
├── src/
│   ├── extraction/           # Scrapy project (data_gathering)
│   │   └── data_gathering/
│   │       ├── settings.py
│   │       └── spiders/
│   │           └── notebook.py
│   ├── transform/            # ETL transformation & loading
│   │   ├── main.py           # Pipeline orchestrator (logging + idempotency)
│   │   ├── normalizers.py    # Brand inference, sales bucket normalization
│   │   ├── cleaners.py       # Price & review string cleaning
│   │   └── loaders.py        # SQLite loader + SQL view creation
│   └── dashboard/            # Streamlit dashboard
│       ├── app.py            # UI orchestrator
│       ├── data_loader.py    # Data access, KPIs, insights
│       └── charts.py         # Plotly chart builders
├── tests/
│   ├── test_cleaners.py
│   └── test_normalizers.py
├── Makefile                  # Pipeline commands
├── requirements.txt
└── requirements-dev.txt
```

---

## 🛠️ Setup & Installation

```bash
git clone https://github.com/eagmarques/notebooks-market-analysis-etl.git
cd notebooks-market-analysis-etl

python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
pip install -r requirements-dev.txt  # for tests and linting
```

---

## 🚀 How to Run

### Option 1 — Using Make (recommended)

```bash
make extract      # Scrape Mercado Livre → data/raw/
make transform    # ETL: clean, deduplicate, load → data/analytics/
make dashboard    # Launch Streamlit dashboard
make test         # Run unit tests
make all          # extract + transform in sequence
```

### Option 2 — Manual (Module Execution)

Running scripts directly as files is not supported due to the package-based absolute imports (`src.transform...`). Use the following module executions:

#### 1. Extract
```bash
# De dentro da pasta raiz
scrapy crawl notebook --cwd src/extraction/data_gathering
# Ou simplesmente
cd src/extraction/data_gathering && scrapy crawl notebook
```

#### 2. Transform & Load
```bash
# Sempre da pasta raiz
python -m src.transform.main
```

#### 3. Dashboard
```bash
# Sempre da pasta raiz
streamlit run src/dashboard/app.py
```

---

## ⚙️ Configuration

Edit `config/settings.yaml` to adjust:

| Key | Default | Description |
|-----|---------|-------------|
| `etl.price_min` | 1000 | Minimum price filter (R$) |
| `etl.price_max` | 10000 | Maximum price filter (R$) |
| `etl.table_name` | notebooks | SQLite table name |
| `etl.db_filename` | mercadolivre.db | Database filename |

---

## 🧪 Running Tests

```bash
python -m pytest tests/ -v
```

---

## 💎 Data Quality Features (Senior Revamp)

This project was refactored to handle the complexities of real-world scraping:

- 🧠 **Robust Brand Inference**: Multi-layered brand detection (Raw HTML → Keyword Matching → Fallback to "Unknown"). Now recognizes specific lines like *Ideapad, Nitro, Alienware, ROG, Legion*.
- 🧹 **Noise Filtering**: Automatic exclusion of accessories (skins, chargers, cases, parts) using regex patterns to ensure the analytical database contains only valid notebooks.
- 🩹 **Price Healing**: Automatically detects and heals suspicious prices (e.g., installments or mis-scraped values < R$500) and ensures `old_money >= new_money`.
- ✅ **Advanced Deduplication**: Deduplicates based on a combination of `brand + name + seller + price`, ensuring same product offers from different vendors are preserved while duplicates are removed.
- 🚀 **Idempotent ETL**: Tracks processed raw files in a local manifest to avoid redundant processing.
- 📦 **Modern Package Architecture**: Uses absolute imports and standard project layout for maximum compatibility and scalability.