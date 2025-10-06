

"""
main.py
Streamlit entry point for HealthCareLytics.
"""
import streamlit as st
import pandas as pd
import os
from datetime import datetime
from analytics import run_analysis, available_operations, generate_plotly_figure
from cleaning import dropna_selected_columns
from export import build_pdf_report

st.set_page_config(page_title="HealthCareLytics", layout="wide")

REPORTS_DIR = "reports"
if not os.path.exists(REPORTS_DIR):
    os.makedirs(REPORTS_DIR)

st.title("HealthCareLytics")
st.markdown("Upload healthcare CSV / Excel datasets, analyze interactively, and export PDF reports.")

# -- Upload
uploaded_file = st.file_uploader("Upload dataset (CSV or Excel)", type=['csv', 'xlsx', 'xls'])
max_rows_option = st.selectbox("If dataset is large, load first:", ["Auto (detect & prompt)", "10000", "20000", "Custom..."])
custom_rows = None
if max_rows_option == "Custom...":
    custom_rows = st.number_input("Custom number of rows to load", min_value=1000, max_value=10000000, value=10000, step=1000)

df = None
total_rows = None
if uploaded_file:
    st.info(f"Uploaded: {uploaded_file.name}")
    try:
        if uploaded_file.name.endswith(".csv"):
            uploaded_file.seek(0)
            row_count = sum(1 for _ in uploaded_file) - 1
            total_rows = max(0, row_count)
            uploaded_file.seek(0)

            if max_rows_option == "Auto (detect & prompt)" and total_rows and total_rows > 20000:
                choice = st.radio(f"Detected ~{total_rows} rows. Choose how many rows to load:", ("10,000", "20,000", "Custom"))
                if choice == "Custom":
                    read_n = st.number_input("Rows to read", min_value=1000, max_value=10000000, value=10000, step=1000)
                else:
                    read_n = int(choice.replace(",", ""))
            elif max_rows_option == "10000":
                read_n = 10000
            elif max_rows_option == "20000":
                read_n = 20000
            elif max_rows_option == "Custom...":
                read_n = custom_rows or 10000
            else:
                read_n = None

            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, nrows=read_n if read_n else None)
        else:
            uploaded_file.seek(0)
            df = pd.read_excel(uploaded_file, nrows=(custom_rows or None))
            total_rows = None
        st.success(f"Loaded {len(df):,} rows" + (f" (from ~{total_rows:,} total)" if total_rows else ""))
    except Exception as e:
        st.error(f"Could not read file: {e}")
        st.stop()

    # -- Column mapping
    st.sidebar.header("Column mapping & selections")
    all_cols = list(df.columns)
    st.sidebar.markdown(f"**Detected columns ({len(all_cols)})**")
    selected_columns = st.sidebar.multiselect(
        "Select columns to include in analysis (at least one)",
        all_cols, default=all_cols[: min(8, len(all_cols))]
    )

    if not selected_columns:
        st.warning("Please select at least one column to proceed.")
        st.stop()

    working_df = df[selected_columns].copy()

    # -- Data cleaning
    st.sidebar.markdown("### Data cleaning (user-controlled)")
    remove_na = st.sidebar.checkbox("Remove rows with missing/nulls in selected columns (Drop NA)", value=False)
    if remove_na:
        if st.sidebar.button("Run data cleaning (drop NA)"):
            cleaned = dropna_selected_columns(working_df, subset=selected_columns)
            st.sidebar.success(f"Dropped rows -> {len(working_df) - len(cleaned):,} rows removed")
            working_df = cleaned
    else:
        st.sidebar.info("Data cleaning not applied (duplicates preserved by design).")

    # -- Filters
    st.subheader("Data preview & filters")
    st.write(f"Showing columns: {', '.join(selected_columns)}")

    st.sidebar.header("Filters")
    filters = {}
    for col in selected_columns:
        if pd.api.types.is_numeric_dtype(working_df[col]):
            lo = float(working_df[col].min()) if not working_df[col].isna().all() else None
            hi = float(working_df[col].max()) if not working_df[col].isna().all() else None
            if lo is not None and hi is not None:
                r = st.sidebar.slider(f"{col} range", min_value=lo, max_value=hi, value=(lo, hi))
                filters[col] = ("numeric_range", r)
        else:
            vals = working_df[col].dropna().unique()
            if len(vals) <= 50:
                sel = st.sidebar.multiselect(f"Filter {col}", options=sorted(map(str, vals)), default=None)
                if sel:
                    filters[col] = ("in", sel)
            else:
                search = st.sidebar.text_input(f"Search {col} (substring)")
                if search:
                    filters[col] = ("search", search)

    # Apply filters
    df_filtered = working_df.copy()
    for col, cond in filters.items():
        typ = cond[0]
        if typ == "numeric_range":
            lo, hi = cond[1]
            df_filtered = df_filtered[df_filtered[col].between(lo, hi)]
        elif typ == "in":
            df_filtered = df_filtered[df_filtered[col].astype(str).isin(cond[1])]
        elif typ == "search":
            df_filtered = df_filtered[df_filtered[col].astype(str).str.contains(cond[1], case=False, na=False)]

    st.dataframe(df_filtered.head(100))
    st.write(f"Filtered rows: {len(df_filtered):,}")

    # -- Charting (independent of analysis)
    st.subheader("Charts")
    chart_type = st.selectbox(
        "Select chart type",
        ["Bar", "Line", "Pie", "Histogram", "Box", "Scatter", "Bubble", "Stacked Area", "Heatmap (correlation)"]
    )

    target_col_chart = st.selectbox("Select target column", selected_columns)
    group_by_chart = st.multiselect("Group by (optional)", [c for c in selected_columns if c != target_col_chart], key="group_by_chart_selector")

    fig_chart = generate_plotly_figure(df_filtered, chart_type, target_col_chart, group_by_chart)
    st.plotly_chart(fig_chart, use_container_width=True)

    # -- Analysis (optional)
    st.subheader("Optional Analysis")
    if st.checkbox("Enable analysis"):
        target_col = st.selectbox("Choose target column for analysis", options=selected_columns)
        operation = st.selectbox("Choose operation", options=available_operations())
        group_by = st.multiselect("Group by (optional)", options=[c for c in selected_columns if c != target_col],key="group_by_selector")
        if st.button("Run Analysis"):
            with st.spinner("Computing analysis..."):
                try:
                    result_df = run_analysis(df_filtered, target_col, operation, group_by)
                    st.subheader("Analysis results")
                    st.dataframe(result_df.head(200))
                    st.markdown("### Summary statistics")
                    st.write(result_df.describe(include='all'))
                except Exception as e:
                    st.error(f"Analysis failed: {e}")

    # -- Export PDF
    st.subheader("Export / Download")
    if st.button("Build PDF report"):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(REPORTS_DIR, f"report_{ts}.pdf")
        try:
            build_pdf_report(
                report_path,
                df_sample=df_filtered.head(5000),
                analysis_result=result_df if 'result_df' in locals() else None,
                fig=fig_chart,
                meta={"file": uploaded_file.name, "rows": len(df_filtered)}
            )
            with open(report_path, "rb") as f:
                pdf_bytes = f.read()
            st.success(f"Report saved to {report_path}")
            st.download_button("Download PDF report", data=pdf_bytes, file_name=os.path.basename(report_path), mime="application/pdf")
        except Exception as e:
            st.error(f"Failed to generate report: {e}")