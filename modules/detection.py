"""
Detection module - OCR and heuristic productivity detection

"""

import re
from typing import Optional, Dict, List, Tuple
import numpy as np
import cv2
import pytesseract
import mss
from PIL import Image


class ProductivityDetector:
    """
    Detects productivity using OCR and visual heuristics.
    
    Features:
    - OCR text extraction
    - Text density calculation
    - Work keyword detection
    - Bright white document detection
    - Lecture content detection
    - Mathematical notation detection
    - Productivity score computation
    """
    
    def __init__(self):
        """Initialize the productivity detector."""
        self.screen_capturer = mss.mss()
        
        # Thresholds (configurable)
        self.text_density_threshold = 300  # words per frame
        self.brightness_threshold = 200  # 0-255 scale (bright white docs)
        self.work_keyword_threshold = 3  # minimum keywords to flag
        
        # Work-related keywords
        self.work_keywords = [
            # Coding
            'import', 'def', 'function', 'class', 'return', 'const', 'var', 'let',
            'async', 'await', 'module', 'package', 'interface', 'type',
            # Academic
            'report', 'essay', 'thesis', 'chapter', 'section', 'paragraph',
            'assignment', 'homework', 'project', 'dissertation',
            # Documents
            'document', 'draft', 'revision', 'editing', 'review',
            # Academic content
            'lecture', 'exam', 'quiz', 'study', 'notes', 'summary',
            # General work
            'meeting', 'agenda', 'task', 'todo', 'deadline', 'due date',
            'presentation', 'slides', 'deck'
        ]
        
        # Lecture indicators
        self.lecture_keywords = [
            'lecture', 'slide', 'chapter', 'section', 'lesson',
            'unit', 'module', 'course', 'syllabus'
        ]
        
        # Mathematical notation patterns
        self.math_symbols = ['∫', 'Σ', '∑', 'θ', 'α', 'β', 'γ', 'Δ', 'δ', 'π', '∞', '√', '≤', '≥', '≠', '≈']
        self.math_keywords = ['proof', 'theorem', 'equation', 'formula', 'derivative', 
                            'integral', 'matrix', 'vector', 'calculus', 'algebra']
        
    def capture_screen(self) -> Optional[np.ndarray]:
        """
        Capture the current screen as a numpy array.
        
        Returns:
            numpy array of screen image (BGR format) or None if capture fails
        """
        try:
            # Capture primary monitor
            monitor = self.screen_capturer.monitors[1]  # monitors[0] is all monitors, [1] is primary
            screenshot = self.screen_capturer.grab(monitor)
            
            # Convert to numpy array and BGR format (for OpenCV)
            img = np.array(screenshot)
            # mss returns BGRA, convert to BGR
            img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            
            return img_bgr
        except Exception as e:
            print(f"Error capturing screen: {e}")
            return None
    
    def extract_text(self, image: np.ndarray) -> str:
        """
        Extract text from screen image using OCR.
        
        Args:
            image: numpy array image (BGR format)
            
        Returns:
            Extracted text string
        """
        try:
            # Convert BGR to RGB for PIL
            img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(img_rgb)
            
            # Perform OCR
            # Use pytesseract to extract text
            text = pytesseract.image_to_string(pil_image)
            
            return text
        except Exception as e:
            print(f"Error in OCR text extraction: {e}")
            return ""
    
    def calculate_brightness(self, image: np.ndarray) -> float:
        """
        Calculate average brightness of the screen.
        
        Args:
            image: numpy array image (BGR format)
            
        Returns:
            Average brightness value (0-255)
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Calculate mean brightness
            brightness = np.mean(gray)
            
            return float(brightness)
        except Exception as e:
            print(f"Error calculating brightness: {e}")
            return 0.0
    
    def detect_text_density(self, text: str) -> int:
        """
        Calculate text density (word count) from OCR text.
        
        Args:
            text: OCR extracted text
            
        Returns:
            Number of words detected
        """
        if not text:
            return 0
        
        # Simple word count (split by whitespace)
        words = text.split()
        return len(words)
    
    def search_keywords(self, text: str, keywords: List[str]) -> List[str]:
        """
        Search for keywords in text (case-insensitive).
        
        Args:
            text: Text to search in
            keywords: List of keywords to search for
            
        Returns:
            List of found keywords
        """
        if not text:
            return []
        
        text_lower = text.lower()
        found = []
        
        for keyword in keywords:
            if keyword.lower() in text_lower:
                found.append(keyword)
        
        return found
    
    def detect_work_keywords(self, text: str) -> Tuple[List[str], int]:
        """
        Detect work-related keywords in OCR text.
        
        Args:
            text: OCR extracted text
            
        Returns:
            Tuple of (found_keywords_list, count)
        """
        found = self.search_keywords(text, self.work_keywords)
        return found, len(found)
    
    def detect_lecture_content(self, text: str) -> bool:
        """
        Detect lecture/slide content indicators.
        
        Looks for: "Lecture", "Slide", "Chapter", "Slide 1/40", etc.
        
        Args:
            text: OCR extracted text
            
        Returns:
            True if lecture content detected
        """
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Check for lecture keywords
        found_keywords = self.search_keywords(text, self.lecture_keywords)
        if found_keywords:
            return True
        
        # Check for slide patterns like "Slide 1/40", "1/40", "Page 1 of 40"
        slide_patterns = [
            r'slide\s+\d+',  # "Slide 1", "Slide 10"
            r'\d+/\d+',       # "1/40", "10/100"
            r'page\s+\d+\s+of\s+\d+',  # "Page 1 of 40"
            r'chapter\s+\d+',  # "Chapter 1"
        ]
        
        for pattern in slide_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        
        return False
    
    def detect_math_notation(self, text: str) -> bool:
        """
        Detect mathematical notation and symbols.
        
        Looks for: ∫, Σ, θ, proof, theorem, equation, etc.
        
        Args:
            text: OCR extracted text
            
        Returns:
            True if mathematical notation detected
        """
        if not text:
            return False
        
        # Check for math symbols
        for symbol in self.math_symbols:
            if symbol in text:
                return True
        
        # Check for math keywords
        found_keywords = self.search_keywords(text, self.math_keywords)
        if found_keywords:
            return True
        
        # Check for equation patterns like "f(x) =", "y = mx + b"
        equation_patterns = [
            r'[a-z]\s*=\s*',  # "x =", "f(x) ="
            r'\d+\s*[+\-*/]\s*\d+',  # "2 + 2", "x * y"
            r'\([^)]+\)',  # Parentheses (common in math)
        ]
        
        for pattern in equation_patterns:
            if len(re.findall(pattern, text)) >= 2:  # Multiple occurrences suggest math
                return True
        
        return False
    
    def detect_bright_document(self, brightness: float) -> bool:
        """
        Detect bright white document screens.
        
        Args:
            brightness: Average brightness value (0-255)
            
        Returns:
            True if brightness exceeds threshold (bright white doc)
        """
        return brightness >= self.brightness_threshold
    
    def compute_visual_score(self, image: np.ndarray, ocr_text: Optional[str] = None) -> Dict:
        """
        Compute productivity score from visual heuristics.
        
        Args:
            image: Screen image (numpy array)
            ocr_text: Optional pre-extracted OCR text (if None, will extract)
            
        Returns:
            Dictionary with detection results and score:
            {
                'brightness': float,
                'bright_document': bool,
                'text_density': int,
                'work_keywords': List[str],
                'work_keyword_count': int,
                'lecture_detected': bool,
                'math_detected': bool,
                'productivity_score': float (0.0-1.0),
                'triggers_activated': int
            }
        """
        results = {
            'brightness': 0.0,
            'bright_document': False,
            'text_density': 0,
            'work_keywords': [],
            'work_keyword_count': 0,
            'lecture_detected': False,
            'math_detected': False,
            'productivity_score': 0.0,
            'triggers_activated': 0
        }
        
        # Calculate brightness
        brightness = self.calculate_brightness(image)
        results['brightness'] = brightness
        results['bright_document'] = self.detect_bright_document(brightness)
        
        # Extract text if not provided
        if ocr_text is None:
            ocr_text = self.extract_text(image)
        
        # Text density
        text_density = self.detect_text_density(ocr_text)
        results['text_density'] = text_density
        
        # Work keywords
        work_keywords, work_count = self.detect_work_keywords(ocr_text)
        results['work_keywords'] = work_keywords
        results['work_keyword_count'] = work_count
        
        # Lecture detection
        results['lecture_detected'] = self.detect_lecture_content(ocr_text)
        
        # Math detection
        results['math_detected'] = self.detect_math_notation(ocr_text)
        
        # Compute productivity score (0.0 - 1.0)
        # Each trigger contributes points
        triggers_activated = 0
        score_components = []
        
        # Bright document (0.3 points)
        if results['bright_document']:
            triggers_activated += 1
            score_components.append(0.3)
        
        # High text density (0.2 points if > threshold)
        if text_density >= self.text_density_threshold:
            triggers_activated += 1
            score_components.append(0.2)
        
        # Work keywords (0.2 points if >= threshold)
        if work_count >= self.work_keyword_threshold:
            triggers_activated += 1
            score_components.append(0.2)
        
        # Lecture content (0.15 points)
        if results['lecture_detected']:
            triggers_activated += 1
            score_components.append(0.15)
        
        # Math notation (0.15 points)
        if results['math_detected']:
            triggers_activated += 1
            score_components.append(0.15)
        
        # Total score (capped at 1.0)
        productivity_score = min(sum(score_components), 1.0)
        
        results['productivity_score'] = productivity_score
        results['triggers_activated'] = triggers_activated
        
        return results
    
    def analyze_screen(self) -> Dict:
        """
        Capture current screen and analyze for productivity.
        
        Returns:
            Dictionary with detection results
        """
        # Capture screen
        image = self.capture_screen()
        
        if image is None:
            return {
                'error': 'Failed to capture screen',
                'productivity_score': 0.0
            }
        
        # Analyze
        return self.compute_visual_score(image)


# Convenience function for quick testing
def test_detection():
    """Quick test function to analyze current screen."""
    detector = ProductivityDetector()
    results = detector.analyze_screen()
    
    print("\n=== Productivity Detection Results ===")
    print(f"Brightness: {results.get('brightness', 0):.1f} {'(BRIGHT DOC)' if results.get('bright_document') else ''}")
    print(f"Text Density: {results.get('text_density', 0)} words")
    print(f"Work Keywords: {results.get('work_keyword_count', 0)} found - {results.get('work_keywords', [])[:5]}")
    print(f"Lecture Content: {'DETECTED' if results.get('lecture_detected') else 'Not detected'}")
    print(f"Math Notation: {'DETECTED' if results.get('math_detected') else 'Not detected'}")
    print(f"\nProductivity Score: {results.get('productivity_score', 0.0):.2f}")
    print(f"Triggers Activated: {results.get('triggers_activated', 0)}")
    
    return results


if __name__ == "__main__":
    # Test the detection module
    print("DeProductify - OCR & Visual Detection Test\n")
    print("Capturing screen and analyzing...")
    
    try:
        results = test_detection()
    except Exception as e:
        print(f"Error: {e}")
        print("\nNote: Make sure Tesseract OCR is installed!")
        print("Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
