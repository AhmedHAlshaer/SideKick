"""
Submission Parser - Extracts student answers from PDF submissions.

🎓 WHY THIS IS HARD:
-------------------
Student PDFs are MESSY:
- Handwritten text (if scanned)
- Different layouts
- Missing question numbers
- Unclear formatting

Our strategy:
1. Extract all text
2. Find question markers (1a, 1b, etc.)
3. Extract the answer after each marker
4. Track confidence (flag uncertain extractions)
"""

import re
import fitz  # PyMuPDF
from pathlib import Path
from typing import Optional, List, Tuple, Dict
from datetime import datetime

from ..models.submission import Submission, StudentAnswer
from ..models.rubric import Rubric


class SubmissionParser:
    """
    Parses student PDF submissions into structured Submission objects.
    
    Usage:
        parser = SubmissionParser()
        submission = parser.parse("student_001.pdf", rubric)
    """
    
    # Pattern to find question labels: "1a", "1.a", "1a)", "(1a)", "1. a"
    QUESTION_PATTERN = r'(?:^|\n)\s*(?:\()?(\d+)\s*[.\-]?\s*([a-z])?(?:\)|\.|\:)?\s*'
    
    def __init__(self, submissions_dir: Optional[Path] = None):
        """Initialize parser."""
        self.submissions_dir = submissions_dir or Path("grading_data/submissions")
        self.submissions_dir.mkdir(parents=True, exist_ok=True)
    
    def parse(
        self, 
        pdf_path: str | Path, 
        rubric: Rubric,
        student_id: Optional[str] = None
    ) -> Submission:
        """
        Parse a student submission PDF.
        
        Args:
            pdf_path: Path to student's PDF
            rubric: The rubric (tells us what questions to look for)
            student_id: Optional student ID (extracted from filename if not given)
            
        Returns:
            Submission object with extracted answers
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"Submission not found: {pdf_path}")
        
        # Extract student ID from filename if not provided
        if not student_id:
            student_id = self._extract_student_id(pdf_path.stem)
        
        # Extract text
        raw_text = self._extract_pdf_text(pdf_path)
        
        # Get expected question IDs from rubric
        expected_questions = self._get_expected_questions(rubric)
        
        # Extract answers
        answers = self._extract_answers(raw_text, expected_questions)
        
        return Submission(
            student_id=student_id,
            assignment_id=rubric.assignment_id,
            file_path=str(pdf_path),
            answers=answers,
            submission_time=datetime.now()
        )
    
    def parse_batch(
        self, 
        pdf_dir: str | Path, 
        rubric: Rubric
    ) -> List[Submission]:
        """
        Parse all PDF submissions in a directory.
        
        🎓 CONCEPT: Batch Processing
        ----------------------------
        In production, you often process many files at once.
        This method handles a whole folder of submissions.
        """
        pdf_dir = Path(pdf_dir)
        submissions = []
        
        pdf_files = list(pdf_dir.glob("*.pdf"))
        print(f"📄 Found {len(pdf_files)} PDFs to process...")
        
        for i, pdf_path in enumerate(pdf_files, 1):
            try:
                print(f"  [{i}/{len(pdf_files)}] Parsing {pdf_path.name}...")
                submission = self.parse(pdf_path, rubric)
                submissions.append(submission)
            except Exception as e:
                print(f"  ⚠️  Error parsing {pdf_path.name}: {e}")
        
        print(f"✅ Parsed {len(submissions)} submissions")
        return submissions
    
    # ========================================================================
    # EXTRACTION METHODS
    # ========================================================================
    
    def _extract_pdf_text(self, pdf_path: Path) -> str:
        """Extract text from PDF."""
        doc = fitz.open(pdf_path)
        text_parts = []
        
        for page in doc:
            text_parts.append(page.get_text())
        
        doc.close()
        return "\n".join(text_parts)
    
    def _extract_student_id(self, filename: str) -> str:
        """
        Extract student ID from filename.
        
        🎓 HANDLES:
        - "student_001.pdf" → "001"
        - "john_doe_12345.pdf" → "12345"
        - "submission_abc123.pdf" → "abc123"
        """
        # Look for common patterns
        patterns = [
            r'student[_\-]?(\w+)',
            r'submission[_\-]?(\w+)',
            r'(\d{3,})',  # 3+ digit number
            r'[_\-](\w+)$',  # Last part after underscore/dash
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Fallback: use whole filename
        return filename
    
    def _get_expected_questions(self, rubric: Rubric) -> List[str]:
        """Get list of question IDs from rubric."""
        question_ids = []
        
        for question in rubric.questions:
            for sub_q in question.sub_questions:
                question_ids.append(sub_q.id)
        
        return question_ids
    
    def _extract_answers(
        self, 
        text: str, 
        expected_questions: List[str]
    ) -> List[StudentAnswer]:
        """
        Extract answers for each expected question.
        
        🎓 CONCEPT: Pattern-Based Extraction
        ------------------------------------
        We look for question markers and extract what follows.
        
        Example:
            "1a) True"  →  StudentAnswer(question_id="1a", raw_text="True")
            "2. 42"     →  StudentAnswer(question_id="2", raw_text="42")
        """
        answers = []
        
        # Find all question markers in the text
        found_answers = self._find_answer_blocks(text)
        
        for q_id in expected_questions:
            if q_id in found_answers:
                raw_text, confidence = found_answers[q_id]
                answers.append(StudentAnswer(
                    question_id=q_id,
                    raw_text=raw_text,
                    parsed_value=self._clean_answer(raw_text),
                    confidence=confidence
                ))
            else:
                # Question not found - create placeholder
                answers.append(StudentAnswer(
                    question_id=q_id,
                    raw_text="",
                    parsed_value="",
                    confidence=0.0  # Flag for review
                ))
        
        return answers
    
    def _find_answer_blocks(self, text: str) -> Dict[str, Tuple[str, float]]:
        """
        Find all question markers and their answers.
        
        Returns:
            Dict mapping question_id → (answer_text, confidence)
        """
        answers = {}
        
        # Pattern: "1a" or "1.a" or "1a)" or "(1a)" followed by text
        pattern = r'(?:^|\n)\s*(?:\()?(\d+)\s*[.\-]?\s*([a-z])?(?:\)|\.|\:)?\s*(.+?)(?=(?:\n\s*(?:\()?\d+\s*[.\-]?\s*[a-z]?(?:\)|\.|\:)?)|$)'
        
        matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            q_num = match.group(1)
            q_letter = match.group(2) or ""
            answer_text = match.group(3).strip()
            
            q_id = f"{q_num}{q_letter}".lower()
            
            # Calculate confidence based on answer quality
            confidence = self._calculate_confidence(answer_text)
            
            # Take first line as the actual answer (rest might be work)
            first_line = answer_text.split('\n')[0].strip()
            
            answers[q_id] = (first_line, confidence)
        
        return answers
    
    def _calculate_confidence(self, answer_text: str) -> float:
        """
        Calculate confidence score for extracted answer.
        
        🎓 CONCEPT: Uncertainty Quantification
        --------------------------------------
        Not all extractions are equally reliable. We track confidence to:
        - Automatically grade high-confidence answers
        - Flag low-confidence for manual review
        """
        if not answer_text:
            return 0.0
        
        confidence = 1.0
        
        # Short answers are more likely correct extractions
        if len(answer_text) > 200:
            confidence -= 0.2
        
        # Contains question text (student copied the question)
        if '?' in answer_text:
            confidence -= 0.3
        
        # Multiple lines suggest extraction grabbed too much
        if answer_text.count('\n') > 2:
            confidence -= 0.2
        
        # Very short might be truncated
        if len(answer_text) < 2:
            confidence -= 0.3
        
        return max(0.0, min(1.0, confidence))
    
    def _clean_answer(self, raw_text: str) -> str:
        """
        Clean up extracted answer text.
        
        Removes:
        - Extra whitespace
        - Common prefixes like "Answer:"
        - Trailing punctuation
        """
        if not raw_text:
            return ""
        
        text = raw_text.strip()
        
        # Remove common prefixes
        prefixes = ['answer:', 'ans:', 'solution:', '=']
        for prefix in prefixes:
            if text.lower().startswith(prefix):
                text = text[len(prefix):].strip()
        
        # Remove trailing punctuation (except needed ones like parentheses)
        text = text.rstrip('.,;:')
        
        return text