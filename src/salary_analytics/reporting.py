"""Markdown, JSON, and headless Seaborn/Matplotlib chart reporting utilities."""

import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any

from salary_analytics.queries import SalaryAnalysisReport

logger = logging.getLogger(__name__)


def report_to_dict(report: SalaryAnalysisReport) -> dict[str, Any]:
    """Serialize ``SalaryAnalysisReport`` into plain JSON-compatible dictionaries."""
    return asdict(report)


def _format_markdown_table(heading: str, headers: tuple[str, ...], alignments: str, rows: list[str]) -> list[str]:
    """Render a reusable Markdown table block for a report section."""
    header_line = "| " + " | ".join(headers) + " |"
    return ["", heading, header_line, alignments, *rows]


def _build_section_tables(report: SalaryAnalysisReport) -> list[list[str]]:
    """Build formatted Markdown table blocks for all four business questions."""
    return [
        _format_markdown_table(
            "## 1. Salary Trend by Year",
            ("Year", "Avg Salary (USD)", "Min (USD)", "Max (USD)", "Samples"),
            "|---:|---:|---:|---:|---:|",
            [
                f"| {item.work_year} | ${item.avg_salary_usd:,.2f} | ${item.min_salary_usd:,} | "
                f"${item.max_salary_usd:,} | {item.sample_count} |"
                for item in report.yearly_trends
            ],
        ),
        _format_markdown_table(
            "## 2. Salary by Experience Level",
            ("Level", "Label", "Avg Salary (USD)", "Samples"),
            "|---|---|---:|---:|",
            [
                f"| {exp.experience_level} | {exp.experience_label} | ${exp.avg_salary_usd:,.2f} | {exp.sample_count} |"
                for exp in report.experience_breakdown
            ],
        ),
        _format_markdown_table(
            "## 3. Remote Ratio Comparison",
            ("Remote Ratio", "Work Mode", "Avg Salary (USD)", "Samples"),
            "|---:|---|---:|---:|",
            [
                f"| {rem.remote_ratio}% | {rem.work_mode} | ${rem.avg_salary_usd:,.2f} | {rem.sample_count} |"
                for rem in report.remote_breakdown
            ],
        ),
        _format_markdown_table(
            "## 4. Top Paying Roles",
            ("Job Title", "Avg Salary (USD)", "Max Salary (USD)", "Employees"),
            "|---|---:|---:|---:|",
            [
                f"| {role.job_title} | ${role.avg_salary_usd:,.2f} | ${role.max_salary_usd:,} | {role.employee_count} |"
                for role in report.top_roles
            ],
        ),
    ]


def format_report_markdown(report: SalaryAnalysisReport) -> str:
    """Render a structured Markdown executive summary from a salary analysis report.

    Args:
        report: Computed ``SalaryAnalysisReport``.

    Returns:
        Human-readable Markdown string summarizing all four business questions.
    """
    s = report.summary
    lines = [
        "# Data Science Salary Analysis Report",
        "",
        "## Dataset Overview",
        f"- **Records Analyzed**: {s.total_records:,}",
        f"- **Distinct Job Titles**: {s.distinct_roles:,}",
        f"- **Coverage Period**: {s.min_year} - {s.max_year}",
        f"- **Overall Average Salary**: ${s.overall_avg_salary_usd:,.2f}",
        f"- **Salary Range**: ${s.min_salary_usd:,} - ${s.max_salary_usd:,}",
    ]
    for table_lines in _build_section_tables(report):
        lines.extend(table_lines)
    return "\n".join(lines) + "\n"


def export_report_json(report: SalaryAnalysisReport, output_path: str | Path) -> Path:
    """Write ``SalaryAnalysisReport`` to disk as formatted JSON.

    Args:
        report: Computed ``SalaryAnalysisReport``.
        output_path: Destination JSON file path.

    Returns:
        Resolved output ``Path``.
    """
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = report_to_dict(report)
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    logger.info("Exported salary analysis JSON report to %s", target)
    return target


