from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "Analyze_AB_Test_Results.ipynb"
REPORTS = ROOT / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

HTML_NAME = "Analyze_AB_Test_Results.html"
PDF_NAME = "Analyze_AB_Test_Results.pdf"

def run(cmd: list[str]) -> None:
    print("Running:", " ".join(map(str, cmd)))
    subprocess.run(cmd, check=True)


def main() -> None:
    if not NOTEBOOK.exists():
        raise FileNotFoundError(f"Notebook not found: {NOTEBOOK}")

    run([
        sys.executable, "-m", "jupyter", "nbconvert",
        "--to", "html",
        "--execute",
        str(NOTEBOOK),
        "--output", HTML_NAME,
        "--output-dir", str(REPORTS),
    ])

    html_path = REPORTS / HTML_NAME
    if not html_path.exists():
        raise FileNotFoundError(f"HTML export not created: {html_path}")

    run([
        sys.executable, "-m", "jupyter", "nbconvert",
        "--to", "webpdf",
        "--execute",
        "--allow-chromium-download",
        str(NOTEBOOK),
        "--output", PDF_NAME,
        "--output-dir", str(REPORTS),
    ])

    print(f"Created: {html_path}")
    print(f"Created: {REPORTS / PDF_NAME}")


if __name__ == "__main__":
    main()
