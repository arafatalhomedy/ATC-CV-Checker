"""
app.py
------
Flask API for the CV/ATS Checker.

Endpoints:
  GET  /api/health   - simple health check
  POST /api/analyze  - upload a CV (multipart) + job description (text),
                        returns the full ATS report as JSON
  POST /api/optimize - upload a CV (multipart) + job description (text),
                        returns an ATS-optimized plain-text resume

No external CORS package is used (kept dependency-free); CORS headers
are set manually in `add_cors_headers` below so this works with any
frontend dev server (Vite, CRA, etc.) without extra installs.
"""

import os
import tempfile
import traceback

from flask import Flask, request, jsonify, Response

from parser.scorer import generate_ats_report
from parser.extract import UnsupportedFileType, extract_text
from parser.suggestions import generate_suggestions, generate_optimized_resume

app = Flask(__name__)

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_FILE_SIZE_MB = 5

app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE_MB * 1024 * 1024


@app.after_request
def add_cors_headers(response):
    """Allow the React dev server (or any origin) to call this API."""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


def _validate_upload(req):
    """
    Common validation for both /analyze and /optimize.
    Returns (cv_file, job_description, error_response).
    If error_response is not None, the caller should return it immediately.
    """
    if "cv" not in req.files:
        return None, None, (jsonify({"error": "No CV file uploaded. Expected a 'cv' file field."}), 400)

    cv_file = req.files["cv"]
    job_description = req.form.get("job_description", "").strip()

    if cv_file.filename == "":
        return None, None, (jsonify({"error": "No file selected."}), 400)

    if not job_description:
        return None, None, (jsonify({"error": "Job description text is required."}), 400)

    ext = os.path.splitext(cv_file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return None, None, (jsonify({
            "error": f"Unsupported file type '{ext}'. Please upload a .pdf or .docx file."
        }), 400)

    return cv_file, job_description, None


@app.route("/api/analyze", methods=["POST", "OPTIONS"])
def analyze():
    # Browsers send an OPTIONS preflight request before the real POST
    # for multipart requests with custom headers - just acknowledge it.
    if request.method == "OPTIONS":
        return "", 204

    cv_file, job_description, err = _validate_upload(request)
    if err:
        return err

    ext = os.path.splitext(cv_file.filename)[1].lower()

    # Save to a temp file since our parser functions work off filepaths
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        cv_file.save(tmp.name)
        tmp_path = tmp.name

    try:
        report = generate_ats_report(tmp_path, job_description)

        # Generate improvement suggestions
        suggestions = generate_suggestions(report)

        response_data = {
            "final_score": round(report.final_score, 4),
            "component_scores": {
                k: round(v, 4) for k, v in report.component_scores.items()
            },
            "missing_sections": report.missing_sections,
            "format_warnings": report.format_warnings,
            "keyword_table": report.keyword_table.to_dict(orient="records"),
            "suggestions": suggestions,
        }
        return jsonify(response_data)

    except UnsupportedFileType as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        # Log full traceback server-side for debugging, but keep the
        # client-facing error message generic.
        traceback.print_exc()
        return jsonify({"error": "Failed to analyze the CV. Please check the file and try again."}), 500
    finally:
        os.unlink(tmp_path)


@app.route("/api/optimize", methods=["POST", "OPTIONS"])
def optimize():
    if request.method == "OPTIONS":
        return "", 204

    cv_file, job_description, err = _validate_upload(request)
    if err:
        return err

    ext = os.path.splitext(cv_file.filename)[1].lower()

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        cv_file.save(tmp.name)
        tmp_path = tmp.name

    try:
        cv_text = extract_text(tmp_path)
        optimized = generate_optimized_resume(cv_text, job_description)

        return Response(
            optimized,
            mimetype="text/plain",
            headers={"Content-Disposition": "attachment; filename=optimized_resume.txt"},
        )

    except UnsupportedFileType as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Failed to optimize the CV. Please try again."}), 500
    finally:
        os.unlink(tmp_path)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
