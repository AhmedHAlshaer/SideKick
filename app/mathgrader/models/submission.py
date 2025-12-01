"""
Submission Data Models

These models define student submissions - what students write as answers.

🎓 LEARNING CONCEPT: "Input Models vs Business Models"
------------------------------------------------------
We have two types of models:

1. **Business Models** (Rubric) - The "ideal" structure
   - Clean, well-defined
   - Everything in the right place
   
2. **Input Models** (Submission) - The "messy reality"
   - Students make typos
   - Formatting varies
   - Answers might be missing
   - Need to handle ambiguity

Submission models need to be MORE flexible than Rubric models!

🔑 KEY INSIGHT: Confidence Scores
---------------------------------
When parsing student PDFs, we might not be 100% sure what they wrote.
Maybe they wrote "1 / 4" or "1/4" or "one fourth".

We store:
- raw_text: Exactly what they wrote
- parsed_value: Our best guess at what they meant
- confidence: How sure we are (0.0 to 1.0)

If confidence is low, we flag for manual review!
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ============================================================================
# STUDENT ANSWER
# ============================================================================

class StudentAnswer(BaseModel):
    """
    A single answer from a student.
    
    🎓 CONCEPT: Parsing Uncertainty
    -------------------------------
    Student PDFs are messy. They might write:
    - "1/4" ← clear
    - "1 / 4" ← needs normalization
    - "1 over 4" ← needs interpretation
    - "0.25" ← mathematically equivalent
    - "thirteen fifty-seconds" ← WTF?
    
    We handle this with a two-stage approach:
    1. Extract raw text (what they literally wrote)
    2. Parse to normalized form (what we think they meant)
    3. Store confidence (how sure we are)
    
    Example:
        raw_text: "1 / 4"
        parsed_value: "1/4"
        confidence: 0.95
    
    vs:
        raw_text: "one divided by four"
        parsed_value: "1/4"
        confidence: 0.70  ← Less confident, flag for review
    """
    
    # Which question this answers (e.g., "1a", "2b")
    question_id: str = Field(description="Question identifier (e.g., '1a')")
    
    # Exactly what the student wrote (unmodified)
    raw_text: str = Field(description="Raw text from PDF")
    
    # Our normalized interpretation
    parsed_value: Optional[str] = Field(
        default=None,
        description="Parsed/normalized answer"
    )
    
    # How confident we are in the parsing (0.0 to 1.0)
    confidence: float = Field(
        default=1.0,
        ge=0.0,  # Greater than or equal to 0
        le=1.0,  # Less than or equal to 1
        description="Parsing confidence (0.0 to 1.0)"
    )
    
    # 🎓 PYDANTIC FEATURE: Validation Constraints
    # ge=0.0, le=1.0 ensures confidence is always between 0 and 1
    # If you try: StudentAnswer(confidence=1.5)
    # Pydantic raises: ValidationError: confidence must be <= 1.0
    
    # Optional notes about parsing issues
    parsing_notes: Optional[str] = Field(
        default=None,
        description="Notes about any parsing ambiguities"
    )


# ============================================================================
# SUBMISSION
# ============================================================================

class Submission(BaseModel):
    """
    A complete student submission.
    
    🎓 CONCEPT: Mapping Answers to Questions
    ----------------------------------------
    Challenge: Student PDFs don't always follow a clean format.
    They might:
    - Skip questions
    - Answer out of order
    - Put multiple answers on one line
    
    Our job: Extract answers and map them to question IDs.
    
    Example mapping:
        "1a. True"  → StudentAnswer(question_id="1a", raw_text="True", ...)
        "1b) F"     → StudentAnswer(question_id="1b", raw_text="F", ...)
        "1c: 0.25"  → StudentAnswer(question_id="1c", raw_text="0.25", ...)
    
    We use a List[StudentAnswer] instead of Dict because:
    - Preserves order (might be useful)
    - Can handle duplicate answers (student changed their mind)
    - More flexible for iteration
    """
    
    # Student identifier (could be name, ID, email, etc.)
    student_id: str = Field(description="Student identifier")
    
    # Optional student name
    student_name: Optional[str] = Field(
        default=None,
        description="Student's full name"
    )
    
    # Which assignment this is for
    assignment_id: str = Field(description="Assignment identifier (e.g., 'HW10')")
    
    # Path to the PDF file
    file_path: str = Field(description="Path to submission PDF")
    
    # All the student's answers
    answers: List[StudentAnswer] = Field(
        default_factory=list,
        description="List of all student answers"
    )
    
    # When they submitted (if available)
    submission_time: Optional[datetime] = Field(
        default=None,
        description="Submission timestamp"
    )
    
    # 🎓 CONCEPT: Helper Methods
    # --------------------------
    # Pydantic models can have methods! Let's add helpful utilities:
    
    def get_answer(self, question_id: str) -> Optional[StudentAnswer]:
        """
        Find the answer for a specific question.
        
        Args:
            question_id: Question to find (e.g., "1a")
            
        Returns:
            StudentAnswer if found, None otherwise
            
        🎓 WHY THIS IS USEFUL:
        Instead of:
            answer = next((a for a in submission.answers if a.question_id == "1a"), None)
        
        We can do:
            answer = submission.get_answer("1a")
        
        Much cleaner!
        """
        for answer in self.answers:
            if answer.question_id == question_id:
                return answer
        return None
    
    def has_answer(self, question_id: str) -> bool:
        """
        Check if student answered a question.
        
        Args:
            question_id: Question to check
            
        Returns:
            True if student provided an answer, False otherwise
        """
        return self.get_answer(question_id) is not None
    
    def get_low_confidence_answers(self, threshold: float = 0.8) -> List[StudentAnswer]:
        """
        Get all answers below a confidence threshold.
        
        These should be flagged for manual review.
        
        Args:
            threshold: Confidence threshold (default 0.8)
            
        Returns:
            List of answers with low confidence
            
        🎓 CONCEPT: Quality Assurance
        We don't want to auto-grade things we're not confident about.
        This method helps us find answers that need human review.
        """
        return [
            answer for answer in self.answers 
            if answer.confidence < threshold
        ]
    
    def answer_count(self) -> int:
        """Get total number of answers provided."""
        return len(self.answers)
    
    # 🎓 PYDANTIC FEATURE: Custom Validation
    # We can add validators to ensure data integrity
    
    from pydantic import field_validator
    
    @field_validator('student_id')
    @classmethod
    def student_id_not_empty(cls, v: str) -> str:
        """Ensure student ID is not empty."""
        if not v or not v.strip():
            raise ValueError("student_id cannot be empty")
        return v.strip()
    
    # This runs automatically when creating a Submission:
    # Submission(student_id="  ") → ValidationError!
    # Submission(student_id=" ABC ") → student_id="ABC" (stripped)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "StudentAnswer",
    "Submission"
]


# 🎓 SUMMARY: Submission Models
# ==============================
#
# StudentAnswer:
# - question_id: Which question
# - raw_text: What they literally wrote
# - parsed_value: Our interpretation
# - confidence: How sure we are
#
# Submission:
# - student_id: Who submitted it
# - answers: List of all answers
# - Helper methods: get_answer(), has_answer(), etc.
#
# KEY INSIGHT: Submissions are MESSY
# We model uncertainty explicitly with confidence scores!
#
# NEXT: Build GradeResult model (the output of grading)

