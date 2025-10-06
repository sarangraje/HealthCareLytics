"""
analytics.py
Core analysis functions: aggregations, trends, and plotting helpers.
"""
from typing import List, Optional
import pandas as pd
import numpy as np
import plotly.express as px

def available_operations():
    return ["Count", "Sum", "Average", "Min", "Max", "Trend"]

def run_analysis(df: pd.DataFrame, target_col: str, operation: str, group_by: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Perform an analysis on df.
    - df: filtered dataframe (already sampled if needed)
    - target_col: column to perform operation on
    - operation: one of available_operations()
    - group_by: optional list of columns to group by
    Returns a summary DataFrame.
    """
    if group_by is None or len(group_by) == 0:
        group_by = []

    # If target is numeric for numeric ops, coerce
    if operation in ("Sum", "Average", "Min", "Max", "Trend"):
        # coerce numeric; invalid parsing -> NaN
        series = pd.to_numeric(df[target_col], errors="coerce")
    else:
        series = df[target_col]

    if operation == "Count":
        if group_by:
            res = df.groupby(group_by).size().reset_index(name="count")
        else:
            res = pd.DataFrame({"count": [len(df)]})
        return res

    if operation == "Sum":
        if group_by:
            res = df.groupby(group_by)[target_col].apply(lambda s: pd.to_numeric(s, errors="coerce").sum(skipna=True)).reset_index(name="sum")
        else:
            res = pd.DataFrame({"sum": [pd.to_numeric(df[target_col], errors="coerce").sum(skipna=True)]})
        return res

    if operation == "Average":
        if group_by:
            res = df.groupby(group_by)[target_col].apply(lambda s: pd.to_numeric(s, errors="coerce").mean()).reset_index(name="mean")
        else:
            res = pd.DataFrame({"mean": [pd.to_numeric(df[target_col], errors="coerce").mean()]})
        return res

    if operation == "Min":
        if group_by:
            res = df.groupby(group_by)[target_col].apply(lambda s: pd.to_numeric(s, errors="coerce").min()).reset_index(name="min")
        else:
            res = pd.DataFrame({"min": [pd.to_numeric(df[target_col], errors="coerce").min()]})
        return res

    if operation == "Max":
        if group_by:
            res = df.groupby(group_by)[target_col].apply(lambda s: pd.to_numeric(s, errors="coerce").max()).reset_index(name="max")
        else:
            res = pd.DataFrame({"max": [pd.to_numeric(df[target_col], errors="coerce").max()]})
        return res

    if operation == "Trend":
        # Trend implies time-series: try to interpret group_by or index as date
        # If there is a single datetime column in group_by, resample or aggregate by period
        df_copy = df.copy()
        # try to find datetime-like column
        dt_cols = [c for c in df_copy.columns if pd.api.types.is_datetime64_any_dtype(df_copy[c]) or pd.api.types.is_datetime64_dtype(pd.to_datetime(df_copy[c], errors="coerce"))]
        if not dt_cols and group_by:
            # maybe first group_by is a time column
            dt_candidate = group_by[0]
            try:
                df_copy[dt_candidate] = pd.to_datetime(df_copy[dt_candidate], errors="coerce")
                dt_cols = [dt_candidate]
            except Exception:
                dt_cols = []
        if dt_cols:
            dt = dt_cols[0]
            df_copy[dt] = pd.to_datetime(df_copy[dt], errors="coerce")
            # aggregate by date (day)
            if group_by:
                gb = [c for c in group_by if c != dt]
                if gb:
                    # group by date + other group(s)
                    res = df_copy.groupby([pd.Grouper(key=dt, freq='D')] + gb)[target_col].agg(lambda s: pd.to_numeric(s, errors="coerce").sum()).reset_index()
                else:
                    res = df_copy.groupby(pd.Grouper(key=dt, freq='D'))[target_col].agg(lambda s: pd.to_numeric(s, errors="coerce").sum()).reset_index()
            else:
                res = df_copy.groupby(pd.Grouper(key=dt, freq='D'))[target_col].agg(lambda s: pd.to_numeric(s, errors="coerce").sum()).reset_index()
            return res.fillna(0)
        else:
            # fallback: create an index order trend
            tmp = pd.DataFrame({"index": range(len(df_copy)), target_col: pd.to_numeric(df_copy[target_col], errors="coerce")})
            return tmp

    raise ValueError("Unsupported operation")

def generate_plotly_figure(result_df: pd.DataFrame, chart_type: str, target_col: str, group_by: Optional[List[str]]):
    """
    Create a Plotly figure from analysis result.
    """

    # Basic heuristics for mapping result_df to visualizations
    try:
        if chart_type == "Bar":
            if len(result_df.columns) >= 2:
                x = result_df.columns[0]
                y = result_df.columns[-1]
                fig = px.bar(result_df, x=x, y=y, title="Bar chart")
            else:
                fig = px.bar(result_df, y=result_df.columns[0], title="Bar chart")
        elif chart_type == "Line":
            # expect first col = x (time or group), second col = value
            if len(result_df.columns) >= 2:
                fig = px.line(result_df, x=result_df.columns[0], y=result_df.columns[-1], title="Line chart")
            else:
                fig = px.line(result_df, y=result_df.columns[0], title="Line chart")
        elif chart_type == "Pie":
            if len(result_df.columns) >= 2:
                fig = px.pie(result_df, names=result_df.columns[0], values=result_df.columns[-1], title="Pie chart")
            else:
                fig = px.pie(result_df, names=result_df.index, values=result_df.iloc[:,0], title="Pie chart")
        elif chart_type == "Histogram":
            fig = px.histogram(result_df, x=target_col, title="Histogram")
        elif chart_type == "Box":
            fig = px.box(result_df, y=target_col, title="Box plot")
        elif chart_type == "Scatter":
            if len(result_df.columns) >= 2:
                fig = px.scatter(result_df, x=result_df.columns[0], y=result_df.columns[-1], title="Scatter")
            else:
                fig = px.scatter(result_df, y=result_df.columns[0], title="Scatter")
        elif chart_type == "Bubble":
            # require at least 3 columns: x, y, size
            cols = result_df.columns.tolist()
            if len(cols) >= 3:
                fig = px.scatter(result_df, x=cols[0], y=cols[1], size=cols[2], title="Bubble chart")
            else:
                fig = px.scatter(result_df, y=result_df.iloc[:,0], title="Bubble chart")
        elif chart_type == "Stacked Area":
            # wide-format stacking requires pivot; attempt best-effort
            fig = px.area(result_df, x=result_df.columns[0], y=result_df.columns[-1], title="Stacked area")
        elif chart_type == "Heatmap (correlation)":
            corr = result_df.select_dtypes(include=[int, float]).corr()
            fig = px.imshow(corr, title="Correlation heatmap")
        else:
            fig = px.line(result_df, title="Result")
    except Exception as e:
        # fallback
        fig = px.line(result_df, title=f"Chart (fallback): {e}")

    fig.update_layout(margin=dict(l=20, r=20, t=30, b=20))
    return fig
