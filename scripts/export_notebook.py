from pathlib import Path
import subprocess
import sys

from pptx import Presentation


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "Analyze_AB_Test_Results.ipynb"
REPORTS = ROOT / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)
PRESENTATION = ROOT / "presentation" / "AB_Test_Results.pptx"
TEMPLATE_PRESENTATION = Path.home() / "Downloads" / "analyze-a_b-test-results-template (2).pptx"
COUNTRY_IMAGE = ROOT / "images" / "country_distribution_pct.png"

HTML_NAME = "Analyze_AB_Test_Results.html"
PDF_NAME = "Analyze_AB_Test_Results.pdf"


def run(cmd):
    print("Running:", " ".join(map(str, cmd)))
    subprocess.run(cmd, check=True)


def remove_slide(prs: Presentation, slide_index: int) -> None:
    slide_id_list = prs.slides._sldIdLst
    slide_id_list.remove(slide_id_list[slide_index])


def update_presentation():
    source_presentation = TEMPLATE_PRESENTATION if TEMPLATE_PRESENTATION.exists() else PRESENTATION
    if not source_presentation.exists():
        raise FileNotFoundError(
            f"Neither template nor project presentation was found: {TEMPLATE_PRESENTATION} / {PRESENTATION}"
        )
    if not COUNTRY_IMAGE.exists():
        raise FileNotFoundError(f"Country distribution image not found: {COUNTRY_IMAGE}")

    prs = Presentation(source_presentation)

    if len(prs.slides) >= 2:
        slide_text = "\n".join(
            getattr(shape, "text", "").strip() for shape in prs.slides[1].shapes if hasattr(shape, "text")
        )
        if "How to Use This Template" in slide_text:
            remove_slide(prs, 1)

    prs.slides[0].shapes[2].text = "Data Scientist: Francesco Malagrino"

    slide = prs.slides[2]
    slide.shapes[1].text = (
        "Total Variant Visitors: 35,211\n"
        "Total Control Participants: 34,678\n\n"
        "Users from: US (69.9%), UK (25.1%), CA (5.0%)"
    )
    picture_shape = next(shape for shape in slide.shapes if shape.shape_type == 13)
    left, top, width, height = picture_shape.left, picture_shape.top, picture_shape.width, picture_shape.height
    sp = picture_shape._element
    sp.getparent().remove(sp)
    slide.shapes.add_picture(str(COUNTRY_IMAGE), left, top, width=width, height=height)

    slide = prs.slides[3]
    slide.shapes[1].text = (
        "Executive Summary: Treatment is associated with higher conversion rates than control overall and within each country. "
        "The treatment conversion rate is 15.53% versus 10.53% for control, and the treatment lift appears in the US, UK, and CA. "
        "Country-level conversion rates differ somewhat, but the treatment effect is consistently positive."
    )
    table = next(shape.table for shape in slide.shapes if shape.shape_type == 19)
    values = {
        (1, 1): "10.73%",
        (1, 2): "10.16%",
        (1, 3): "9.45%",
        (2, 1): "15.78%",
        (2, 2): "14.87%",
        (2, 3): "15.40%",
    }
    for (row, col), value in values.items():
        table.cell(row, col).text = value

    slide = prs.slides[4]
    slide.shapes[1].text = (
        "Treatment Conversion Rate: 15.53%\n"
        "Control Conversion Rate:\u200b 10.53%\n"
        "Delta in Treatment vs. Control Conversion Rate:\u200b +5.01 percentage points\n"
        "p-value:\u200b 0.00 (simulation-based; 0 of 500 null differences exceeded observed)\n"
        "Conclusion:\n"
        "\u200bWe reject H0 at the 0.05 level. The treatment page performs significantly better than the control page, "
        "so the company should implement the new page."
    )

    prs.save(PRESENTATION)
    print(f"Created: {PRESENTATION}")


def main():
    if not NOTEBOOK.exists():
        raise FileNotFoundError(f"Notebook not found: {NOTEBOOK}")
    update_presentation()

    run([
        sys.executable, "-m", "jupyter", "nbconvert",
        "--to", "html",
        "--execute",
        str(NOTEBOOK),
        "--output", HTML_NAME,
        "--output-dir", str(REPORTS),
    ])

    run([
        sys.executable, "-m", "jupyter", "nbconvert",
        "--to", "webpdf",
        "--execute",
        "--allow-chromium-download",
        str(NOTEBOOK),
        "--output", PDF_NAME,
        "--output-dir", str(REPORTS),
    ])

    print(f"Created: {REPORTS / HTML_NAME}")
    print(f"Created: {REPORTS / PDF_NAME}")


if __name__ == "__main__":
    main()
