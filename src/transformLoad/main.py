import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Tuple

import pandas as pd


def normalize_sales_bucket(series: pd.Series) -> Tuple[pd.Series, pd.Series]:
    """
    Convert raw sales text into:
    - sales_count_estimate: numeric estimate
    - sales_bucket: categorical sales range
    """
    sales_text = series.fillna("").astype(str).str.lower()

    sales_count = (
        sales_text
        .replace(r"^em$", "0", regex=True)
        .str.extract(r"(\d+)", expand=False)
    )

    sales_count = pd.to_numeric(sales_count, errors="coerce").fillna(0)

    sales_count.loc[sales_text.str.contains("mil", na=False)] *= 1000

    sales_bucket = pd.cut(
        sales_count,
        bins=[0, 100, 500, 1000, 5000, 10000, float("inf")],
        labels=["0-100", "100-500", "500-1k", "1k-5k", "5k-10k", "10k+"],
        right=False
    )

    return sales_count, sales_bucket


def extract(data_dir: Path) -> pd.DataFrame:
    """
    Read all JSONL files from the data directory and concatenate them.
    """
    files = list(data_dir.glob("*.jsonl"))

    if not files:
        raise FileNotFoundError(f"No JSONL files found in: {data_dir}")

    dfs = []
    for file in files:
        df = pd.read_json(file, lines=True)
        df["source_file"] = file.name
        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)


def clean_prices(series: pd.Series) -> pd.Series:
    """
    Convert Brazilian-formatted price strings to numeric.
    Example: '1.234,56' -> 1234.56
    """
    return (
        series.astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .pipe(pd.to_numeric, errors="coerce")
    )


def clean_reviews(series: pd.Series) -> pd.Series:
    """
    Convert review rating strings to numeric.
    Example: '4,8' -> 4.8
    """
    return (
        series.astype(str)
        .str.replace(",", ".", regex=False)
        .str.replace("ou", "", regex=False)
        .str.strip()
        .pipe(pd.to_numeric, errors="coerce")
    )


def transform(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply all transformation rules to the raw dataset.
    """
    df = df.copy()

    df = df.sort_values("source_file")

    df["sales_count_estimate"], df["sales_bucket"] = normalize_sales_bucket(
        df["sales_bucket"]
    )

    df["old_money"] = clean_prices(df["old_money"])
    df["new_money"] = clean_prices(df["new_money"])
    df["reviews_rating_number"] = clean_reviews(df["reviews_rating_number"])

    df["new_money"] = df["new_money"].fillna(df["old_money"])
    df["reviews_rating_number"] = df["reviews_rating_number"].fillna(0)

    df = df.drop_duplicates(
        subset=[
            "brand",
            "name",
            "old_money",
            "new_money",
            "reviews_rating_number",
            "seller",
            "sales_bucket",
        ],
        keep="last"
    )

    df["_source"] = df["url"]
    df = df.drop(columns=["url"])

    df["_datetime"] = datetime.now()

    df = df[
        (df["old_money"] >= 1000) & (df["old_money"] <= 10000) &
        (df["new_money"] >= 1000) & (df["new_money"] <= 10000)
    ]

    df = df.sort_values("name")

    return df


def load_to_sqlite(df: pd.DataFrame, db_path: Path, table_name: str = "notebook") -> None:
    """
    Save transformed data into a SQLite table.
    """
    with sqlite3.connect(db_path) as conn:
        df.to_sql(table_name, conn, if_exists="replace", index=False)


def load_to_jsonl(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save transformed data into a JSONL file.
    """
    df.to_json(
        output_path,
        orient="records",
        lines=True,
        date_format="iso"
    )


def main() -> None:
    BASE_DIR = Path(__file__).resolve().parents[2]
    data_dir = BASE_DIR / "data"
    db_path = data_dir / "mercadolivre.db"
    output_path = data_dir / "notebooks.jsonl"

    raw_df = extract(data_dir)
    transformed_df = transform(raw_df)

    load_to_sqlite(transformed_df, db_path)
    load_to_jsonl(transformed_df, output_path)


if __name__ == "__main__":
    main()