def _save_trend_chart(report: SalaryAnalysisReport, target_dir: Path, plt: Any, sns: Any, pd: Any) -> Path | None:
    """Render yearly average salary line chart when trend data is non-empty."""
    if not report.yearly_trends:
        return None
    trend_df = pd.DataFrame([asdict(x) for x in report.yearly_trends])
    out_path = target_dir / "salary_trend.png"
    fig, ax = plt.subplots(figsize=(10, 6))
    try:
        sns.lineplot(data=trend_df, x="work_year", y="avg_salary_usd", marker="o", linewidth=2.5, ax=ax)
        ax.set_title("Data Science Average Salary Trend")
        ax.set_xlabel("Year")
        ax.set_ylabel("Average Salary (USD)")
        ax.set_xticks(trend_df["work_year"].tolist())
        fig.tight_layout()
        fig.savefig(out_path, dpi=150)
    finally:
        plt.close(fig)
    return out_path


def _save_barplot(
    df: Any,
    *,
    x: str,
    y: str,
    hue: str,
    palette: str,
    title: str,
    xlabel: str,
    ylabel: str,
    figsize: tuple[int, int],
    out_path: Path,
    plt: Any,
    sns: Any,
) -> Path:
    """Render and close a Seaborn v0.14-compliant barplot cleanly."""
    fig, ax = plt.subplots(figsize=figsize)
    try:
        sns.barplot(data=df, x=x, y=y, hue=hue, palette=palette, legend=False, ax=ax)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        fig.tight_layout()
        fig.savefig(out_path, dpi=150)
    finally:
        plt.close(fig)
    return out_path


def _build_barplot_specs(report: SalaryAnalysisReport, pd: Any) -> list[tuple[Any, dict[str, Any]]]:
    """Assemble DataFrame and styling parameters for all categorical bar charts."""
    specs: list[tuple[Any, dict[str, Any]]] = []
    if report.experience_breakdown:
        specs.append(
            (
                pd.DataFrame([asdict(x) for x in report.experience_breakdown]),
                dict(
                    x="experience_level",
                    y="avg_salary_usd",
                    hue="experience_level",
                    palette="viridis",
                    title="Average Salary by Experience Level",
                    xlabel="Experience Level",
                    ylabel="Average Salary (USD)",
                    figsize=(10, 6),
                    filename="experience_salary.png",
                ),
            )
        )
    if report.remote_breakdown:
        rem_df = pd.DataFrame([asdict(x) for x in report.remote_breakdown])
        rem_df["remote_ratio_str"] = rem_df["remote_ratio"].astype(str)
        specs.append(
            (
                rem_df,
                dict(
                    x="remote_ratio_str",
                    y="avg_salary_usd",
                    hue="remote_ratio_str",
                    palette="magma",
                    title="Average Salary: WFO vs Hybrid vs Full Remote",
                    xlabel="Remote Ratio (%)",
                    ylabel="Average Salary (USD)",
                    figsize=(8, 5),
                    filename="remote_salary.png",
                ),
            )
        )
    if report.top_roles:
        specs.append(
            (
                pd.DataFrame([asdict(x) for x in report.top_roles]),
                dict(
                    x="avg_salary_usd",
                    y="job_title",
                    hue="job_title",
                    palette="coolwarm",
                    title="Top Paying Data Science Roles",
                    xlabel="Average Salary (USD)",
                    ylabel="",
                    figsize=(12, 6),
                    filename="top_roles.png",
                ),
            )
        )
    return specs


def generate_salary_charts(report: SalaryAnalysisReport, output_dir: str | Path) -> list[Path]:
    """Generate headless PNG charts using Seaborn v0.14-safe syntax.

    Args:
        report: Computed ``SalaryAnalysisReport``.
        output_dir: Directory where chart PNG files will be written.

    Returns:
        List of generated chart ``Path`` objects.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import pandas as pd
    import seaborn as sns

    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")
    generated: list[Path] = []

    trend_chart = _save_trend_chart(report, target_dir, plt, sns, pd)
    if trend_chart is not None:
        generated.append(trend_chart)

    for df, opts in _build_barplot_specs(report, pd):
        filename = opts.pop("filename")
        generated.append(_save_barplot(df, out_path=target_dir / filename, plt=plt, sns=sns, **opts))

    logger.info("Generated %d salary chart files in %s", len(generated), target_dir)
    return generated
