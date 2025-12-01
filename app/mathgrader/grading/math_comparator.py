"""
Math Comparator - Handles mathematical equivalence checking.

🎓 WHY THIS EXISTS:
-------------------
Students write answers in many forms:
- "1/4" vs "0.25" vs "0.250" vs ".25"
- "2x" vs "2*x" vs "x*2"
- "True" vs "true" vs "T"

A simple string match would mark correct answers wrong!

This module uses SymPy to check MATHEMATICAL equivalence.
"""

import re
from typing import Optional, Tuple, List
from sympy import (
    sympify, 
    simplify, 
    Rational, 
    Float,
    Symbol,
    Eq,
    N
)
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor
)

from ..models.rubric import QuestionType


class MathComparator:
    """
    Compares student answers to correct answers with mathematical awareness.
    
    🎓 CONCEPT: Semantic vs Syntactic Equality
    ------------------------------------------
    - Syntactic: Are the strings identical? "1/4" != "0.25"
    - Semantic: Do they represent the same value? "1/4" == "0.25" ✓
    
    We want SEMANTIC equality for math grading!
    
    Usage:
        comparator = MathComparator()
        is_correct, confidence = comparator.compare("1/4", "0.25", QuestionType.NUMERIC)
        # → (True, 1.0)
    """
    
    # Parsing transformations for SymPy
    TRANSFORMATIONS = (
        standard_transformations + 
        (implicit_multiplication_application, convert_xor)
    )
    
    # Tolerance for floating point comparison
    FLOAT_TOLERANCE = 1e-6
    
    def compare(
        self, 
        student_answer: str, 
        correct_answer: str,
        question_type: QuestionType,
        equivalent_forms: List[str] = None
    ) -> Tuple[bool, float]:
        """
        Compare student answer to correct answer.
        
        Args:
            student_answer: What the student wrote
            correct_answer: The rubric's correct answer
            question_type: Type of question (affects comparison logic)
            equivalent_forms: Pre-computed equivalent forms to check
            
        Returns:
            Tuple of (is_correct, confidence)
            - is_correct: True if answers match
            - confidence: 0.0-1.0, how confident we are in the comparison
        """
        # Clean inputs
        student = self._normalize(student_answer)
        correct = self._normalize(correct_answer)
        
        # Empty answer is always wrong
        if not student:
            return (False, 1.0)
        
        # Exact match (fast path)
        if student == correct:
            return (True, 1.0)
        
        # Check pre-computed equivalent forms
        if equivalent_forms:
            if student in [self._normalize(f) for f in equivalent_forms]:
                return (True, 1.0)
        
        # Type-specific comparison
        if question_type == QuestionType.TRUE_FALSE:
            return self._compare_boolean(student, correct)
        
        elif question_type == QuestionType.NUMERIC:
            return self._compare_numeric(student, correct)
        
        elif question_type == QuestionType.PROBABILITY:
            return self._compare_probability(student, correct)
        
        elif question_type == QuestionType.BIG_O:
            return self._compare_big_o(student, correct)
        
        elif question_type == QuestionType.MULTIPLE_CHOICE:
            return self._compare_multiple_choice(student, correct)
        
        else:
            # For SHORT_ANSWER, PROOF, GRAPHING - need manual/LLM grading
            return (False, 0.3)  # Low confidence = flag for review
    
    # ========================================================================
    # NORMALIZATION
    # ========================================================================
    
    def _normalize(self, text: str) -> str:
        """
        Normalize text for comparison.
        
        🎓 CONCEPT: Canonical Form
        --------------------------
        Convert all variations to a single "canonical" form:
        - Lowercase
        - Strip whitespace
        - Remove extra spaces
        """
        if not text:
            return ""
        
        text = str(text).strip().lower()
        text = re.sub(r'\s+', ' ', text)  # Collapse whitespace
        return text
    
    # ========================================================================
    # TYPE-SPECIFIC COMPARISONS
    # ========================================================================
    
    def _compare_boolean(self, student: str, correct: str) -> Tuple[bool, float]:
        """
        Compare True/False answers.
        
        🎓 HANDLES: true, True, TRUE, T, t, false, False, FALSE, F, f
        """
        true_values = {'true', 't', '1', 'yes', 'y'}
        false_values = {'false', 'f', '0', 'no', 'n'}
        
        student_bool = None
        correct_bool = None
        
        if student in true_values:
            student_bool = True
        elif student in false_values:
            student_bool = False
        
        if correct in true_values:
            correct_bool = True
        elif correct in false_values:
            correct_bool = False
        
        # Could not parse one of them
        if student_bool is None or correct_bool is None:
            return (False, 0.5)  # Uncertain
        
        return (student_bool == correct_bool, 1.0)
    
    def _compare_numeric(self, student: str, correct: str) -> Tuple[bool, float]:
        """
        Compare numeric/mathematical expressions.
        
        🎓 HANDLES:
        - Fractions: 1/4, 1/2
        - Decimals: 0.25, .5
        - Expressions: 2*3, 2^3
        - Symbolic: 2x, x^2
        """
        try:
            # Try to parse as SymPy expressions
            student_expr = self._parse_math(student)
            correct_expr = self._parse_math(correct)
            
            if student_expr is None or correct_expr is None:
                return (False, 0.5)
            
            # Check symbolic equality
            diff = simplify(student_expr - correct_expr)
            if diff == 0:
                return (True, 1.0)
            
            # Try numeric evaluation
            try:
                student_val = float(N(student_expr))
                correct_val = float(N(correct_expr))
                
                if abs(student_val - correct_val) < self.FLOAT_TOLERANCE:
                    return (True, 0.95)  # Slightly less confident for numeric
            except (TypeError, ValueError):
                pass
            
            return (False, 0.9)
            
        except Exception:
            return (False, 0.5)
    
    def _compare_probability(self, student: str, correct: str) -> Tuple[bool, float]:
        """
        Compare probability values.
        
        🎓 HANDLES:
        - Fractions: 1/4, 13/52
        - Decimals: 0.25, 0.5
        - Percentages: 25%, 50%
        """
        # Strip percentage sign and convert
        student = student.rstrip('%')
        correct = correct.rstrip('%')
        
        # If correct answer has %, convert student to percentage
        if '%' in correct:
            try:
                student_val = float(self._parse_math(student)) * 100
                correct_val = float(self._parse_math(correct.rstrip('%')))
                if abs(student_val - correct_val) < self.FLOAT_TOLERANCE:
                    return (True, 0.95)
            except:
                pass
        
        # Otherwise, compare as regular numeric
        return self._compare_numeric(student, correct)
    
    def _compare_big_o(self, student: str, correct: str) -> Tuple[bool, float]:
        """
        Compare Big-O notation answers.
        
        🎓 HANDLES:
        - O(n), O(n^2), O(log n), O(n!)
        - With or without the O() wrapper
        - Different variable names
        """
        # Extract the expression inside O()
        student_inner = self._extract_big_o(student)
        correct_inner = self._extract_big_o(correct)
        
        if not student_inner or not correct_inner:
            return (False, 0.5)
        
        # Normalize common variations
        student_inner = self._normalize_big_o(student_inner)
        correct_inner = self._normalize_big_o(correct_inner)
        
        # Direct match after normalization
        if student_inner == correct_inner:
            return (True, 1.0)
        
        # Try symbolic comparison
        try:
            n = Symbol('n')
            student_expr = parse_expr(student_inner, local_dict={'n': n})
            correct_expr = parse_expr(correct_inner, local_dict={'n': n})
            
            if simplify(student_expr - correct_expr) == 0:
                return (True, 0.95)
        except:
            pass
        
        return (False, 0.8)
    
    def _compare_multiple_choice(self, student: str, correct: str) -> Tuple[bool, float]:
        """Compare multiple choice answers (A, B, C, D)."""
        # Just compare the first character (the letter)
        student_letter = student[0] if student else ""
        correct_letter = correct[0] if correct else ""
        
        return (student_letter == correct_letter, 1.0)
    
    # ========================================================================
    # HELPERS
    # ========================================================================
    
    def _parse_math(self, expr: str) -> Optional[any]:
        """
        Parse a mathematical expression using SymPy.
        
        🎓 CONCEPT: Robust Parsing
        --------------------------
        We use multiple strategies to parse messy student input:
        1. Try SymPy's standard parser
        2. Try with implicit multiplication (2x → 2*x)
        3. Handle common notations (^ for exponent)
        """
        if not expr:
            return None
        
        # Pre-process common notations
        expr = expr.replace('^', '**')  # Caret to Python exponent
        expr = expr.replace('×', '*')   # Unicode multiplication
        expr = expr.replace('÷', '/')   # Unicode division
        
        try:
            return parse_expr(expr, transformations=self.TRANSFORMATIONS)
        except:
            pass
        
        # Try as a simple fraction
        if '/' in expr:
            try:
                parts = expr.split('/')
                if len(parts) == 2:
                    return Rational(parts[0].strip(), parts[1].strip())
            except:
                pass
        
        # Try as float
        try:
            return Float(expr)
        except:
            pass
        
        return None
    
    def _extract_big_o(self, expr: str) -> str:
        """Extract the inner expression from O(...)."""
        # Match O(...) or just the expression
        match = re.search(r'[oO]\s*\(\s*(.+?)\s*\)', expr)
        if match:
            return match.group(1)
        
        # No O() wrapper, return cleaned expression
        return expr.strip()
    
    def _normalize_big_o(self, expr: str) -> str:
        """Normalize Big-O expressions."""
        expr = expr.lower()
        expr = expr.replace(' ', '')
        expr = expr.replace('^', '**')
        expr = expr.replace('log(n)', 'logn')
        expr = expr.replace('log n', 'logn')
        return expr