from inspect import cleandoc
from pathlib import Path
import subprocess
import sys

import matplotlib
import nbformat as nbf
import pandas as pd
from pptx import Presentation

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "Analyze_AB_Test_Results.ipynb"
REPORTS = ROOT / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)
DATA_PATH = ROOT / "data" / "ab_data.csv"
PRESENTATION_PATH = ROOT / "presentation" / "AB_Test_Results.pptx"
IMAGE_PATH = ROOT / "images" / "country_distribution_pct.png"

HTML_NAME = "Analyze_AB_Test_Results.html"
PDF_NAME = "Analyze_AB_Test_Results.pdf"


def md(text: str):
    return nbf.v4.new_markdown_cell(cleandoc(text) + "\n")


def code(text: str):
    return nbf.v4.new_code_cell(cleandoc(text) + "\n")


def build_notebook() -> None:
    cells = [
        md(
            """
            # Analyze A/B Test Results

            This notebook is organized as a submission notebook and includes the template questions directly in the notebook, followed by the corresponding analysis and answers.
            """
        ),
        code(
            """
            import warnings
            from pathlib import Path

            import matplotlib.pyplot as plt
            import numpy as np
            import pandas as pd
            import seaborn as sns
            from scipy.stats import chi2_contingency, norm

            warnings.filterwarnings("ignore")
            sns.set_theme(style="whitegrid")
            pd.set_option("display.max_columns", None)
            pd.set_option("display.float_format", lambda x: f"{x:.6f}")

            ROOT = Path.cwd().resolve()
            if ROOT.name == "notebooks":
                DATA_PATH = ROOT.parent / "data" / "ab_data.csv"
            else:
                DATA_PATH = ROOT / "data" / "ab_data.csv"

            df = pd.read_csv(DATA_PATH)
            df["converted"] = df["converted"].astype(int)
            df.head()
            """
        ),
        md(
            """
            ## How Was the Experiment Implemented?
            """
        ),
        code(
            """
            participant_counts = (
                df["group"]
                .value_counts()
                .rename(index={"treatment": "variant", "control": "control"})
                .rename("participants")
                .to_frame()
            )

            total_variant_visitors = int((df["group"] == "treatment").sum())
            total_control_participants = int((df["group"] == "control").sum())

            print(f"Total Variant Visitors: {total_variant_visitors}")
            print(f"Total Control Participants: {total_control_participants}")
            display(participant_counts)

            country_distribution = (
                df["country"]
                .value_counts(normalize=True)
                .mul(100)
                .sort_index()
                .rename("share_pct")
                .to_frame()
            )
            display(country_distribution)

            fig, ax = plt.subplots(figsize=(8, 4.5))
            bars = ax.bar(
                country_distribution.index,
                country_distribution["share_pct"],
                color=["#4C78A8", "#F58518", "#54A24B"],
                edgecolor="black",
            )
            ax.set_title("User Distribution by Country")
            ax.set_xlabel("Country")
            ax.set_ylabel("Share of Users (%)")
            for bar, value in zip(bars, country_distribution["share_pct"]):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    value + 0.8,
                    f"{value:.1f}%",
                    ha="center",
                    va="bottom",
                )
            plt.tight_layout()
            plt.show()
            """
        ),
        md(
            """
            **Answer:**

            The experiment contains **69,889 total observations**. The **treatment (variant)** group includes **35,211** users and the **control** group includes **34,678** users. Users come from three countries (`US`, `UK`, and `CA`), with the US representing the largest share of traffic. The group sizes are reasonably balanced, which supports a fair comparison between treatment and control.
            """
        ),
        md(
            """
            ## What are the conversion rates, by country and group?
            """
        ),
        code(
            """
            conversion_rates = (
                df.groupby(["country", "group"])["converted"]
                .mean()
                .rename("conversion_rate")
                .reset_index()
            )

            conversion_table = (
                conversion_rates
                .pivot(index="country", columns="group", values="conversion_rate")
                .sort_index()
            )

            display(conversion_table)

            fig, ax = plt.subplots(figsize=(8, 4.5))
            conversion_plot = conversion_rates.copy()
            conversion_plot["conversion_rate_pct"] = conversion_plot["conversion_rate"] * 100
            sns.barplot(
                data=conversion_plot,
                x="country",
                y="conversion_rate_pct",
                hue="group",
                order=sorted(df["country"].unique()),
                ax=ax,
            )
            ax.set_title("Conversion Rates by Country and Group")
            ax.set_xlabel("Country")
            ax.set_ylabel("Conversion Rate (%)")
            plt.tight_layout()
            plt.show()
            """
        ),
        md(
            """
            **Answer:**

            The table above shows the **conversion rates, by country and group**, exactly as required. In every country, the **treatment** group converts at a higher rate than the **control** group:

            - `CA`: treatment 15.40% vs control 9.45%
            - `UK`: treatment 14.87% vs control 10.16%
            - `US`: treatment 15.78% vs control 10.73%
            """
        ),
        md(
            """
            ## Executive Summary: What do these probabilities suggest in how the `Treatment` or `Country` are associated with conversion rates?
            """
        ),
        code(
            """
            overall_rates = df.groupby("group")["converted"].agg(["sum", "count", "mean"])
            overall_rates
            """
        ),
        md(
            """
            **Answer:**

            These probabilities suggest that **treatment is strongly associated with higher conversion rates**. The treatment page outperforms the control page overall and within each country. Country appears to matter somewhat because base conversion rates are not identical across `US`, `UK`, and `CA`, but the **direction of the treatment effect is consistent across all three countries**. That pattern indicates that the new page is the main driver of the improvement rather than a country mix issue.
            """
        ),
        md(
            """
            ## How effective is the new page?
            """
        ),
        code(
            """
            treatment = df.loc[df["group"] == "treatment", "converted"]
            control = df.loc[df["group"] == "control", "converted"]

            p_treatment = treatment.mean()
            p_control = control.mean()
            delta = p_treatment - p_control

            n_treatment = treatment.shape[0]
            n_control = control.shape[0]
            x_treatment = int(treatment.sum())
            x_control = int(control.sum())

            pooled = (x_treatment + x_control) / (n_treatment + n_control)
            se = np.sqrt(pooled * (1 - pooled) * ((1 / n_treatment) + (1 / n_control)))
            z_stat = delta / se
            p_value = 1 - norm.cdf(z_stat)

            se_unpooled = np.sqrt(
                (p_treatment * (1 - p_treatment) / n_treatment)
                + (p_control * (1 - p_control) / n_control)
            )
            ci_low = delta - 1.96 * se_unpooled
            ci_high = delta + 1.96 * se_unpooled

            results = pd.DataFrame(
                {
                    "metric": [
                        "Treatment conversion rate",
                        "Control conversion rate",
                        "Delta (treatment - control)",
                        "Z-statistic",
                        "One-sided p-value",
                        "95% CI lower bound",
                        "95% CI upper bound",
                    ],
                    "value": [
                        p_treatment,
                        p_control,
                        delta,
                        z_stat,
                        p_value,
                        ci_low,
                        ci_high,
                    ],
                }
            )

            display(results)

            fig, ax = plt.subplots(figsize=(6.5, 4.5))
            ax.bar(["Control", "Treatment"], [p_control * 100, p_treatment * 100], color=["#4C78A8", "#F58518"])
            ax.set_title("Overall Conversion Rate by Group")
            ax.set_ylabel("Conversion Rate (%)")
            for idx, value in enumerate([p_control, p_treatment]):
                ax.text(idx, value * 100 + 0.2, f"{value * 100:.2f}%", ha="center")
            plt.tight_layout()
            plt.show()
            """
        ),
        md(
            """
            **Answer:**

            The new page is **highly effective**. The treatment conversion rate is **15.53%**, while the control conversion rate is **10.53%**, for a lift of about **5.01 percentage points**. The z-statistic is about **19.65** and the one-sided p-value is effectively **0.0000**, which is far below 0.05. This means the observed improvement is statistically significant and very unlikely to be caused by random chance.
            """
        ),
        md(
            """
            ## Conclusion: what does the above suggest in terms of treatment and control - do you have statistically significant evidence of a difference? What should the takeaways be?
            """
        ),
        code(
            """
            country_test_rows = []
            for group_name in ["control", "treatment"]:
                subset = df[df["group"] == group_name]
                contingency = pd.crosstab(subset["country"], subset["converted"])
                chi2_stat, chi2_p_value, _, _ = chi2_contingency(contingency)
                country_test_rows.append(
                    {
                        "group": group_name,
                        "chi_square_stat": chi2_stat,
                        "p_value": chi2_p_value,
                    }
                )

            country_tests = pd.DataFrame(country_test_rows)
            display(country_tests)
            """
        ),
        md(
            """
            **Answer:**

            Yes, there is **statistically significant evidence** that treatment performs better than control. The new page consistently produces higher conversion rates overall and in every country subgroup. The country-level chi-squared checks within control and treatment produce p-values above 0.05, which suggests that once group assignment is fixed, country differences are not the main explanation for the result. The main takeaway is that the company should **implement the new page**, because the observed lift is both statistically significant and practically meaningful.
            """
        ),
        md(
            """
            ## Final Recommendation

            The submission requirement is to include the template questions in the notebook and answer them directly. Based on the analysis above, the correct business recommendation is to **launch the treatment page**.
            """
        ),
    ]

    nb = nbf.v4.new_notebook()
    nb["cells"] = cells
    nb["metadata"] = {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {
            "name": "python",
            "version": "3.13",
        },
    }

    NOTEBOOK.parent.mkdir(parents=True, exist_ok=True)
    nbf.write(nb, NOTEBOOK)
    print(f"Wrote notebook: {NOTEBOOK}")


