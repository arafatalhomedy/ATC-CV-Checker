"""
scorer.py
---------
Combines all the individual checks (keyword match, section structure,
contact info, format risk) into one weighted ATS-strength score.

The weighting is a judgment call, not a reverse-engineered ATS formula -
real systems are proprietary and vary by vendor. This is a transparent,
tunable proxy: every component of the score is visible in the breakdown,
not hidden inside a black-box number.
"""

from dataclasses import dataclass
import numpy as np
import pandas as pd

try:
    # Used when the parser folder is imported as a package (from parser import ...)
    from .extract import extract_text, has_docx_tables
    from .sections import detect_sections, has_contact_info
    from .keywords import keyword_match_report, keyword_coverage_score, cosine_similarity_score
except ImportError:
    # Used when this file is run directly as a script (python scorer.py ...)
    from extract import extract_text, has_docx_tables
    from sections import detect_sections, has_contact_info
    from keywords import keyword_match_report, keyword_coverage_score, cosine_similarity_score

# Weights must sum to 1.0. Keyword match dominates because that's what
# most real ATS keyword-search behavior optimizes for.
WEIGHTS = {
    "keyword_coverage": 0.45,
    "cosine_similarity": 0.15,
    "section_completeness": 0.20,
    "contact_info": 0.10,
    "format_risk": 0.10,
}


@dataclass
class ATSReport:
    final_score: float
    component_scores: dict
    keyword_table: pd.DataFrame
    missing_sections: list
    format_warnings: list
    cv_text: str = ""
    jd_text: str = ""

    def summary(self) -> str:
        lines = [
            f"ATS Strength Score: {self.final_score:.0%}",
            "",
            "Breakdown:",
        ]
        for name, score in self.component_scores.items():
            weight_pct = WEIGHTS[name] * 100
            lines.append(f"  {name:22s} {score:>5.0%}  (weight {weight_pct:.0f}%)")

        if self.missing_sections:
            lines.append("")
            lines.append(f"Missing sections: {', '.join(self.missing_sections)}")

        if self.format_warnings:
            lines.append("")
            lines.append("Format warnings:")
            for w in self.format_warnings:
                lines.append(f"  - {w}")

        return "\n".join(lines)


def score_format_risk(filepath: str) -> tuple[float, list]:
    """
    Basic format-risk check. Returns (score 0-1, list of warning strings).
    1.0 = no detected format risks, lower = more risk.
    """
    warnings = []
    score = 1.0

    if has_docx_tables(filepath):
        warnings.append(
            "Resume uses tables for layout - some ATS parsers misread or "
            "drop text inside tables. Consider a single-column layout."
        )
        score -= 0.5

    return max(score, 0.0), warnings


def generate_ats_report(cv_filepath: str, jd_text: str) -> ATSReport:
    """
    Run the full pipeline: extract -> parse sections -> match keywords ->
    check format -> combine into a final weighted score.
    """
    cv_text = extract_text(cv_filepath)

    # Section / structure check
    section_report = detect_sections(cv_text)
    section_score = section_report.completeness_score

    # Contact info check
    contact = has_contact_info(cv_text)
    contact_score = np.mean([contact["has_email"], contact["has_phone"]])

    # Keyword matching
    match_df = keyword_match_report(cv_text, jd_text)
    coverage_score = keyword_coverage_score(match_df)
    cosine_score = cosine_similarity_score(cv_text, jd_text)

    # Format risk
    format_score, format_warnings = score_format_risk(cv_filepath)

    component_scores = {
        "keyword_coverage": coverage_score,
        "cosine_similarity": cosine_score,
        "section_completeness": section_score,
        "contact_info": float(contact_score),
        "format_risk": format_score,
    }

    # Weighted sum via NumPy - this is the actual "final percentage"
    scores_array = np.array([component_scores[k] for k in WEIGHTS])
    weights_array = np.array([WEIGHTS[k] for k in WEIGHTS])
    final_score = float(np.dot(scores_array, weights_array))

    return ATSReport(
        final_score=final_score,
        component_scores=component_scores,
        keyword_table=match_df,
        missing_sections=section_report.missing,
        format_warnings=format_warnings,
        cv_text=cv_text,
        jd_text=jd_text,
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python scorer.py <path_to_cv> <path_to_job_description.txt>")
        sys.exit(1)

    with open(sys.argv[2], "r", encoding="utf-8") as f:
        jd_text = f.read()

    report = generate_ats_report(sys.argv[1], jd_text)
    print(report.summary())
    print("\nKeyword detail:")
    print(report.keyword_table.to_string(index=False))
