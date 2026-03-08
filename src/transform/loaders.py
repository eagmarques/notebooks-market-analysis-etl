"""
loaders.py
Funções de persistência de dados: SQLite (com views analíticas) e JSONL.
"""
from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


# ── SQL Views ────────────────────────────────────────────────────────────────

_VIEWS_DDL = """
CREATE VIEW IF NOT EXISTS vw_brand_summary AS
SELECT
    brand,
    COUNT(*)                                           AS total_listings,
    ROUND(AVG(new_money), 2)                           AS avg_price,
    ROUND(AVG(old_money), 2)                           AS avg_old_price,
    ROUND(AVG(reviews_rating_number), 2)               AS avg_rating,
    ROUND(
        AVG((old_money - new_money) * 100.0 / old_money),
        2
    )                                                  AS avg_discount_pct
FROM notebooks
WHERE brand IS NOT NULL
GROUP BY brand;

CREATE VIEW IF NOT EXISTS vw_price_buckets AS
SELECT
    CASE
        WHEN new_money <  2000 THEN 'Até R$2k'
        WHEN new_money <  4000 THEN 'R$2k–4k'
        WHEN new_money <  6000 THEN 'R$4k–6k'
        WHEN new_money <  8000 THEN 'R$6k–8k'
        ELSE                        'Acima R$8k'
    END AS price_bucket,
    COUNT(*) AS total_listings
FROM notebooks
WHERE new_money IS NOT NULL
GROUP BY price_bucket;

CREATE VIEW IF NOT EXISTS vw_top_sellers AS
SELECT
    seller,
    COUNT(*)                   AS total_listings,
    ROUND(AVG(new_money), 2)   AS avg_price
FROM notebooks
WHERE seller IS NOT NULL
GROUP BY seller
ORDER BY total_listings DESC;
"""


def _create_views(conn: sqlite3.Connection) -> None:
    """Create or replace analytical SQL views."""
    # SQLite does not support CREATE OR REPLACE VIEW, so we drop first.
    view_names = ["vw_brand_summary", "vw_price_buckets", "vw_top_sellers"]
    for view in view_names:
        conn.execute(f"DROP VIEW IF EXISTS {view}")
    for statement in _VIEWS_DDL.strip().split(";"):
        stmt = statement.strip()
        if stmt:
            conn.execute(stmt)
    logger.info("SQL analytical views created/refreshed.")


def load_to_sqlite(
    df: pd.DataFrame,
    db_path: Path,
    table_name: str = "notebooks",
) -> None:
    """
    Save transformed data into a SQLite table and refresh analytical views.
    The table is fully replaced on each run (upsert via replace strategy).
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        logger.info("Loaded %d rows into table '%s'.", len(df), table_name)
        _create_views(conn)


def load_to_jsonl(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save transformed data into a JSONL file (processed layer).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_json(output_path, orient="records", lines=True, date_format="iso")
    logger.info("Saved %d rows to '%s'.", len(df), output_path)
