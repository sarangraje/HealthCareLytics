"""
export.py
Report generation utilities: create PDF reports including charts and summary stats.
Uses reportlab for PDF and Plotly + kaleido for images.
"""
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet
import tempfile
import os
import plotly.io as pio
import tempfile

def _save_plotly_fig_as_png(fig, path):
    # Use kaleido backend
    if fig is not None:
        pio.write_image(fig, path, format="png", engine="kaleido", scale=2)

def build_pdf_report(output_path: str, df_sample: pd.DataFrame, analysis_result: pd.DataFrame = None, fig=None, meta: dict = None):
    """
    Build a PDF report at output_path.
    - df_sample: a sampled subset of the dataset (small)
    - analysis_result: DataFrame from analysis (optional)
    - fig: a Plotly figure object to include (optional)
    - meta: dict with file metadata (optional)
    """
    # Create temporary image file (only if chart exists)
    tmpdir = tempfile.mkdtemp()
    figpath = os.path.join(tmpdir, "figure.png")
    if fig is not None:
        _save_plotly_fig_as_png(fig, figpath)

    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    flow = []

    # --- Title ---
    title = meta.get("file", "HealthCareLytics Report") if meta else "HealthCareLytics Report"
    flow.append(Paragraph(f"<b>{title}</b>", styles['Title']))
    flow.append(Spacer(1, 12))

    # --- Metadata ---
    if meta:
        flow.append(Paragraph(f"Generated: {pd.Timestamp.now()}", styles['Normal']))
        if "rows" in meta:
            flow.append(Paragraph(f"Rows analyzed: {meta['rows']}", styles['Normal']))
    flow.append(Spacer(1, 12))

    # --- Summary statistics ---
    if df_sample is not None and not df_sample.empty:
        flow.append(Paragraph("<b>Summary statistics (sample)</b>", styles['Heading3']))
        sample_stats = df_sample.describe(include='all').to_string()
        flow.append(Paragraph(f"<pre>{sample_stats}</pre>", styles['Code']))
        flow.append(Spacer(1, 12))
    else:
        flow.append(Paragraph("No data sample available.", styles['Normal']))
        flow.append(Spacer(1, 12))

    # --- Analysis results ---
    if analysis_result is not None and not analysis_result.empty:
        flow.append(Paragraph("<b>Analysis result</b>", styles['Heading3']))
        flow.append(Paragraph(f"<pre>{analysis_result.head(200).to_string(index=False)}</pre>", styles['Code']))
        flow.append(Spacer(1, 12))
    else:
        flow.append(Paragraph("No analysis results available.", styles['Normal']))
        flow.append(Spacer(1, 12))

    # --- Chart ---
    if fig is not None:
        flow.append(Paragraph("<b>Chart</b>", styles['Heading3']))
        flow.append(RLImage(figpath, width=450, height=300))
        flow.append(Spacer(1, 12))

    # --- Build PDF ---
    doc.build(flow)

    # --- Cleanup ---
    try:
        os.remove(figpath)
    except Exception:
        pass
    try:
        os.rmdir(tmpdir)
    except Exception:
        pass

def save_chart(fig, filename="chart.png"):
    """
    Save a matplotlib/plotly figure as PNG.
    """
    if hasattr(fig, "write_image"):  # Plotly figure
        import plotly.io as pio
        pio.write_image(fig, filename, format="png", engine="kaleido", scale=2)
    else:  # Matplotlib figure
        fig.savefig(filename, bbox_inches="tight")
    return filename



def export_pdf(summary_text, chart_files, output_file="report.pdf"):
    """
    Export a PDF with summary text + charts.
    
    Args:
        summary_text (str): Text content (stats, notes).
        chart_files (list): List of chart image file paths.
        output_file (str): Name of the output PDF file.
    """
    doc = SimpleDocTemplate(output_file, pagesize=letter)
    styles = getSampleStyleSheet()
    flowables = []
    
    # Add summary
    flowables.append(Paragraph("<b>HealthcareLytics Report</b>", styles["Title"]))
    flowables.append(Spacer(1, 12))
    flowables.append(Paragraph(summary_text, styles["Normal"]))
    flowables.append(Spacer(1, 24))
    
    # Add charts
    for chart in chart_files:
        flowables.append(RLImage(chart, width=400, height=300))
        flowables.append(Spacer(1, 12))
    
    doc.build(flowables)
    return output_file


def generate_temp_file(suffix=".pdf"):
    """
    Create a temporary file path for downloads.
    """
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    return path
