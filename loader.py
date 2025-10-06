import pandas as pd
import io

def load_dataset(uploaded_file, max_rows=None):
    """
    Load a dataset (CSV or Excel) into a pandas DataFrame.
    
    Args:
        uploaded_file: file-like object from Streamlit uploader
        max_rows: int or None, if set, limit number of rows to load
        
    Returns:
        df (pd.DataFrame): Loaded dataset
    """
    if uploaded_file is None:
        return None
    
    filename = uploaded_file.name.lower()
    
    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(uploaded_file, nrows=max_rows)
        elif filename.endswith((".xls", ".xlsx")):
            df = pd.read_excel(uploaded_file, nrows=max_rows)
        else:
            raise ValueError("Unsupported file type. Please upload CSV or Excel.")
    except Exception as e:
        raise RuntimeError(f"Error loading dataset: {str(e)}")
    
    return df


def sample_rows(df, num_rows):
    """
    Return a sample of the DataFrame for performance on very large datasets.
    
    Args:
        df (pd.DataFrame): Original DataFrame
        num_rows (int): Number of rows to sample
        
    Returns:
        pd.DataFrame
    """
    if df is None:
        return None
    if num_rows >= len(df):
        return df
    return df.sample(n=num_rows, random_state=42).reset_index(drop=True)
