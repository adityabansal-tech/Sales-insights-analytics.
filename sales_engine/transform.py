"""
Data cleaning & validation before load.
"""
import pandas as pd


def clean_fact_sales(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)

    # drop exact duplicates
    df = df.drop_duplicates(subset=["line_id"])

    # drop rows with missing critical fields
    df = df.dropna(subset=["order_date", "customer_id", "product_id", "quantity", "unit_price"])

    # remove invalid quantities/prices
    df = df[(df["quantity"] > 0) & (df["unit_price"] > 0)]

    # recompute derived columns to guarantee consistency
    df["sales_amount"] = (df["quantity"] * df["unit_price"] * (1 - df["discount"])).round(2)

    after = len(df)
    print(f"[transform] fact_sales: {before} -> {after} rows after cleaning "
          f"({before - after} dropped)")
    return df


def clean_dimension(df: pd.DataFrame, key_col: str) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates(subset=[key_col])
    df = df.dropna(subset=[key_col])
    after = len(df)
    if before != after:
        print(f"[transform] {key_col}: {before} -> {after} rows after cleaning")
    return df
