"""
main.py — ETL Orchestrator
Reads raw JSONL files → transforms data → loads to SQLite + JSONL.
"""
from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml

from src.transform.cleaners import clean_prices, clean_reviews
from src.transform.loaders import load_to_jsonl, load_to_sqlite
from src.transform.normalizers import (
    normalize_brand_series,
    normalize_brand,
    CANONICAL_BRANDS,
)

# ── Logging setup ──────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


# ── Config loading ─────────────────────────────────────────────────────────

def load_config(config_path: Path) -> dict:
    """Load YAML configuration file."""
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ── Processed files tracking ───────────────────────────────────────────────

def get_processed_files(log_path: Path) -> set[str]:
    """Return set of filenames already processed in previous runs."""
    if not log_path.exists():
        return set()
    return set(log_path.read_text(encoding="utf-8").splitlines())


def register_processed_files(log_path: Path, filenames: list[str]) -> None:
    """Append newly processed filenames to the tracking log."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        for name in filenames:
            f.write(name + "\n")
    logger.info("Registered %d file(s) as processed.", len(filenames))


# ── Extract ────────────────────────────────────────────────────────────────

def extract(raw_dir: Path, processed_log: Path) -> pd.DataFrame:
    """
    Read all NEW JSONL files from raw_dir (skipping already-processed ones)
    and concatenate them into a single DataFrame.
    """
    all_files = sorted(raw_dir.glob("*.jsonl"))
    if not all_files:
        raise FileNotFoundError(f"No JSONL files found in: {raw_dir}")

    already_processed = get_processed_files(processed_log)
    new_files = [f for f in all_files if f.name not in already_processed]

    if not new_files:
        logger.warning(
            "All %d JSONL file(s) already processed. Nothing to do.",
            len(all_files),
        )
        return pd.DataFrame()

    logger.info(
        "Found %d file(s) to process (skipping %d already done).",
        len(new_files),
        len(already_processed),
    )

    dfs: list[pd.DataFrame] = []
    for file in new_files:
        df = pd.read_json(file, lines=True)
        df["source_file"] = file.name
        logger.info("  → Read %d rows from '%s'.", len(df), file.name)
        dfs.append(df)

    register_processed_files(processed_log, [f.name for f in new_files])
    return pd.concat(dfs, ignore_index=True)


# ── Transform ──────────────────────────────────────────────────────────────

def transform(
    df: pd.DataFrame,
    price_min: float,
    price_max: float,
) -> pd.DataFrame:
    """
    Apply all transformation rules to the raw dataset.
    Steps:
      1. Infer brand from title (if not present or incomplete)
      2. Clean prices and reviews
      3. Fill missing values
      4. Deduplicate
      6. Apply price filter
      7. Add metadata columns
      8. Remove items that brand is not in the list of brands
    """
    if df.empty:
        return df

    df = df.copy()
    rows_before = len(df)
    logger.info("Starting transformation with %d rows.", rows_before)

    # 1 — Brand handling: Keep raw brand if present, otherwise infer from name.
    # We apply normalization (normalize_brand_series) in both cases to ensure consistency.
    raw_brand = df.get("brand")
    name_series = df.get("name", df.get("title"))

    if raw_brand is not None:
        # Fill missing raw brands with inference from name
        df["brand"] = raw_brand.fillna(name_series.map(normalize_brand))
        # Normalize the result (to catch cases where raw brand is not in canonical format)
        df["brand"] = normalize_brand_series(df["brand"])
    else:
        # Fallback if the 'brand' column is completely missing from raw
        df["brand"] = normalize_brand_series(name_series)

    # 2 — Clean and sanitize prices
    df["old_money"] = clean_prices(df["old_money"])
    df["new_money"] = clean_prices(df["new_money"])
    df["reviews_rating_number"] = clean_reviews(df["reviews_rating_number"])

    # PRICE LOGIC:
    # Use old_money as fallback for new_money if latter is missing
    df["new_money"] = df["new_money"].fillna(df["old_money"])

    # SANITY CHECK & ADJUSTMENT for old_money:
    # If old_money is null, too low (< 500), or lower than new_money,
    # sync it with new_money to ensure data quality and dashboard consistency.
    invalid_old_money_mask = (
        df["old_money"].isna() |
        (df["old_money"] < 500) |
        (df["old_money"] < df["new_money"])
    )
    df.loc[invalid_old_money_mask, "old_money"] = df["new_money"]

    # 3 — Keep raw sales fact (no estimation)
    # The 'sales_bucket' column already contains the raw text from Scrapy.

    # 4 — Fill missing reviews
    df["reviews_rating_number"] = df["reviews_rating_number"].fillna(0)

    # 5 — Deduplication
    # We include 'seller' and 'sales_bucket' to ensure different offers are preserved,
    # and 'brand' + 'name' to identify the product uniquely within those offers.
    dedup_cols = [
        "brand", "name", "old_money", "new_money",
        "seller", "sales_bucket"
    ]
    existing_dedup_cols = [c for c in dedup_cols if c in df.columns]
    df = df.drop_duplicates(subset=existing_dedup_cols, keep="last")
    logger.info(
        "After deduplication: %d rows (removed %d).",
        len(df),
        rows_before - len(df),
    )

    # 6 — Noise filtering (Accessories & Parts)
    # Exclude items that are clearly not notebooks (e.g. skins, cases, chargers)
    noise_keywords = [
        "capa", "skin", "pelicula", "bolsa", "maleta", "estojo", "case",
        "fonte", "carregador", "bateria", "teclado", "mouse", "tela",
        "display", "ssd", "memoria", "cabo", "dobradica", "carcaca",
        "suporte", "cooler", "ventilador", "base", "adesivo", "hub", "adaptador",
        "placa", "peças", "gabinete", "para o", "para", "peça", "dobradiças",
        "moldura", "tela", "compatible ", "compatível", 
    ]
    # Use non-capturing group (?:...) to avoid UserWarning about match groups
    noise_regex = r"\b(?:" + "|".join(noise_keywords) + r")\b"
    is_notebook = ~df["name"].str.contains(noise_regex, case=False, regex=True)
    df = df[is_notebook]
    logger.info("After noise filtering: %d rows.", len(df))

    # 7 — Price filter
    price_mask = (
        df["new_money"].notna()
        & df["new_money"].between(price_min, price_max)
    )
    rows_before_filter = len(df)
    df = df[price_mask]
    removed = rows_before_filter - len(df)
    if removed:
        logger.warning(
            "Price filter [R$%.0f–R$%.0f] removed %d rows.",
            price_min, price_max, removed,
        )
    
    # 8 - Brand filter: Only keep items successfully identified as a known brand
    df = df[df["brand"].isin(CANONICAL_BRANDS)]
    logger.info("After brand filter: %d rows.", len(df))

    # 9 — Metadata
    df = df.rename(columns={"url": "_source"}) if "url" in df.columns else df
    df["_datetime"] = datetime.now().isoformat()

    df = df.sort_values("name").reset_index(drop=True)
    logger.info("Transformation complete. Final dataset: %d rows.", len(df))
    return df


# ── Main ───────────────────────────────────────────────────────────────────

def main() -> None:
    BASE_DIR = Path(__file__).resolve().parents[2]
    config_path = BASE_DIR / "config" / "settings.yaml"

    logger.info("Loading configuration from '%s'.", config_path)
    config = load_config(config_path)
    etl_cfg = config["etl"]

    # Resolve paths
    raw_dir = BASE_DIR / etl_cfg["raw_data_dir"]
    processed_dir = BASE_DIR / etl_cfg["processed_dir"]
    analytics_dir = BASE_DIR / etl_cfg["analytics_dir"]
    db_path = analytics_dir / etl_cfg["db_filename"]
    output_path = processed_dir / etl_cfg["processed_filename"]
    processed_log = BASE_DIR / etl_cfg["processed_log"]
    table_name = etl_cfg["table_name"]
    price_min = float(etl_cfg["price_min"])
    price_max = float(etl_cfg["price_max"])

    logger.info("=== ETL Pipeline Start ===")

    # Extract
    raw_df = extract(raw_dir, processed_log)
    if raw_df.empty:
        logger.info("No new data to process. Exiting.")
        return

    # Transform
    transformed_df = transform(raw_df, price_min=price_min, price_max=price_max)

    if transformed_df.empty:
        logger.warning("Transformed dataset is empty. Nothing to load.")
        return

    # Load
    load_to_sqlite(transformed_df, db_path, table_name=table_name)
    load_to_jsonl(transformed_df, output_path)

    logger.info("=== ETL Pipeline Complete ===")


if __name__ == "__main__":
    main()
