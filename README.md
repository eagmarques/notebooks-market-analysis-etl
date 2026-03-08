# 📊 Notebook Market ETL
An end-to-end Data Pipeline for competitive analysis of notebooks sold on Mercado Livre.

This portfolio project simulates a real-world consulting scenario: a company hiring a data team to evaluate the competitive landscape of the notebook market.

---

## 🎯 Business Context

A technology company needs to analyze the notebook category on Mercado Livre to understand:

- Competitor positioning
- Pricing distribution
- Brand dominance
- Seller behavior
- Customer perception (ratings & reviews)

To solve this business challenge, a complete data pipeline was developed — from data extraction to dashboard visualization.

---

## 🏗️ Architecture Overview

```text
Mercado Livre (Web)
        ↓
Web Scraping (Python/Scrapy)
        ↓
Local JSONL/SQL Database
        ↓
Transformation Layer (Python/Pandas)
        ↓
Analytical Dashboard (Streamlit)
```

---

## 🛠️ Setup & Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/eagmarques/notebooks-market-analysis-etl.git
    cd notebooks-market-analysis-etl
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv .venv
    # On Windows:
    .venv\Scripts\activate
    # On Linux/macOS:
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Environment Variables:**
    Create a `.env` file in the root directory and add your credentials (if applicable).

---

## 🚀 How to Run

### 1. Extraction (Scrapy)
To run the spider and collect data:
```bash
cd src/extraction/data_gathering
scrapy crawl notebook -o ../../../data/notebooks.jsonl
```

### 2. Transform & Load
To process the raw data:
```bash
python src/transformLoad/main.py
```

### 3. Dashboard
To launch the Streamlit dashboard:
```bash
streamlit run src/dashboard/app.py
```