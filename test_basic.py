import pandas as pd
from data.loader import load_dataset, sample_rows
from reports.exporter import export_pdf, save_chart, generate_temp_file
import matplotlib.pyplot as plt
import os

def test_loader_csv(tmp_path):
    # Create a fake CSV
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("a,b\n1,2\n3,4\n")
    
    with open(csv_file, "rb") as f:
        df = load_dataset(f)
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2

def test_sample_rows():
    df = pd.DataFrame({"a": range(100)})
    sampled = sample_rows(df, 10)
    assert len(sampled) == 10

def test_export_pdf(tmp_path):
    # Make a dummy chart
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [4, 5, 6])
    chart_file = tmp_path / "chart.png"
    save_chart(fig, str(chart_file))
    
    assert os.path.exists(chart_file)
    
    pdf_file = tmp_path / "report.pdf"
    export_pdf("Test summary", [str(chart_file)], str(pdf_file))
    
    assert os.path.exists(pdf_file)
