"""
Grade Result Data Models

These models define the OUTPUT of grading - scores, feedback, etc.

🎓 LEARNING CONCEPT: "Output Models"
------------------------------------
After we grade a submission, we need to:
1. Store the scores
2. Store feedback for the student
3. Store metadata for analytics
4. Flag items needing manual review

This model captures ALL of that in a structured way.

🔑 KEY DESIGN DECISION: Granular Feedback
-----------------------------------------
Instead of just storing a total score, we store:
- Per-question grades
- Per-question feedback
- What they answered vs what was correct
- Why points were deducted

This makes the grading TRANSPARENT and EDUCATIONAL for students!
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ============================================================================
# QUESTION GRADE
# ============================================================================

class QuestionGrade(BaseModel):
    """
    Grade for a single question/sub-question.
    
    🎓 CONCEPT: Granular Grading
    ----------------------------
    We don't just store "Question 1: 30/35"
    We store EACH sub-question:
    - 1a: 5/5 ✓
    - 1b: 3/5 ✗ (confused independence with mutual exclusivity)
    - 1c: 5/5 ✓
    - ...
    
    This lets us:
    1. Give specific feedback per question
    2. Track which questions are hardest
    3. Show students exactly where they lost points
    4. Generate analytics (which questions do students struggle with?)
    
    This is the SAME pattern Gradescope uses!
    """
    
    # Which question this grades
    question_id: str = Field(description="Question identifier (e.g., '1a')")
    
    # Points earned
    points_earned: float = Field(description="Points student earned")
    
    # Points possible
    points_possible: float = Field(description="Total points possible")
    
    # What the student answered
    student_answer: str = Field(description="Student's answer")
    
    # What the correct answer was
    correct_answer: str = Field(description="Correct answer")
    
    # Was it correct?
    is_correct: bool = Field(description="Whether answer was correct")
    
    # Feedback explaining the grade
    feedback: str = Field(description="Feedback for student")
    
    # Optional notes for TA review
    grading_notes: Optional[str] = Field(
        default=None,
        description="Internal notes (not shown to student)"
    )
    
    # 🎓 HELPER METHOD: Percentage
    def percentage(self) -> float:
        """Calculate percentage for this question."""
        if self.points_possible == 0:
            return 0.0
        return (self.points_earned / self.points_possible) * 100


# ============================================================================
# GRADE RESULT
# ============================================================================

class GradeResult(BaseModel):
    """
    Complete grading result for a submission.
    
    🎓 CONCEPT: Comprehensive Grading Output
    ----------------------------------------
    This is the FINAL OUTPUT of the grading process.
    
    It includes:
    1. Scores (total, per-question)
    2. Feedback (overall, per-question)
    3. Metadata (when graded, by what system)
    4. Quality flags (needs review?)
    
    This single object can be:
    - Sent to student (they see their grade + feedback)
    - Sent to TA (they review flagged items)
    - Exported to CSV (for gradebook)
    - Stored for analytics (which questions are hard?)
    
    🔑 DESIGN PATTERN: "Rich Domain Model"
    --------------------------------------
    Instead of just:
        {"student": "Ahmed", "score": 87}
    
    We have a RICH model with:
    - Detailed breakdown
    - Metadata
    - Helper methods
    - Validation
    
    This is how professional systems are built!
    """
    
    # ============= IDENTIFICATION =============
    
    submission_id: str = Field(
        description="Unique ID for this submission"
    )
    
    student_id: str = Field(
        description="Student identifier"
    )
    
    assignment_id: str = Field(
        description="Assignment identifier (e.g., 'HW10')"
    )
    
    # ============= SCORES =============
    
    total_score: float = Field(
        description="Total points earned (including base points)"
    )
    
    total_possible: float = Field(
        description="Total points possible"
    )
    
    percentage: float = Field(
        description="Percentage score (0-100)"
    )
    
    # ============= DETAILED BREAKDOWN =============
    
    question_grades: List[QuestionGrade] = Field(
        description="Grades for each question"
    )
    
    overall_feedback: str = Field(
        description="Summary feedback for student"
    )
    
    # ============= METADATA =============
    
    graded_at: datetime = Field(
        default_factory=datetime.now,
        description="When this was graded"
    )
    
    graded_by: str = Field(
        default="MathGrader AI",
        description="What/who graded this"
    )
    
    # ============= QUALITY ASSURANCE =============
    
    needs_review: bool = Field(
        default=False,
        description="Flag for manual TA review"
    )
    
    review_reasons: List[str] = Field(
        default_factory=list,
        description="Why manual review is needed"
    )
    
    # 🎓 CONCEPT: Quality Flags
    # -------------------------
    # We flag submissions for review when:
    # - Parsing confidence was low
    # - LLM gave uncertain grade
    # - Student answer was ambiguous
    # - Score is suspiciously high/low
    #
    # This keeps humans in the loop for edge cases!
    
    # ============= HELPER METHODS =============
    
    def letter_grade(self) -> str:
        """
        Calculate letter grade.
        
        Returns:
            Letter grade (A, B, C, D, F)
            
        🎓 CONCEPT: Derived Properties
        We could store this in the database, but better to calculate it.
        Why? If grading scale changes, we can recalculate automatically!
        """
        if self.percentage >= 90:
            return "A"
        elif self.percentage >= 80:
            return "B"
        elif self.percentage >= 70:
            return "C"
        elif self.percentage >= 60:
            return "D"
        else:
            return "F"
    
    def passed(self, passing_percentage: float = 60.0) -> bool:
        """
        Check if student passed.
        
        Args:
            passing_percentage: Minimum passing percentage (default 60%)
            
        Returns:
            True if passed, False otherwise
        """
        return self.percentage >= passing_percentage
    
    def incorrect_questions(self) -> List[QuestionGrade]:
        """Get all questions that were answered incorrectly."""
        return [qg for qg in self.question_grades if not qg.is_correct]
    
    def correct_questions(self) -> List[QuestionGrade]:
        """Get all questions that were answered correctly."""
        return [qg for qg in self.question_grades if qg.is_correct]
    
    def accuracy(self) -> float:
        """
        Calculate accuracy (% of questions correct).
        
        Returns:
            Percentage of questions answered correctly
            
        🎓 NOTE: Different from score percentage!
        - Score: Weighted by points
        - Accuracy: Simple count of correct answers
        """
        if not self.question_grades:
            return 0.0
        
        correct_count = len(self.correct_questions())
        total_count = len(self.question_grades)
        return (correct_count / total_count) * 100
    
    def to_gradebook_entry(self) -> dict:
        """
        Export as gradebook entry (for Canvas, etc.).
        
        Returns:
            Dict suitable for CSV export
            
        🎓 CONCEPT: Export Formats
        Different systems need different formats:
        - Canvas: Needs specific column names
        - Gradescope: Different format
        - Internal: Our rich format
        
        We keep ONE source of truth (GradeResult) and convert as needed!
        """
        return {
            "student_id": self.student_id,
            "assignment": self.assignment_id,
            "score": self.total_score,
            "possible": self.total_possible,
            "percentage": f"{self.percentage:.2f}%",
            "letter_grade": self.letter_grade(),
            "needs_review": "Yes" if self.needs_review else "No"
        }
    
    def to_student_report(self) -> str:
        """
        Generate human-readable report for student.
        
        Returns:
            Formatted string suitable for display
            
        🎓 CONCEPT: Multiple Representations
        The same data can be represented differently for different audiences:
        - Student: Focus on learning, feedback
        - TA: Focus on review flags, edge cases
        - Analytics: Focus on aggregate statistics
        """
        report = f"""
