"""
Quick test for the rubric parser.

Run with: python test_rubric_parser.py
"""

from pathlib import Path
from app.mathgrader.parsers import RubricParser


def test_with_text():
    """Test parser with sample text (no PDF needed)."""
    parser = RubricParser()
    
    # Sample rubric text
    test_text = """
    CSCI-C241 Homework #10
    Give 18 points for completing the assignment.
    
    1. Deck of Cards (35 points)
    
    a) (5 points) Are S and H mutually exclusive?
    Answer: True
    Grading: +1 correct, -1 incorrect, minimum 0
    
    b) (5 points) Are S and K independent?
    Answer: False
    
    c) (5 points) Calculate P(H)
    Answer: 1/4
    
    2. Big-O Notation (10 points)
    
    What is the Big-O of f(n) = 25n! + n² + 2ⁿ?
    Answer: O(n!)
    
    3. Proof (10 points)
    
    Prove that there are infinitely many prime numbers.
    Grading: Partial credit allowed based on proof quality.
    """
    
    # Parse it
    rubric = parser._parse_rubric_text(test_text, "HW10_test")
    
    # Print results
    print("=" * 60)
    print("📋 RUBRIC PARSING TEST")
    print("=" * 60)
    print(f"\nAssignment: {rubric.assignment_id}")
    print(f"Base Points: {rubric.base_points}")
    print(f"Total Points: {rubric.total_points}")
    print(f"Questions: {len(rubric.questions)}\n")
    
    for q in rubric.questions:
        print(f"Question {q.number} ({q.total_points} pts)")
        print(f"  Sub-questions: {len(q.sub_questions)}")
        
        for sq in q.sub_questions:
            print(f"    {sq.id}: {sq.points} pts")
            print(f"       Type: {sq.question_type.value}")
            print(f"       Answer: {sq.solution.value}")
            print(f"       Grading: {sq.grading_rule.rule_type.value}")
        print()
    
    print("✅ Test passed!")


def test_with_real_pdf():
    """
    Test with your actual rubric PDF.
    
    UPDATE THIS PATH to your actual rubric file!
    """
    parser = RubricParser()
    
    # UPDATE THIS:
    rubric_path = Path("grading_data/rubrics/HW_10_rubric.pdf")
    
    if not rubric_path.exists():
        print(f"⚠️  Rubric not found at: {rubric_path}")
        print("   Update the path in test_with_real_pdf() function")
        return
    
    rubric = parser.parse(rubric_path)
    
    print("=" * 60)
    print("📋 REAL PDF PARSING TEST")
    print("=" * 60)
    print(f"\n✅ Successfully parsed: {rubric_path.name}")
    print(f"   Assignment: {rubric.assignment_id}")
    print(f"   Total Points: {rubric.total_points}")
    print(f"   Questions: {len(rubric.questions)}")


if __name__ == "__main__":
    print("\n🧪 Running parser tests...\n")
    
    # Test 1: With sample text
    test_with_text()
    
    print("\n" + "=" * 60)
    print("\n🧪 Testing with real PDF...\n")
    
    # Test 2: With real PDF (if you have one)
    test_with_real_pdf()