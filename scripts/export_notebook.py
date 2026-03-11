from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "Analyze_AB_Test_Results.ipynb"
REPORTS = ROOT / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

HTML_OUT = REPORTS / "Analyze_AB_Test_Results.html"
PDF_OUT = REPORTS / "Analyze_AB_Test_Results.pdf"

def run(cmd):
    print("Running:", " ".join(map(str, cmd)))
    subprocess.run(cmd, check=True)

def main():
    if not NOTEBOOK.exists():
        raise FileNotFoundError(f"Notebook not found: {NOTEBOOK}")

    run([
        sys.executable, "-m", "jupyter", "nbconvert",
        "--to", "html",
        "--execute",
        str(NOTEBOOK),
        "--output", HTML_OUT.name,
        "--output-dir", str(REPORTS),
    ])

    if not HTML_OUT.exists():
        raise FileNotFoundError(f"HTML export not created: {HTML_OUT}")

    run([
        sys.executable, "-m", "jupyter", "nbconvert",
        "--to", "webpdf",
        str(NOTEBOOK),
        "--execute",
        "--allow-chromium-download",
        "--output", PDF_OUT.name,
        "--output-dir", str(REPORTS),
    ])

    print(f"Created: {HTML_OUT}")
    print(f"Created: {PDF_OUT}")

if __name__ == "__main__":
    main()
