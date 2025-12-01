"""
MathGrader Tools for Sidekick.

Integrates the grading engine with the chat interface.
"""

from langchain_core.tools import StructuredTool, Tool
from pydantic import BaseModel, Field
from typing import Optional
import os

from .grading.grading_engine import GradingEngine
from .parsers.rubric_parser import RubricParser
from .parsers.submission_parser import SubmissionParser

# Global engine instance
_grading_engine: Optional[GradingEngine] = None
_rubric_parser = RubricParser()
_submission_parser = SubmissionParser()
_loaded_rubrics = {}

def get_engine() -> GradingEngine:
    global _grading_engine
    if _grading_engine is None:
        _grading_engine = GradingEngine()
    return _grading_engine

# --- Tool Functions ---

def load_rubric(rubric_path: str, rubric_name: str = "default") -> str:
    """Load and parse a grading rubric."""
    try:
        rubric = _rubric_parser.parse(rubric_path)
        _loaded_rubrics[rubric_name] = rubric
        
        return f"""✅ Rubric '{rubric_name}' loaded!
- Assignment: {rubric.assignment_id}
- Total Points: {rubric.total_points}
- Questions: {len(rubric.questions)}
"""
    except Exception as e:
        return f"❌ Error loading rubric: {str(e)}"

def grade_submission(submission_path: str, rubric_name: str = "default") -> str:
    """Grade a single submission."""
    if rubric_name not in _loaded_rubrics:
        return f"❌ Rubric '{rubric_name}' not loaded. Load it first."
    
    try:
        rubric = _loaded_rubrics[rubric_name]
        submission = _submission_parser.parse(submission_path, rubric)
        engine = get_engine()
        result = engine.grade(submission, rubric)
        
        return result.to_student_report()
        
    except Exception as e:
        return f"❌ Error grading: {str(e)}"

def grade_batch(submissions_folder: str, rubric_name: str = "default") -> str:
    """Grade all PDFs in a folder."""
    if rubric_name not in _loaded_rubrics:
        return f"❌ Rubric '{rubric_name}' not loaded."
    
    try:
        rubric = _loaded_rubrics[rubric_name]
        submissions = _submission_parser.parse_batch(submissions_folder, rubric)
        engine = get_engine()
        results = engine.grade_batch(submissions, rubric)
        
        # Calculate stats
        scores = [r.percentage for r in results]
        avg = sum(scores) / len(scores) if scores else 0
        
        return f"""✅ Batch complete!
- Graded: {len(results)}
- Average: {avg:.1f}%
- Results saved to: grading_data/results/
"""
    except Exception as e:
        return f"❌ Error in batch: {str(e)}"

# --- Tool Definitions ---

def get_grading_tools():
    return [
        StructuredTool.from_function(
            func=load_rubric,
            name="load_rubric",
            description="Load a grading rubric from PDF. Args: rubric_path, rubric_name"
        ),
        StructuredTool.from_function(
            func=grade_submission,
            name="grade_submission",
            description="Grade a student PDF. Args: submission_path, rubric_name"
        ),
        StructuredTool.from_function(
            func=grade_batch,
            name="grade_batch",
            description="Grade folder of PDFs. Args: submissions_folder, rubric_name"
        )
    ]