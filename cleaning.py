"""
cleaning.py
Data cleaning utilities.
"""
import pandas as pd
from typing import List, Optional

def dropna_selected_columns(df: pd.DataFrame, subset: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Drop rows with NA in 'subset' columns.
    - subset: list of columns to check. If None, check all columns.
    Returns cleaned DataFrame.
    """
    if subset is None:
        subset = list(df.columns)
    # Defensive: keep index reset
    cleaned = df.dropna(subset=subset).reset_index(drop=True)
    return cleaned
