"""
suggestions.py
--------------
Generates actionable improvement suggestions and an ATS-optimized
plain-text resume from the analysis report.

Key design constraint: the optimized resume only reorganises and
rephrases the user's *existing* content — it never fabricates skills,
experience or qualifications.
"""

import re
import textwrap

try:
    from .keywords import clean_and_tokenize, extract_keywords
    from .sections import SECTION_PATTERNS, EXPECTED_SECTIONS, detect_sections, has_contact_info
except ImportError:
    from keywords import clean_and_tokenize, extract_keywords
    from sections import SECTION_PATTERNS, EXPECTED_SECTIONS, detect_sections, has_contact_info


# ── Suggestions ──────────────────────────────────────────────────────

def generate_suggestions(report) -> list[dict]:
    """
    Produce a list of suggestion dicts from a completed ATSReport.
    Each dict has:
        category  – 'keywords' | 'structure' | 'format' | 'contact'
        text      – human-readable advice string
        priority  – 'high' | 'medium' | 'low'
    """
    suggestions: list[dict] = []

    # ── Keyword suggestions ──────────────────────────────────────
    missing_kws = [
        row for _, row in report.keyword_table.iterrows()
        if not row["found_in_cv"]
    ]
    found_kws = [
        row for _, row in report.keyword_table.iterrows()
        if row["found_in_cv"]
    ]

    if missing_kws:
        top_missing = [r["keyword"] for r in missing_kws[:5]]
        suggestions.append({
            "category": "keywords",
            "text": (
                f"Your resume is missing these important JD keywords: "
                f"{', '.join(top_missing)}. "
                f"If you have experience with any of them, weave them naturally "
                f"into your experience bullet points."
            ),
            "priority": "high",
        })

        # Check for near-matches (user might use a synonym / abbreviation)
        cv_tokens = set(clean_and_tokenize(report.cv_text))
        for row in missing_kws:
            kw = row["keyword"]
            # Look for partial overlap that could be a synonym
            close = [t for t in cv_tokens if kw in t or t in kw]
            if close:
                suggestions.append({
                    "category": "keywords",
                    "text": (
                        f"The JD uses '{kw}' but your resume has "
                        f"'{close[0]}'. Consider also using the exact "
                        f"term '{kw}' so ATS keyword filters pick it up."
                    ),
                    "priority": "medium",
                })

    coverage = report.component_scores.get("keyword_coverage", 0)
    if coverage < 0.5:
        suggestions.append({
            "category": "keywords",
            "text": (
                "Your keyword coverage is below 50%. Review the job description "
                "and mirror its exact terminology in your Skills and Experience sections."
            ),
            "priority": "high",
        })

    # ── Section structure ────────────────────────────────────────
    for section in report.missing_sections:
        suggestions.append({
            "category": "structure",
            "text": (
                f"Add a clearly labelled '{section.title()}' section. "
                f"ATS parsers look for standard headers to categorise your information."
            ),
            "priority": "high" if section in ("experience", "skills") else "medium",
        })

    section_score = report.component_scores.get("section_completeness", 0)
    if section_score < 1.0 and not report.missing_sections:
        suggestions.append({
            "category": "structure",
            "text": (
                "Your section headers may use non-standard names. "
                "Stick to common labels like 'Experience', 'Education', "
                "'Skills', 'Summary' for best ATS compatibility."
            ),
            "priority": "medium",
        })

    # ── Format ───────────────────────────────────────────────────
    for warning in report.format_warnings:
        suggestions.append({
            "category": "format",
            "text": warning,
            "priority": "medium",
        })

    format_score = report.component_scores.get("format_risk", 0)
    if format_score < 1.0 and not report.format_warnings:
        suggestions.append({
            "category": "format",
            "text": (
                "Your resume may have formatting elements that ATS parsers "
                "struggle with. Use a clean single-column layout with "
                "standard fonts."
            ),
            "priority": "medium",
        })

    # ── Contact info ─────────────────────────────────────────────
    contact = has_contact_info(report.cv_text)
    if not contact["has_email"]:
        suggestions.append({
            "category": "contact",
            "text": "No email address detected. Add a visible email so recruiters can reach you.",
            "priority": "high",
        })
    if not contact["has_phone"]:
        suggestions.append({
            "category": "contact",
            "text": "No phone number detected. Consider adding one for easier recruiter contact.",
            "priority": "medium",
        })

    # ── General tips based on overall score ───────────────────────
    if report.final_score >= 0.75:
        suggestions.append({
            "category": "keywords",
            "text": (
                "Great match! Fine-tune by quantifying achievements "
                "(e.g., 'Increased sales by 30%') to stand out after passing ATS."
            ),
            "priority": "low",
        })

    return suggestions


# ── Optimised resume builder ─────────────────────────────────────────

# Standard ATS-friendly section order
_SECTION_ORDER = [
    "contact", "summary", "skills", "experience",
    "education", "projects", "certifications",
]


