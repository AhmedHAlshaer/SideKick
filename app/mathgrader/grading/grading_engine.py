"""
Grading Engine - Orchestrates the entire grading process.

🎓 THIS IS THE HEART OF THE SYSTEM:
-----------------------------------
It brings everything together:
1. Takes a rubric (correct answers)
2. Takes a submission (student answers)
3. Compares each answer
4. Applies grading rules
5. Produces a GradeResult

This is the "conductor" of the orchestra!
"""

from typing import List, Optional
from datetime import datetime

from ..models.rubric import Rubric, GradingRuleType
from ..models.submission import Submission
from ..models.grade_result import GradeResult, QuestionGrade
from .math_comparator import MathComparator


class GradingEngine:
    """
    Main grading engine that processes submissions against rubrics.
    
    🎓 CONCEPT: Pipeline Pattern
    ----------------------------
    This follows the "pipeline" pattern:
    
    Rubric + Submission → GradingEngine → GradeResult
    
    Each component has a single responsibility:
    - Rubric: Defines what's correct
    - Submission: Contains student answers
    - Engine: Compares them
    - Result: Contains grades + feedback
    
    Usage:
        engine = GradingEngine()
        result = engine.grade(submission, rubric)
        print(f"Score: {result.total_score}/{result.max_score}")
    """
    
    def __init__(self):
        """Initialize the grading engine."""
        self.comparator = MathComparator()
    
    def grade(self, submission: Submission, rubric: Rubric) -> GradeResult:
        """
        Grade a single submission against a rubric.
        
        Args:
            submission: Student's submission
            rubric: The grading rubric
            
        Returns:
            GradeResult with scores and feedback
        """
        question_grades = []
        total_score = rubric.base_points  # Start with base completion points
        
        # Grade each question
        for question in rubric.questions:
            for sub_q in question.sub_questions:
                # Find student's answer for this question
                student_answer = submission.get_answer(sub_q.id)
                
                # Grade it
                grade = self._grade_question(sub_q, student_answer, rubric)
                question_grades.append(grade)
                
                # Add to total (respecting minimum score rules)
                total_score += grade.points_earned
        
        # Apply global minimum if needed
        total_score = max(0, total_score)
        
        return GradeResult(
            student_id=submission.student_id,
            assignment_id=submission.assignment_id,
            submission_id=f"{submission.student_id}_{submission.assignment_id}",
            question_grades=question_grades,
            total_score=total_score,
            total_possible=rubric.total_points,
            percentage=(total_score / rubric.total_points) * 100 if rubric.total_points > 0 else 0,
            overall_feedback=self._generate_overall_feedback(question_grades),
            graded_at=datetime.now()
        )
    
    def grade_batch(
        self, 
        submissions: List[Submission], 
        rubric: Rubric
    ) -> List[GradeResult]:
        """
        Grade multiple submissions.
        
        🎓 CONCEPT: Batch Processing
        ----------------------------
        Process many submissions at once for efficiency.
        """
        results = []
        
        print(f"📝 Grading {len(submissions)} submissions...")
        
        for i, submission in enumerate(submissions, 1):
            print(f"  [{i}/{len(submissions)}] Grading {submission.student_id}...")
            result = self.grade(submission, rubric)
            results.append(result)
        
        print(f"✅ Graded {len(results)} submissions")
        return results
    
    # ========================================================================
    # QUESTION GRADING
    # ========================================================================
    
    def _grade_question(
        self, 
        sub_question, 
        student_answer, 
        rubric: Rubric
    ) -> QuestionGrade:
        """
        Grade a single question.
        
        🎓 FLOW:
        1. Check if answer exists
        2. Compare to correct answer
        3. Apply grading rules
        4. Generate feedback
        """
        # No answer provided
        if not student_answer or not student_answer.raw_text:
            return QuestionGrade(
                question_id=sub_question.id,
                points_earned=0,
                points_possible=sub_question.points,
                is_correct=False,
                student_answer="",
                correct_answer=sub_question.solution.value,
                feedback="No answer provided."
            )
        
        # Low confidence extraction - flag for review
        if student_answer.confidence < 0.5:
            return QuestionGrade(
                question_id=sub_question.id,
                points_earned=0,
                points_possible=sub_question.points,
                is_correct=False,
                student_answer=student_answer.raw_text,
                correct_answer=sub_question.solution.value,
                feedback="Could not reliably extract answer. Flagged for manual review.",
                grading_notes="Low confidence extraction"
            )
        
        # Compare answers
        is_correct, confidence = self.comparator.compare(
            student_answer.parsed_value,
            sub_question.solution.value,
            sub_question.question_type,
            sub_question.solution.equivalent_forms
        )
        
        # Low comparison confidence - flag for review
        grading_notes = None
        if confidence < 0.7:
            grading_notes = "Answer comparison uncertain"
        
        # Apply grading rules
        points = self._apply_grading_rule(
            is_correct, 
            sub_question.grading_rule,
            sub_question.points
        )
        
        # Generate feedback
        feedback = self._generate_feedback(
            is_correct,
            student_answer.parsed_value,
            sub_question.solution.value,
            sub_question.question_type
        )
        
        return QuestionGrade(
            question_id=sub_question.id,
            points_earned=points,
            points_possible=sub_question.points,
            is_correct=is_correct,
            student_answer=student_answer.parsed_value,
            correct_answer=sub_question.solution.value,
            feedback=feedback,
            grading_notes=grading_notes
        )
    
    def _apply_grading_rule(
        self, 
        is_correct: bool, 
        rule, 
        max_points: float
    ) -> float:
        """
        Apply grading rule to determine points.
        
        🎓 GRADING RULE TYPES:
        - NO_PARTIAL: All or nothing
        - PARTIAL_CREDIT: Can get partial (handled by LLM)
        - PER_ITEM_PENALTY: +1 correct, -1 wrong (for T/F)
        """
        if rule.rule_type == GradingRuleType.NO_PARTIAL:
            return max_points if is_correct else 0
        
        elif rule.rule_type == GradingRuleType.PER_ITEM_PENALTY:
            points = rule.points_correct if is_correct else rule.points_incorrect
            return max(rule.minimum_score, points)
        
        elif rule.rule_type == GradingRuleType.PARTIAL_CREDIT:
            # For now, treat as all-or-nothing
            # In the future, use LLM for partial credit
            return max_points if is_correct else 0
        
        else:
            return max_points if is_correct else 0
    
    def _generate_feedback(
        self, 
        is_correct: bool,
        student_answer: str,
        correct_answer: str,
        question_type
    ) -> str:
        """
        Generate helpful feedback for the student.
        
        🎓 CONCEPT: Educational Feedback
        --------------------------------
        Don't just say "wrong" - help them learn!
        """
        if is_correct:
            return "✓ Correct!"
        
        # For wrong answers, provide the correct one
        return f"✗ Incorrect. Your answer: {student_answer}. Correct answer: {correct_answer}"

    def _generate_overall_feedback(self, question_grades: List[QuestionGrade]) -> str:
        """Generate overall summary feedback."""
        incorrect = [qg for qg in question_grades if not qg.is_correct]
        if not incorrect:
            return "Excellent work! All answers are correct."
        
        feedback = "Overall good effort. Areas for improvement:\n"
        for qg in incorrect:
            feedback += f"- Question {qg.question_id}: {qg.feedback}\n"
        return feedback