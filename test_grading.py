"""
Full integration test for the grading system.

Run with: python test_grading.py
"""

from datetime import datetime
from app.mathgrader.parsers import RubricParser
from app.mathgrader.grading import GradingEngine
from app.mathgrader.models.submission import Submission, StudentAnswer
from app.mathgrader.models.rubric import QuestionType


def test_full_pipeline():
    """Test the complete grading pipeline."""
    
    # 1. Parse a rubric (using test text)
    parser = RubricParser()
    test_rubric_text = """
    CSCI-C241 Homework #10
    Give 18 points for completing the assignment.
    
    1. Boolean Questions (10 points)
    
    a) (5 points) Is the sky blue?
    Answer: True
    Grading: +1 correct, -1 incorrect, minimum 0
    
    b) (5 points) Is water dry?
    Answer: False
    
    2. Math Questions (10 points)
    
    a) (5 points) What is 1/4 as a decimal?
    Answer: 0.25
    
    b) (5 points) What is 2 + 2?
    Answer: 4
    """
    
    rubric = parser._parse_rubric_text(test_rubric_text, "HW10_test")
    print(f"✅ Parsed rubric: {rubric.assignment_id}")
    print(f"   Total points: {rubric.total_points}")
    
    # 2. Create a mock submission
    submission = Submission(
        student_id="student_001",
        assignment_id=rubric.assignment_id,
        file_path="student_001.pdf",
        answers=[
            StudentAnswer(question_id="1a", raw_text="True", parsed_value="true", confidence=0.95),
            StudentAnswer(question_id="1b", raw_text="True", parsed_value="true", confidence=0.95),  # WRONG
            StudentAnswer(question_id="2a", raw_text="1/4", parsed_value="1/4", confidence=0.95),   # Equivalent!
            StudentAnswer(question_id="2b", raw_text="4", parsed_value="4", confidence=0.95),
        ],
        submission_time=datetime.now()
    )
    print(f"\n✅ Created submission for: {submission.student_id}")
    
    # 3. Grade it!
    engine = GradingEngine()
    result = engine.grade(submission, rubric)
    
    # 4. Print results
    print("\n" + "=" * 60)
    print("📊 GRADING RESULTS")
    print("=" * 60)
    print(f"\nStudent: {result.student_id}")
    print(f"Score: {result.total_score}/{result.total_possible}")
    print(f"Percentage: {result.percentage:.1f}%")
    print(f"Letter Grade: {result.letter_grade()}")
    
    print("\n📝 Question Breakdown:")
    for qg in result.question_grades:
        status = "✓" if qg.is_correct else "✗"
        print(f"   {qg.question_id}: {status} {qg.points_earned}/{qg.points_possible} pts")
        print(f"      {qg.feedback}")
    
    print("\n✅ Integration test passed!")


if __name__ == "__main__":
    test_full_pipeline()