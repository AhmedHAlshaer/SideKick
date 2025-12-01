"""
Rubric Parser - Extracts structured rubric data from PDF files.

🎓 LEARNING OBJECTIVES:
----------------------
1. PDF text extraction with PyMuPDF
2. Regex pattern matching for structure extraction
3. Error-resilient parsing (handle messy PDFs)
4. Caching for performance

This is the first "real" component that processes external data!
"""

import re
import fitz  # PyMuPDF
from pathlib import Path
from typing import Optional, List, Tuple
import json

from ..models.rubric import (
    Rubric,
    Question,
    SubQuestion,
    Solution,
    GradingRule,
    GradingRuleType,
    QuestionType
)


class RubricParser:
    """
    Parses PDF rubrics into structured Rubric objects.
    
    🎓 CONCEPT: Fault-Tolerant Parsing
    ----------------------------------
    PDFs are messy! Different instructors format rubrics differently.
    
    Our strategy:
    1. Extract all text from PDF
    2. Use regex patterns to find structure (questions, points, etc.)
    3. Be permissive - if we can't parse something, skip it gracefully
    4. Cache results to avoid re-parsing
    
    This is how real-world parsers work - they expect imperfect input!
    
    Usage:
        parser = RubricParser()
        rubric = parser.parse("HW_10_rubric.pdf")
        print(f"Found {len(rubric.questions)} questions")
    """
    
    # 🎓 CONCEPT: Regex Pattern Library
    # ---------------------------------
    # Instead of hardcoding patterns everywhere, we define them once
    # This makes the code:
    # - More maintainable (change pattern in one place)
    # - More testable (can test patterns independently)
    # - More readable (named patterns are self-documenting)
    
    PATTERNS = {
        # Matches: "1.", "2.", "Problem 1", "Question 1", "Q1" (Start of line)
        "question": r"(?:^|\n)\s*(?:Problem|Question|Q)?\s*(\d+)\.\s+",
        
        # Matches: "a)", "b)", "(a)", "(b)", "1a)", "1.a"
        "sub_question": r"(?:^|\n)\s*(?:\()?([a-z])\)?[\.\)]\s+",
        
        # Matches: "(5 pts)", "[5]", "5 points" (Strict: must have parens OR keyword)
        "points": r"(?:[\[\(]\s*(\d+(?:\.\d+)?)\s*(?:points?|pts?)?\s*[\]\)])|(?:\b(\d+(?:\.\d+)?)\s*(?:points|pts)\b)",
        
        # Matches: "Answer: 42", "Solution: x = 5", "= 42"
        "solution": r"(?:Answer|Solution|Ans|Sol)\s*[:=]\s*(.+?)(?=\n|$)|(?<=\n)\s*=\s*(.+?)(?=\n|$)",
        
        # Matches grading notes: "Grading: +1 correct, -1 wrong"
        "grading_note": r"Grading\s*(?:Note)?:?\s*(.+?)(?=\n\n|$)",
    }
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize parser.
        
        Args:
            cache_dir: Where to cache parsed rubrics (speeds up re-parsing)
        """
        self.cache_dir = cache_dir or Path("grading_data/rubrics")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    # ========================================================================
    # PUBLIC API
    # ========================================================================
    
    def parse(self, pdf_path: str | Path, use_cache: bool = True) -> Rubric:
        """
        Parse a PDF rubric into a Rubric object.
        
        🎓 CONCEPT: Caching Strategy
        ----------------------------
        Parsing PDFs is slow (regex is expensive on large text).
        
        Strategy:
        1. Check if we've parsed this PDF before (cache exists)
        2. Check if cache is fresh (newer than PDF modification time)
        3. If yes, load from cache (instant!)
        4. If no, parse PDF and save to cache
        
        This is a COMMON pattern in production systems!
        
        Args:
            pdf_path: Path to the PDF file
            use_cache: Whether to use cached version if available
            
        Returns:
            Rubric object with all questions parsed
            
        Raises:
            FileNotFoundError: If PDF doesn't exist
            ValueError: If PDF is empty or unreadable
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"Rubric PDF not found: {pdf_path}")
        
        # Check cache first
        if use_cache:
            cached = self._load_from_cache(pdf_path)
            if cached:
                print(f"✅ Loaded rubric from cache: {pdf_path.name}")
                return cached
        
        print(f"📄 Parsing rubric PDF: {pdf_path.name}...")
        
        # Extract text from PDF
        raw_text = self._extract_pdf_text(pdf_path)
        
        if not raw_text.strip():
            raise ValueError(f"PDF is empty or unreadable: {pdf_path}")
        
        # Parse into structured format
        rubric = self._parse_rubric_text(raw_text, pdf_path.stem)
        
        # Cache for next time
        self._save_to_cache(pdf_path, rubric)
        
        print(f"✅ Parsed {len(rubric.questions)} questions, {rubric.total_points} total points")
        
        return rubric
    
    # ========================================================================
    # PDF EXTRACTION
    # ========================================================================
    
    def _extract_pdf_text(self, pdf_path: Path) -> str:
        """
        Extract all text from a PDF file.
        
        🎓 CONCEPT: PyMuPDF Text Extraction
        -----------------------------------
        PyMuPDF (fitz) extracts text from PDFs by:
        1. Analyzing PDF structure (fonts, positions)
        2. Reconstructing text in reading order
        3. Preserving layout (spaces, newlines)
        
        Alternative methods:
        - get_text("text"): Plain text (what we use)
        - get_text("blocks"): Text + position info
        - get_text("dict"): Full structured data
        
        We use "text" mode because it's simplest for our needs.
        """
        try:
            doc = fitz.open(pdf_path)
            text_parts = []
            
            for page_num, page in enumerate(doc, 1):
                text = page.get_text()
                text_parts.append(text)
            
            doc.close()
            
            full_text = "\n".join(text_parts)
            return full_text
            
        except Exception as e:
            raise ValueError(f"Failed to read PDF: {e}")
    
    # ========================================================================
    # PARSING LOGIC
    # ========================================================================
    
    def _parse_rubric_text(self, text: str, name: str) -> Rubric:
        """
        Parse raw text into a Rubric object.
        
        🎓 CONCEPT: Top-Down Parsing
        ----------------------------
        We parse from largest units to smallest:
        1. Split into question blocks (Question 1, Question 2, etc.)
        2. Parse each question block
        3. Within each, find sub-questions (a, b, c)
        4. Extract points, solutions, grading rules
        
        This is called "top-down parsing" - common in compilers!
        """
        # Extract metadata
        assignment_id = self._extract_assignment_id(text)
        base_points = self._extract_base_points(text)
        
        # Split into question blocks
        question_blocks = self._split_into_questions(text)
        
        # Parse each question
        questions = []
        for q_num, q_text in question_blocks:
            question = self._parse_question(q_num, q_text)
            if question:
                questions.append(question)
        
        # Calculate total
        total_points = sum(q.total_points for q in questions) + base_points
        
        return Rubric(
            assignment_id=assignment_id,
            course="CSCI-C241",  # Could make this configurable
            total_points=total_points,
            base_points=base_points,
            questions=questions
        )
    
    def _extract_assignment_id(self, text: str) -> str:
        """Extract assignment ID like 'HW #10' from text."""
        match = re.search(r'(?:HW|Homework|Assignment)\s*#?\s*(\d+)', text, re.IGNORECASE)
        if match:
            return f"HW{match.group(1)}"
        return "Unknown"
    
    def _extract_base_points(self, text: str) -> float:
        """
        Extract base completion points.
        
        🎓 EXAMPLE: "Give 18 points for completing the assignment"
        """
        match = re.search(r'Give\s+(\d+)\s+points?\s+for\s+complet', text, re.IGNORECASE)
        if match:
            return float(match.group(1))
        return 0.0
    
    def _split_into_questions(self, text: str) -> List[Tuple[int, str]]:
        """
        Split text into question blocks.
        
        🎓 CONCEPT: Regex-Based Splitting
        ---------------------------------
        We use regex to find question boundaries, then slice the text.
        
        Example:
            "1. First question\n2. Second question"
            → [(1, "1. First question\n"), (2, "2. Second question")]
        
        Returns:
            List of (question_number, question_text) tuples
        """
        pattern = self.PATTERNS["question"]
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        
        if not matches:
            # No clear question structure
            print("⚠️  Warning: No questions found in rubric")
            return []
        
        blocks = []
        for i, match in enumerate(matches):
            q_num = int(match.group(1))
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            q_text = text[start:end]
            blocks.append((q_num, q_text))
        
        return blocks
    
    def _parse_question(self, q_num: int, text: str) -> Optional[Question]:
        """
        Parse a single question block.
        
        🎓 CONCEPT: Sub-Question Detection
        ----------------------------------
        Some questions have sub-parts (a, b, c), some don't.
        
        Strategy:
        1. Try to find sub-questions (look for a), b), etc.)
        2. If found 2+, treat as multi-part question
        3. If not, treat entire question as one part
        """
        # Try to parse sub-questions
        sub_questions = self._parse_sub_questions(q_num, text)
        
        if not sub_questions:
            # No sub-questions found, create a single one
            points = self._extract_points(text)
            solution = self._extract_solution(text)
            grading_rule = self._extract_grading_rule(text)
            question_type = self._infer_question_type(text)
            
            sub_questions = [
                SubQuestion(
                    id=str(q_num),
                    text=text[:200].strip(),
                    points=points,
                    grading_rule=grading_rule,
                    solution=solution,
                    question_type=question_type
                )
            ]
        
        total_points = sum(sq.points for sq in sub_questions)
        
        return Question(
            number=q_num,
            text=text[:300].strip(),  # Store first 300 chars as context
            sub_questions=sub_questions,
            total_points=total_points
        )
    
    def _parse_sub_questions(self, q_num: int, text: str) -> List[SubQuestion]:
        """
        Parse sub-questions (a, b, c, etc.) from question text.
        
        🎓 CONCEPT: Pattern Matching with Lookahead
        -------------------------------------------
        We find where each sub-question starts, then slice between them.
        
        Example:
            "a) First part\nb) Second part"
            → Two matches at positions of 'a)' and 'b)'
            → Slice text between them
        """
        pattern = self.PATTERNS["sub_question"]
        matches = list(re.finditer(pattern, text))
        
        if len(matches) < 2:
            # Need at least 2 to confirm it's a sub-question pattern
            return []
        
        sub_questions = []
        
        for i, match in enumerate(matches):
            letter = match.group(1)
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            sub_text = text[start:end].strip()
            
            # Parse components
            points = self._extract_points(sub_text)
            solution = self._extract_solution(sub_text)
            grading_rule = self._extract_grading_rule(sub_text)
            question_type = self._infer_question_type(sub_text)
            
            sub_questions.append(SubQuestion(
                id=f"{q_num}{letter}",
                text=sub_text[:150].strip(),
                points=points,
                grading_rule=grading_rule,
                solution=solution,
                question_type=question_type
            ))
        
        return sub_questions
    
    # ========================================================================
    # COMPONENT EXTRACTION
    # ========================================================================
    
    def _extract_points(self, text: str) -> float:
        """
        Extract point value from text.
        
        🎓 HANDLES: "(5 points)", "5 pts", "[5]", etc.
        """
        match = re.search(self.PATTERNS["points"], text, re.IGNORECASE)
        if match:
            # Group 1 (parens) or Group 2 (explicit keyword)
            val = match.group(1) or match.group(2)
            if val:
                return float(val)
        return 1.0  # Default to 1 point if not specified
    
    def _extract_solution(self, text: str) -> Solution:
        """
        Extract the solution/answer from text.
        
        🎓 CONCEPT: Multiple Pattern Attempts
        -------------------------------------
        We try several patterns because answers are formatted differently:
        - "Answer: 1/4"
        - "Solution: x = 5"
        - "= 42"
        - Just the raw value
        """
        # Try explicit answer markers first
        match = re.search(self.PATTERNS["solution"], text, re.IGNORECASE | re.MULTILINE)
        
        if match:
            # Group 1 or Group 2 could be the answer depending on which part of OR matched
            answer = match.group(1) or match.group(2)
            answer = answer.strip()
            # Clean up common artifacts
            answer = answer.split('\n')[0]  # Take first line only
            answer = answer.rstrip('.')  # Remove trailing period
            
            return Solution(
                value=answer,
                equivalent_forms=self._generate_equivalent_forms(answer)
            )
        
        # No explicit answer found
        return Solution(value="", equivalent_forms=[])
    
    def _generate_equivalent_forms(self, answer: str) -> List[str]:
        """
        Generate mathematically equivalent forms.
        
        🎓 CONCEPT: Proactive Equivalence
        ---------------------------------
        We pre-compute some obvious equivalent forms:
        - 1/4 → also accept 0.25
        - 0.5 → also accept 1/2
        - True → also accept T, true, TRUE
        
        The MathComparator will handle more complex equivalence later.
        """
        equivalents = []
        
        # Fraction → decimal
        if "/" in answer:
            try:
                parts = answer.replace(" ", "").split("/")
                if len(parts) == 2:
                    num, denom = float(parts[0]), float(parts[1])
                    decimal = num / denom
                    equivalents.append(f"{decimal:.6f}".rstrip("0").rstrip("."))
            except (ValueError, ZeroDivisionError):
                pass
        
        # True/False variations
        if answer.lower() in ["true", "t"]:
            equivalents.extend(["True", "true", "TRUE", "T"])
        elif answer.lower() in ["false", "f"]:
            equivalents.extend(["False", "false", "FALSE", "F"])
        
        return equivalents
    
    def _extract_grading_rule(self, text: str) -> GradingRule:
        """
        Extract grading rule from "Grading Note:" section.
        
        🎓 EXAMPLES:
        - "+1 correct, -1 incorrect, min 0" → PER_ITEM_PENALTY
        - "5 points if correct" → NO_PARTIAL
        - "Partial credit allowed" → PARTIAL_CREDIT
        """
        match = re.search(self.PATTERNS["grading_note"], text, re.IGNORECASE | re.DOTALL)
        
        if not match:
            # Default rule: all or nothing
            return GradingRule(
                rule_type=GradingRuleType.NO_PARTIAL,
                points_correct=1,
                points_incorrect=0,
                minimum_score=0
            )
        
        note = match.group(1).lower()
        
        # Check for +1/-1 pattern (common for True/False)
        if "+1" in note and "-1" in note:
            min_match = re.search(r'min(?:imum)?\s*(\d+)', note)
            min_score = float(min_match.group(1)) if min_match else 0
            
            return GradingRule(
                rule_type=GradingRuleType.PER_ITEM_PENALTY,
                points_correct=1,
                points_incorrect=-1,
                minimum_score=min_score,
                notes=note
            )
        
        # Check for partial credit
        if "partial" in note:
            return GradingRule(
                rule_type=GradingRuleType.PARTIAL_CREDIT,
                points_correct=1,
                points_incorrect=0,
                minimum_score=0,
                notes=note
            )
        
        # Default: no partial credit
        return GradingRule(
            rule_type=GradingRuleType.NO_PARTIAL,
            points_correct=1,
            points_incorrect=0,
            minimum_score=0
        )
    
    def _infer_question_type(self, text: str) -> QuestionType:
        """
        Infer question type from text content.
        
        🎓 CONCEPT: Heuristic Classification
        ------------------------------------
        We use keywords to guess the question type.
        This isn't perfect, but works well enough!
        
        Better approach for production: Train a classifier
        """
        text_lower = text.lower()
        
        # Check for specific patterns
        if re.search(r'\b(?:true|false)\b', text_lower):
            return QuestionType.TRUE_FALSE
        
        if re.search(r'p\s*\(', text_lower):  # P(...) for probability
            return QuestionType.PROBABILITY
        
        if re.search(r'o\s*\(', text_lower) or 'big-o' in text_lower:
            return QuestionType.BIG_O
        
        if any(word in text_lower for word in ["prove", "proof", "show that"]):
            return QuestionType.PROOF
        
        if any(word in text_lower for word in ["explain", "describe"]):
            return QuestionType.SHORT_ANSWER
        
        # Default to numeric
        return QuestionType.NUMERIC
    
    # ========================================================================
    # CACHING
    # ========================================================================
    
    def _cache_path(self, pdf_path: Path) -> Path:
        """Get cache file path for a PDF."""
        return self.cache_dir / f"{pdf_path.stem}.json"
    
    def _load_from_cache(self, pdf_path: Path) -> Optional[Rubric]:
        """
        Load rubric from cache if valid.
        
        🎓 CONCEPT: Cache Invalidation
        ------------------------------
        Classic problem: "How do you know when cache is stale?"
        
        Our strategy: Compare file modification times
        - If cache is older than PDF → stale, re-parse
        - If cache is newer → valid, use it!
        """
        cache_path = self._cache_path(pdf_path)
        
        if not cache_path.exists():
            return None
        
        # Check if cache is stale (PDF modified after cache)
        if cache_path.stat().st_mtime < pdf_path.stat().st_mtime:
            return None
        
        try:
            with open(cache_path, "r") as f:
                data = json.load(f)
            return Rubric.model_validate(data)
        except Exception as e:
            print(f"⚠️  Cache read failed: {e}")
            return None
    
    def _save_to_cache(self, pdf_path: Path, rubric: Rubric) -> None:
        """Save parsed rubric to cache."""
        cache_path = self._cache_path(pdf_path)
        
        try:
            with open(cache_path, "w") as f:
                f.write(rubric.model_dump_json(indent=2))
        except Exception as e:
            print(f"⚠️  Cache write failed: {e}")


# 🎓 SUMMARY: What This Parser Does
# ==================================
#
# INPUT: PDF file with a rubric
# OUTPUT: Structured Rubric object
#
# PROCESS:
# 1. Extract text from PDF (PyMuPDF)
# 2. Find questions (regex: "1.", "2.", etc.)
# 3. Find sub-questions (regex: "a)", "b)", etc.)
# 4. Extract points, solutions, grading rules
# 5. Infer question types (True/False, Numeric, etc.)
# 6. Build Rubric object
# 7. Cache result for speed
#
# KEY TECHNIQUES:
# - Regex for pattern matching
# - Top-down parsing (large → small)
# - Fault tolerance (gracefully handle missing data)
# - Caching for performance
#
# This is a REAL parser used in production systems!