╔══════════════════════════════════════════════════════════╗
║                    GRADING REPORT                        ║
╚══════════════════════════════════════════════════════════╝

Assignment: {self.assignment_id}
Student: {self.student_id}
Graded: {self.graded_at.strftime('%Y-%m-%d %H:%M')}

─────────────────────────────────────────────────────────────
SCORE: {self.total_score}/{self.total_possible} ({self.percentage:.1f}%) - {self.letter_grade()}
─────────────────────────────────────────────────────────────

QUESTION BREAKDOWN:
"""
        for qg in self.question_grades:
            status = "✓" if qg.is_correct else "✗"
            report += f"\nQ{qg.question_id}: {status} {qg.points_earned}/{qg.points_possible}\n"
            report += f"  Your answer: {qg.student_answer}\n"
            
            if not qg.is_correct:
                report += f"  Correct answer: {qg.correct_answer}\n"
            
            report += f"  {qg.feedback}\n"
        
        report += f"\n{'─' * 61}\n"
        report += f"OVERALL FEEDBACK:\n{self.overall_feedback}\n"
        
        if self.needs_review:
            report += f"\n⚠️  This submission has been flagged for TA review.\n"
        
        return report
    
    # 🎓 PYDANTIC FEATURE: Custom Serialization
    class Config:
        """Model configuration."""
        # This makes datetime serialization work properly
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "QuestionGrade",
    "GradeResult"
]


# 🎓 SUMMARY: Grade Result Models
# ================================
#
# QuestionGrade:
# - Per-question scoring
# - Student answer vs correct answer
# - Specific feedback
#
# GradeResult:
# - Complete grading output
# - Scores + feedback
# - Quality assurance flags
# - Multiple export formats
# - Rich helper methods
#
# KEY INSIGHT: Don't just store a number!
# Store the WHY and the HOW so students can learn.
#
# This is the difference between:
#   "87/100" (not helpful)
# vs
#   "87/100: Great work on probability! Q1b: Remember that 
#    independence ≠ mutual exclusivity. See feedback above."
#
# NEXT: We have ALL our data models! Now we can build the parsers.

