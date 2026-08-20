"""
keywords.py
-----------
Compares a CV against a job description and scores keyword overlap.

This is the core "ATS-style" matching logic: most real ATS platforms
score resumes primarily by how well they match keywords/skills found
in the job description, so this is the highest-weighted piece of the
final score.

Uses:
- scikit-learn's CountVectorizer to tokenize + build word-frequency vectors
- NumPy for the cosine similarity math and array operations
- Pandas to produce a readable matched/missing keyword breakdown
"""

import re
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer

# Generic words that show up in both CVs and JDs but carry no real signal.
# Kept small and explicit rather than pulling in a huge NLTK stopword list,
# since resumes/JDs use a fairly narrow vocabulary of filler words.
CUSTOM_STOPWORDS = {
    "and", "or", "the", "a", "an", "to", "of", "in", "on", "for", "with",
    "is", "are", "as", "at", "by", "be", "will", "we", "you", "your",
    "our", "this", "that", "have", "has", "including", "etc", "including",
    "years", "year", "experience", "work", "working", "role", "team",
    "strong", "ability", "skills", "using", "use", "including",
}


def clean_and_tokenize(text: str) -> list[str]:
    """
    Lowercase, strip punctuation/numbers, and split into word tokens,
    removing stopwords and very short tokens.
    """
    text = text.lower()
    text = re.sub(r"[^a-z\s+#.]", " ", text)  # keep +/# for things like "C++", "C#"
    tokens = text.split()
    tokens = [t.strip(".") for t in tokens if len(t) > 1 and t not in CUSTOM_STOPWORDS]
    return tokens


def extract_keywords(jd_text: str, top_n: int = 30) -> pd.Series:
    """
    Extract the most frequent meaningful terms from a job description.
    Returns a Pandas Series of keyword -> frequency, sorted descending.
    """
    tokens = clean_and_tokenize(jd_text)
    if not tokens:
        return pd.Series(dtype=int)

    series = pd.Series(tokens)
    counts = series.value_counts()
    return counts.head(top_n)


def keyword_match_report(cv_text: str, jd_text: str, top_n: int = 30) -> pd.DataFrame:
    """
    Build a DataFrame showing each top JD keyword, its frequency in the JD,
    and whether it appears in the CV at all.
    """
    jd_keywords = extract_keywords(jd_text, top_n=top_n)
    cv_tokens = set(clean_and_tokenize(cv_text))

    rows = []
    for keyword, freq in jd_keywords.items():
        rows.append({
            "keyword": keyword,
            "jd_frequency": int(freq),
            "found_in_cv": keyword in cv_tokens,
        })

    df = pd.DataFrame(rows)
    return df


def cosine_similarity_score(cv_text: str, jd_text: str) -> float:
    """
    Compute cosine similarity between the CV and JD as whole documents,
    using a bag-of-words vector representation.

    This captures overall vocabulary overlap/weighting beyond just the
    top-N keyword list - e.g. it still rewards matching less common but
    relevant terms.

    Returns a float between 0.0 and 1.0.
    """
    cv_clean = " ".join(clean_and_tokenize(cv_text))
    jd_clean = " ".join(clean_and_tokenize(jd_text))

    if not cv_clean.strip() or not jd_clean.strip():
        return 0.0

    vectorizer = CountVectorizer()
    vectors = vectorizer.fit_transform([cv_clean, jd_clean]).toarray()

    cv_vector, jd_vector = vectors[0], vectors[1]

    # Cosine similarity = (A . B) / (||A|| * ||B||)
    dot_product = np.dot(cv_vector, jd_vector)
    norm_product = np.linalg.norm(cv_vector) * np.linalg.norm(jd_vector)

    if norm_product == 0:
        return 0.0

    return float(dot_product / norm_product)


def keyword_coverage_score(match_df: pd.DataFrame) -> float:
    """
    Simple, interpretable score: what fraction of top JD keywords
    actually appear in the CV. This is the number most people intuitively
    expect when they hear "keyword match percentage".
    """
    if match_df.empty:
        return 0.0
    return float(match_df["found_in_cv"].mean())


if __name__ == "__main__":
    import sys
    from extract import extract_text

    if len(sys.argv) != 3:
        print("Usage: python keywords.py <path_to_cv> <path_to_job_description.txt>")
        sys.exit(1)

    cv_text = extract_text(sys.argv[1])
    with open(sys.argv[2], "r", encoding="utf-8") as f:
        jd_text = f.read()

    report = keyword_match_report(cv_text, jd_text)
    coverage = keyword_coverage_score(report)
    cosine = cosine_similarity_score(cv_text, jd_text)

    print(report.to_string(index=False))
    print(f"\nKeyword coverage: {coverage:.0%}")
    print(f"Cosine similarity: {cosine:.0%}")