def _extract_section_blocks(text: str) -> dict[str, str]:
    """
    Split the raw CV text into section blocks keyed by normalised
    section name (e.g. 'experience', 'skills').  Content that doesn't
    fall under any detected header is collected under '__preamble__'.
    """
    lines = text.split("\n")
    blocks: dict[str, list[str]] = {"__preamble__": []}
    current = "__preamble__"

    for line in lines:
        clean = line.strip()
        matched_section = None

        # Only treat short lines as potential headers
        if clean and len(clean.split()) <= 4:
            for section_name, patterns in SECTION_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, clean, re.IGNORECASE):
                        matched_section = section_name
                        break
                if matched_section:
                    break

        if matched_section:
            current = matched_section
            if current not in blocks:
                blocks[current] = []
            # Don't add the header line itself — we'll write our own
        else:
            if current not in blocks:
                blocks[current] = []
            blocks[current].append(line)

    # Clean up: strip leading/trailing blank lines from each block
    result = {}
    for key, block_lines in blocks.items():
        content = "\n".join(block_lines).strip()
        if content:
            result[key] = content

    return result


def _build_skills_section(cv_text: str, jd_text: str, existing_skills_block: str) -> str:
    """
    Build a skills section that lists the user's existing skills,
    reordered so JD-matching skills come first.
    """
    cv_tokens = set(clean_and_tokenize(cv_text))
    jd_keywords = extract_keywords(jd_text, top_n=30)

    # Skills the user has that match the JD
    matched_skills = [kw for kw in jd_keywords.index if kw in cv_tokens]
    # Remaining skills from the existing block
    if existing_skills_block:
        existing_tokens = clean_and_tokenize(existing_skills_block)
        other_skills = [t for t in dict.fromkeys(existing_tokens)
                        if t not in set(matched_skills)]
    else:
        other_skills = [t for t in cv_tokens if t not in set(matched_skills)]
        # Limit to reasonable set if no existing skills section
        other_skills = other_skills[:20]

    all_skills = matched_skills + other_skills
    if not all_skills:
        return ""

    # Format as comma-separated list
    return ", ".join(s.title() if len(s) > 2 else s.upper() for s in all_skills)


def _build_summary(cv_text: str, jd_text: str) -> str:
    """
    Build a brief professional summary that weaves in the user's
    JD-matched skills. Only uses terms actually found in the CV.
    """
    cv_tokens = set(clean_and_tokenize(cv_text))
    jd_keywords = extract_keywords(jd_text, top_n=15)
    matched = [kw for kw in jd_keywords.index if kw in cv_tokens]

    if not matched:
        return (
            "Experienced professional seeking to leverage a proven track "
            "record of delivering results in a challenging new role."
        )

    skill_list = ", ".join(s.title() if len(s) > 2 else s.upper() for s in matched[:8])
    return (
        f"Results-driven professional with demonstrated expertise in "
        f"{skill_list}. Proven ability to deliver impactful outcomes "
        f"aligned with organizational goals."
    )


def generate_optimized_resume(cv_text: str, jd_text: str) -> str:
    """
    Produce an ATS-optimized plain-text version of the CV.

    Rules:
    1. Uses standard section ordering.
    2. Adds missing section headers with content pulled from the CV.
    3. Reorders skills to prioritise JD matches.
    4. Generates a summary from existing matched skills.
    5. NEVER fabricates skills, experience, or qualifications.
    """
    blocks = _extract_section_blocks(cv_text)
    output_parts: list[str] = []

    # ── Contact / preamble (name, email, phone, etc.) ────────────
    preamble = blocks.get("__preamble__", "")
    contact_block = blocks.get("contact", "")
    header_text = "\n".join(filter(None, [preamble, contact_block])).strip()
    if header_text:
        output_parts.append(header_text)

    # ── Summary (generate if missing) ────────────────────────────
    if "summary" in blocks:
        output_parts.append("SUMMARY\n" + "=" * 40)
        output_parts.append(blocks["summary"])
    else:
        summary = _build_summary(cv_text, jd_text)
        output_parts.append("SUMMARY\n" + "=" * 40)
        output_parts.append(summary)

    # ── Skills (reorganised) ─────────────────────────────────────
    existing_skills = blocks.get("skills", "")
    skills_content = _build_skills_section(cv_text, jd_text, existing_skills)
    if skills_content:
        output_parts.append("SKILLS\n" + "=" * 40)
        output_parts.append(skills_content)

    # ── Remaining sections in standard order ─────────────────────
    for section in _SECTION_ORDER:
        if section in ("contact", "summary", "skills"):
            continue  # already handled
        if section in blocks:
            output_parts.append(
                f"{section.upper()}\n" + "=" * 40
            )
            output_parts.append(blocks[section])

    # ── Any extra sections not in our standard list ──────────────
    handled = set(_SECTION_ORDER) | {"__preamble__"}
    for section, content in blocks.items():
        if section not in handled:
            output_parts.append(
                f"{section.upper()}\n" + "=" * 40
            )
            output_parts.append(content)

    return "\n\n".join(output_parts) + "\n"
