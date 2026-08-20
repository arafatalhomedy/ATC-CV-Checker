"""
sections.py
-----------
Detects standard resume sections (Experience, Education, Skills, etc.)
within the raw extracted text.

ATS systems rely heavily on recognizable section headers to correctly
parse a resume. Missing or non-standard headers is a common reason
resumes get misread.
"""

import re
from dataclasses import dataclass, field


# Common section names -> list of header variants an ATS/parser might expect.
# Keep these lowercase; matching is done case-insensitively.
SECTION_PATTERNS = {
    "contact": [r"contact", r"personal information"],
    "summary": [r"summary", r"objective", r"profile"],
    "experience": [r"experience", r"work history", r"employment history",
                   r"professional experience"],
    "education": [r"education", r"academic background"],
    "skills": [r"skills", r"technical skills", r"core competencies"],
    "projects": [r"projects", r"personal projects"],
    "certifications": [r"certifications", r"licenses"],
}

EXPECTED_SECTIONS = ["contact", "experience", "education", "skills"]


@dataclass
class SectionReport:
    found: dict = field(default_factory=dict)   # section_name -> matched header line
    missing: list = field(default_factory=list)  # section_names not found

    @property
    def completeness_score(self) -> float:
        """Fraction of EXPECTED_SECTIONS that were found, 0.0-1.0."""
        found_expected = [s for s in EXPECTED_SECTIONS if s in self.found]
        return len(found_expected) / len(EXPECTED_SECTIONS)


def detect_sections(text: str) -> SectionReport:
    """
    Scan text line-by-line for lines that look like section headers.
    A line is treated as a potential header if it's short (<=4 words)
    and matches one of our known patterns.
    """
    report = SectionReport()
    lines = text.split("\n")

    for line in lines:
        clean = line.strip()
        if not clean or len(clean.split()) > 4:
            continue  # skip empty lines or long lines (unlikely to be a header)

        for section_name, patterns in SECTION_PATTERNS.items():
            if section_name in report.found:
                continue  # already found this section
            for pattern in patterns:
                if re.search(pattern, clean, re.IGNORECASE):
                    report.found[section_name] = clean
                    break

    report.missing = [s for s in EXPECTED_SECTIONS if s not in report.found]
    return report


def has_contact_info(text: str) -> dict:
    """
    Look for an email address and phone number anywhere in the text.
    Many ATS systems require these to be plain text (not in headers/footers
    or images) to parse a candidate's contact info correctly.
    """
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    phone_pattern = r"(\+?\d{1,3}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}"

    return {
        "has_email": bool(re.search(email_pattern, text)),
        "has_phone": bool(re.search(phone_pattern, text)),
    }


if __name__ == "__main__":
    import sys
    from extract import extract_text

    if len(sys.argv) != 2:
        print("Usage: python sections.py <path_to_cv>")
        sys.exit(1)

    text = extract_text(sys.argv[1])
    report = detect_sections(text)
    contact = has_contact_info(text)

    print("Found sections:", list(report.found.keys()))
    print("Missing expected sections:", report.missing)
    print(f"Completeness score: {report.completeness_score:.0%}")
    print("Contact info detected:", contact)
