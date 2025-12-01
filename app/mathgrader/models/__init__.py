"""
Data Models

🎓 CONCEPT: Package-Level Imports
---------------------------------
This __init__.py makes imports easier for users of our module.

Instead of:
    from mathgrader.models.rubric import Rubric, Question, Solution
    from mathgrader.models.submission import Submission
    from mathgrader.models.grade_result import GradeResult

Users can do:
    from mathgrader.models import Rubric, Submission, GradeResult

This is called a "barrel export" - collecting exports in one place.
"""

# Import from rubric.py
from .rubric import (
    GradingRuleType,
    GradingRule,
    Solution,
    SubQuestion,
    Question,
    Rubric
)

# Import from submission.py
from .submission import (
    StudentAnswer,
    Submission
)

# Import from grade_result.py
from .grade_result import (
    QuestionGrade,
    GradeResult
)

# Define what gets exported with "from mathgrader.models import *"
__all__ = [
    # Rubric models
    "GradingRuleType",
    "GradingRule",
    "Solution",
    "SubQuestion",
    "Question",
    "Rubric",
    
    # Submission models
    "StudentAnswer",
    "Submission",
    
    # Result models
    "QuestionGrade",
    "GradeResult",
]
