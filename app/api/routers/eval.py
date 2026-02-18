"""RAGAS evaluation API: run evaluation and fetch report for dashboard."""

import json
import os
import tempfile
from pathlib import Path

import structlog
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.eval.run_eval import run_evaluation

router = APIRouter()
logger = structlog.get_logger()

EVAL_REPORT_PATH = Path(os.environ.get("EVAL_REPORT_PATH", "/app/eval_report.json"))
DEFAULT_QUESTION_PATH = Path(os.environ.get("EVAL_DATASET_PATH", "/app/question_list.pdf"))


@router.get("/eval/report")
def get_eval_report():
    """Return the last saved RAGAS evaluation report (for dashboard)."""
    if not EVAL_REPORT_PATH.exists():
        raise HTTPException(404, "No evaluation report found. Run an evaluation first.")
    try:
        with open(EVAL_REPORT_PATH) as f:
            return json.load(f)
    except Exception as e:
        logger.error("eval_report_read_failed", path=str(EVAL_REPORT_PATH), error=str(e))
        raise HTTPException(500, "Failed to read report") from e


@router.post("/eval/run")
def run_eval(
    file: UploadFile | None = File(None),
    max_questions: int | None = None,
):
    """
    Run RAGAS evaluation. Optionally upload a question list (PDF or DOCX).
    If no file is provided, uses the default path (e.g. /app/question_list.pdf).
    max_questions: cap how many questions to use (reduces tokens / helps stay within HF free tier). Default from EVAL_MAX_QUESTIONS (20).
    Returns the evaluation report (metrics, question count). May take several minutes.
    """
    question_path: Path
    if file and file.filename:
        suf = Path(file.filename).suffix.lower()
        if suf not in (".pdf", ".docx", ".doc"):
            raise HTTPException(400, "Question list must be PDF or DOCX")
        content = file.file.read()
        try:
            fd, path = tempfile.mkstemp(suffix=suf)
            with os.fdopen(fd, "wb") as f:
                f.write(content)
            question_path = Path(path)
        except Exception as e:
            raise HTTPException(500, "Failed to save uploaded file") from e
        try:
            report = run_evaluation(question_path, report_path=EVAL_REPORT_PATH, max_questions=max_questions)
        except Exception as e:
            _handle_eval_error(e)
        finally:
            question_path.unlink(missing_ok=True)
    else:
        if not DEFAULT_QUESTION_PATH.exists():
            raise HTTPException(
                400,
                "No question list provided and default path not found. "
                "Upload a PDF/DOCX or mount question_list.pdf at /app/question_list.pdf",
            )
        question_path = DEFAULT_QUESTION_PATH
        try:
            report = run_evaluation(question_path, report_path=EVAL_REPORT_PATH, max_questions=max_questions)
        except Exception as e:
            _handle_eval_error(e)

    return report


def _handle_eval_error(e: Exception) -> None:
    """Re-raise as HTTPException with 402 for Payment Required, else 500."""
    logger.error("eval_run_failed", error=str(e))
    msg = str(e).lower()
    if "402" in msg or "payment required" in msg:
        raise HTTPException(
            402,
            "Hugging Face returned Payment Required (402). Free tier limit may be reached. Try reducing EVAL_MAX_QUESTIONS (default 20) or add credits at https://huggingface.co/settings/billing.",
        ) from e
    raise HTTPException(500, str(e)) from e
