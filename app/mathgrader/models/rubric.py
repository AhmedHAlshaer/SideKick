"""
Rubric Data Models

These models define the STRUCTURE of a grading rubric.

🎓 LEARNING CONCEPT: "Data Models"
------------------------------------
Think of these as blueprints or schemas. They define:
- What fields exist (e.g., "points", "solution")
- What type each field is (string, int, float)
- What's required vs optional
- Validation rules

This is the FOUNDATION of your entire system. Get this right and
everything else becomes easier.

🔑 WHY PYDANTIC?
----------------
1. Type checking: Can't pass a string where you need a number
2. Validation: Ensures data is valid before processing
3. JSON export: Easy to save/load from files
4. IDE support: Your editor will autocomplete fields!

🏗️ ARCHITECTURE PATTERN: "Bottom-Up Modeling"
----------------------------------------------
We build from smallest → largest:
  Solution (single answer)
    ↓
  GradingRule (how to score it)
    ↓
  SubQuestion (1a, 1b, etc.)
    ↓
  Question (Question 1)
    ↓
  Rubric (entire assignment)

This is called "composition" - building complex things from simple pieces.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


# ============================================================================
# GRADING RULE TYPES
# ============================================================================
class QuestionType(Enum):
    """
    Types of questions we can grade.
    
    🎓 CONCEPT: Question-Specific Logic
    -----------------------------------
    Different question types need different grading approaches:
    - TRUE_FALSE: Exact match only
    - NUMERIC: Allow math equivalence
    - PROOF: Needs LLM grading
    - MULTIPLE_CHOICE: Exact match
    - SHORT_ANSWER: Fuzzy matching
    - GRAPHING: Manual review (can't auto-grade yet)
    """
    TRUE_FALSE = "true_false"
    NUMERIC = "numeric"
    PROBABILITY = "probability"
    BIG_O = "big_o"
    PROOF = "proof"
    MULTIPLE_CHOICE = "multiple_choice"
    SHORT_ANSWER = "short_answer"
    GRAPHING = "graphing"


class GradingRuleType(Enum):
    """
    Types of grading rules we support.
    
    🎓 CONCEPT: Enums (Enumerations)
    --------------------------------
    Enums are a set of named constants. Instead of using strings:
        rule_type = "exact_match"  # ❌ Could typo as "exact_matc"
    
    We use enums:
        rule_type = GradingRuleType.EXACT_MATCH  # ✅ IDE will catch typos
    
    Benefits:
    - No typos possible
    - IDE autocomplete
    - Self-documenting code
    """
    
    # Must match exactly (e.g., "True" != "true")
    EXACT_MATCH = "exact_match"
    
    # Math equivalence allowed (e.g., 1/4 == 0.25)
    EQUIVALENT = "equivalent"
    
    # +1 for correct, -1 for incorrect (like True/False questions)
    PER_ITEM_PENALTY = "per_item_penalty"
    
    # All or nothing - no partial credit
    NO_PARTIAL = "no_partial"
    
    # Partial credit allowed (for proofs, essays, etc.)
    PARTIAL_CREDIT = "partial_credit"


# ============================================================================
# GRADING RULE
# ============================================================================

class GradingRule(BaseModel):
    """
    How to score a question.
    
    🎓 CONCEPT: Grading Rules
    -------------------------
    Different questions need different scoring logic:
    
    Example 1: True/False with penalty
        - +1 for correct
        - -1 for incorrect
        - Minimum score of 0 (can't go negative)
    
    Example 2: Numerical answer
        - 5 points if correct
        - 0 points if wrong
        - No partial credit
    
    Example 3: Proof
        - 0-10 points based on quality
        - Partial credit allowed
    
    This model captures all those variations in a structured way.
    """
    
    # What type of grading logic to use
    rule_type: GradingRuleType
    
    # How many points if correct
    points_correct: float
    
    # How many points if incorrect (often negative for penalties)
    points_incorrect: float = 0
    
    # Minimum score (prevents negative totals)
    minimum_score: float = 0
    
    # Optional notes for edge cases
    notes: Optional[str] = None
    
    # 🎓 PYDANTIC TIP: Default values
    # Fields without defaults are REQUIRED
    # Fields with defaults are OPTIONAL


# ============================================================================
# SOLUTION
# ============================================================================

class Solution(BaseModel):
    """
    The correct answer(s) for a question.
    
    🎓 CONCEPT: Equivalent Forms
    ----------------------------
    Math has many ways to write the same thing:
        1/4 = 0.25 = 13/52 = 25/100
    
    We store:
    1. The "canonical" form (what rubric says): "1/4"
    2. Equivalent forms we know about: ["0.25", "13/52"]
    3. Explanation (for student feedback)
    
    Later, our MathComparator will check if student answer equals
    ANY of these forms (or is mathematically equivalent).
    """
    
    # The primary/canonical answer from rubric
    value: str = Field(description="The correct answer (e.g., '1/4', 'True', 'n!')")
    
    # Other acceptable forms (we'll learn more of these over time)
    equivalent_forms: List[str] = Field(
        default_factory=list,
        description="Other ways to write the same answer"
    )
    
    # Explanation for how to arrive at this answer
    explanation: Optional[str] = Field(
        default=None,
        description="How to solve this (for student feedback)"
    )
    
    # 🎓 PYDANTIC TIP: Field() for extra metadata
    # - description: Documents what this field means
    # - default_factory: For mutable defaults (lists, dicts)
    #   Never use default=[] in Pydantic! Use default_factory=list


# ============================================================================
# SUB-QUESTION
# ============================================================================

class SubQuestion(BaseModel):
    """
    A single sub-question (like "1a" or "1b").
    
    🎓 CONCEPT: Granular Modeling
    -----------------------------
    Instead of treating "Question 1" as one blob, we break it into
    sub-questions. This lets us:
    - Grade each part separately
    - Give specific feedback per part
    - Track which sub-questions students struggle with most
    
    This is called "granular modeling" - modeling at the most detailed level.
    """
    
    # Unique ID like "1a", "1b", "2a", etc.
    id: str = Field(description="Question identifier (e.g., '1a', '2b')")
    
    # The question text
    text: str = Field(description="What the question asks")
    
    # How many points this sub-question is worth
    points: float = Field(description="Point value")
    
    # How to grade it
    grading_rule: GradingRule
    
    # The correct solution
    solution: Solution

    # Type of question (determines grading logic)
    question_type: QuestionType = Field(
        default=QuestionType.NUMERIC,
        description="Type of question (determines grading logic)"
    )
    
    # 🎓 CONCEPT: Nested Models
    # Notice how SubQuestion contains GradingRule and Solution.
    # This is composition - building complex objects from simpler ones.
    # Pydantic handles this automatically!


# ============================================================================
# QUESTION
# ============================================================================

class Question(BaseModel):
    """
    A main question (like "Question 1") containing multiple sub-questions.
    
    🎓 CONCEPT: Hierarchical Data
    -----------------------------
    Real-world data is often hierarchical:
        Rubric
          └── Question 1
                ├── 1a (5 pts)
                ├── 1b (5 pts)
                └── 1c (10 pts)
    
    We model this hierarchy explicitly with nested models.
    """
    
    # Question number (1, 2, 3, etc.)
    number: int = Field(description="Question number")
    
    # Question text/prompt
    text: str = Field(description="Main question text or setup")
    
    # All sub-questions (1a, 1b, etc.)
    sub_questions: List[SubQuestion] = Field(
        description="List of sub-questions"
    )
    
    # Total points (sum of all sub-questions)
    total_points: float = Field(description="Total points for this question")
    
    # Optional context (e.g., "A standard deck has 52 cards...")
    context: Optional[str] = Field(
        default=None,
        description="Setup/context needed for all sub-questions"
    )
    
    # 🎓 TIP: We could auto-calculate total_points from sub_questions,
    # but explicit is often better for validation - ensures rubric parser
    # got it right!


# ============================================================================
# RUBRIC (Top-Level)
# ============================================================================

class Rubric(BaseModel):
    """
    Complete grading rubric for an assignment.
    
    🎓 CONCEPT: The "Root" Model
    ----------------------------
    This is the top-level object. Everything else nests inside it:
    
    Rubric
      ├── assignment_id: "HW10"
      ├── total_points: 100
      ├── questions: [Question1, Question2, ...]
      │     ├── sub_questions: [1a, 1b, ...]
      │     │     ├── solution: Solution
      │     │     └── grading_rule: GradingRule
      
    When we parse a PDF rubric, we'll build this entire tree structure.
    Then grading becomes: traverse the tree, compare answers.
    """
    
    # Assignment identifier (e.g., "HW10", "Midterm", etc.)
    assignment_id: str = Field(description="Assignment name/ID")
    
    # Course identifier
    course: str = Field(
        default="CSCI-C241",
        description="Course code"
    )
    
    # Total possible points
    total_points: float = Field(description="Total points possible")
    
    # Base points given for completion (e.g., 18 points just for submitting)
    base_points: float = Field(
        default=0,
        description="Points awarded for completion"
    )
    
    # All questions
    questions: List[Question] = Field(description="All questions in assignment")
    
    # Optional general notes
    general_notes: Optional[str] = Field(
        default=None,
        description="General grading instructions"
    )
    
    # 🎓 PYDANTIC FEATURE: Model Validation
    # Pydantic will automatically validate:
    # - assignment_id is a string (can't pass a number)
    # - total_points is a float/number (can't pass "one hundred")
    # - questions is a List of Question objects
    # 
    # This catches bugs EARLY instead of failing during grading!
    
    class Config:
        """
        Pydantic configuration.
        
        🎓 CONCEPT: Model Configuration
        -------------------------------
        The Config class lets you customize Pydantic behavior.
        Common settings:
        - arbitrary_types_allowed: Allow non-Pydantic types
        - json_encoders: Custom JSON serialization
        - validate_assignment: Validate when fields change
        """
        # Enable JSON schema generation (useful for docs/APIs)
        json_schema_extra = {
            "example": {
                "assignment_id": "HW10",
                "course": "CSCI-C241",
                "total_points": 100,
                "base_points": 18,
                "questions": [
                    {
                        "number": 1,
                        "text": "Deck of cards problem",
                        "total_points": 35,
                        "sub_questions": []
                    }
                ]
            }
        }


# ============================================================================
# EXPORTS
# ============================================================================

# When someone does: from mathgrader.models.rubric import *
# These are the things they get:
__all__ = [
    "GradingRuleType",
    "GradingRule",
    "Solution",
    "SubQuestion",
    "Question",
    "Rubric",
    "QuestionType",
]

# 🎓 SUMMARY: What We Just Built
# ===============================
# 
# We created a TYPE-SAFE way to represent a rubric:
#
# 1. Enum for grading rule types (no typos possible)
# 2. GradingRule model (how to score)
# 3. Solution model (what's correct)
# 4. SubQuestion model (1a, 1b, etc.)
# 5. Question model (Question 1, 2, etc.)
# 6. Rubric model (entire assignment)
#
# KEY BENEFITS:
# - Type safety: Python + IDE will catch errors
# - Validation: Data must be valid
# - Documentation: Models ARE the docs
# - JSON export: Easy to save/load
#
# NEXT STEPS:
# - Build Submission model (student answers)
# - Build GradeResult model (grading output)
# - Then we can build the parser!