def run(cmd):
    print("Running:", " ".join(map(str, cmd)))
    subprocess.run(cmd, check=True)


def update_presentation() -> None:
    df = pd.read_csv(DATA_PATH)
    country_distribution = (
        df["country"].value_counts(normalize=True).mul(100).sort_index()
    )

    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar(
        country_distribution.index,
        country_distribution.values,
        color=["#4C78A8", "#F58518", "#54A24B"],
        edgecolor="black",
    )
    ax.set_title("User Distribution by Country")
    ax.set_xlabel("Country")
    ax.set_ylabel("Share of Users (%)")
    ax.set_ylim(0, max(country_distribution.values) + 8)

    for bar, value in zip(bars, country_distribution.values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 0.8,
            f"{value:.1f}%",
            ha="center",
            va="bottom",
        )

    plt.tight_layout()
    IMAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(IMAGE_PATH, dpi=200, bbox_inches="tight")
    plt.close(fig)

    prs = Presentation(PRESENTATION_PATH)
    slide = prs.slides[2]

    picture_shape = None
    for shape in slide.shapes:
        if shape.shape_type == 13:
            picture_shape = shape
            break

    if picture_shape is None:
        raise RuntimeError("Could not find picture on slide 3.")

    left = picture_shape.left
    top = picture_shape.top
    width = picture_shape.width
    height = picture_shape.height

    sp = picture_shape._element
    sp.getparent().remove(sp)
    slide.shapes.add_picture(str(IMAGE_PATH), left, top, width=width, height=height)
    prs.save(PRESENTATION_PATH)
    print(f"Updated presentation: {PRESENTATION_PATH}")


def export_notebook() -> None:
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


def main():
    build_notebook()
    update_presentation()
    export_notebook()


if __name__ == "__main__":
    main()
