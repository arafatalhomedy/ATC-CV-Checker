# CV Desk — ATS Readability Checker

A full-stack tool that checks a resume against a job description and
scores how well it would read to an ATS (Applicant Tracking System),
with a full transparent breakdown of the score.

**Backend:** Flask REST API (Python, NumPy, Pandas, scikit-learn)
**Frontend:** React (Vite) — drag-and-drop resume upload, live results

## Project structure

```
cv_ats_checker/
├── backend/
│   ├── app.py              # Flask API (POST /api/analyze, GET /api/health)
│   ├── parser/              # Core analysis engine
│   │   ├── extract.py       # PDF/DOCX text extraction
│   │   ├── sections.py      # Section + contact-info detection
│   │   ├── keywords.py      # Keyword matching (NumPy/Pandas/sklearn)
│   │   └── scorer.py        # Combines everything into the final score
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main layout + state
│   │   ├── api.js           # Calls the Flask backend
│   │   └── components/
│   │       ├── UploadPanel.jsx      # Drag-and-drop upload + JD textarea
│   │       ├── ScoreStamp.jsx       # The final % as a stamped badge
│   │       ├── BreakdownBars.jsx    # Weighted score breakdown
│   │       └── KeywordMargin.jsx    # Matched/missing keywords
│   └── package.json
└── sample_data/
    ├── sample_cv.docx
    └── sample_job_description.txt
```

## Running it

You need two terminals — one for the backend, one for the frontend.

### 1. Backend (Flask API)

```bash
cd backend
pip install -r requirements.txt
python app.py
```

Runs at `http://localhost:5000`. Confirm it's up:
```bash
curl http://localhost:5000/api/health
```

### 2. Frontend (React)

```bash
cd frontend
npm install
npm run dev
```

Runs at `http://localhost:5173` — open that in your browser.

> **Note:** I built and tested the Flask backend directly in this
> environment (it works end-to-end against the sample data). I could
> **not** run `npm install` here since this sandbox has no network
> access — so the React side is written and syntax-checked but not
> build-verified. If `npm run dev` throws an error, paste it back to me
> and I'll fix it immediately.

## How it works

1. You drop a resume (PDF/DOCX) and paste a job description into the React app
2. The frontend sends both to the Flask API as a multipart POST
3. The backend extracts text, detects resume sections, matches keywords
   against the job description (NumPy/Pandas/scikit-learn), and checks
   for format risks (like tables that trip up real ATS parsers)
4. The API returns a JSON report; the frontend renders it as:
   - A stamped percentage score (green/amber/red by strength)
   - A weighted breakdown bar per scoring component
   - Keyword "margin notes" — highlighted matches, struck-through misses

## API reference

**POST** `/api/analyze`
Multipart form fields: `cv` (file), `job_description` (text)

```json
{
  "final_score": 0.6138,
  "component_scores": {
    "keyword_coverage": 0.4333,
    "cosine_similarity": 0.4588,
    "section_completeness": 0.75,
    "contact_info": 1.0,
    "format_risk": 1.0
  },
  "missing_sections": ["contact"],
  "format_warnings": [],
  "keyword_table": [
    { "keyword": "python", "jd_frequency": 3, "found_in_cv": true },
    { "keyword": "design", "jd_frequency": 3, "found_in_cv": false }
  ]
}
```

## Known limitations

- Not a reverse-engineered real ATS algorithm — a transparent proxy
  for keyword/structure matching (see notes in `backend/parser/scorer.py`)
- No OCR for scanned/image-based PDFs
- Table-layout risk detection is DOCX-only for now
- Frontend hardcodes `http://localhost:5000` as the API base — fine for
  local dev, would need an env variable for deployment

## Next steps worth considering

- Deploy: Flask behind gunicorn, React build served via nginx or Vercel
- Add a loading skeleton instead of the plain "…" placeholder
- Persist past checks (SQLite) so you can compare resume versions over time
- Add the job-application-tracker feature and link each tracked
  application to its own ATS check
