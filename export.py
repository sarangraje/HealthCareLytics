import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
import tempfile
import os

def save_chart(fig, filename="chart.png"):
    """
    Save a matplotlib/plotly figure as PNG.
    """
    if hasattr(fig, "write_image"):  # Plotly figure
        fig.write_image(filename)
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
        flowables.append(Image(chart, width=400, height=300))
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
