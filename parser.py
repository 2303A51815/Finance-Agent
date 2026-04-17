import pandas as pd
from pathlib import Path

def parse_statement(filepath: str):
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    df = pd.read_csv(filepath)
    df.columns = df.columns.str.lower().str.strip()

    rename_map = {
        "transaction date": "date",
        "narration": "description",
        "particulars": "description",
        "debit": "amount",
        "withdrawal": "amount",
    }
    df.rename(columns=rename_map, inplace=True)

    required = ["date", "description", "amount"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing column: '{col}'")

    df = df[required].copy()
    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
    df["amount"] = pd.to_numeric(
        df["amount"].astype(str).str.replace("[₹$,]", "", regex=True),
        errors="coerce"
    )
    df.dropna(inplace=True)
    df.sort_values("date", ascending=False, inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df

def summary(df):
    return {
        "total_transactions": len(df),
        "total_spent": round(df["amount"].sum(), 2),
        "date_range": (df["date"].min(), df["date"].max()),
    }