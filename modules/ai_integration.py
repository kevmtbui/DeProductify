"""
AI Integration module - Gemini API for semantic classification
Handles unknown apps via AI reasoning when heuristics fail
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Optional, Tuple
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class GeminiClassifier:
    """Gemini AI integration for productivity classification"""
    
    def __init__(self, api_key: Optional[str] = None, cache_dir: str = ".gemini_cache"):
        """
        Initialize Gemini classifier
        
        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
            cache_dir: Directory to store cached responses
        """
        # Get API key from parameter or environment variable
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Gemini API key not provided. Set GEMINI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        # Initialize Gemini
        genai.configure(api_key=self.api_key)
        # Use gemini-2.5-flash for fast responses, fallback to gemini-flash-latest
        try:
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        except Exception:
            # Fallback to latest flash if 2.5-flash not available
            self.model = genai.GenerativeModel('gemini-flash-latest')
        
        # Setup cache directory
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = self.cache_dir / "classification_cache.json"
        
        # Load existing cache
        self.cache = self._load_cache()
        
    def _load_cache(self) -> Dict[str, Dict]:
        """Load classification cache from disk"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    def _save_cache(self):
        """Save classification cache to disk"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except IOError:
            pass  # Silently fail if cache can't be written
    
    def _generate_cache_key(self, app_name: str, window_title: str, ocr_text: str) -> str:
        """Generate a unique cache key for the input combination"""
        # Normalize inputs for consistent caching
        combined = f"{app_name.lower().strip()}|{window_title.lower().strip()}|{ocr_text.lower().strip()}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def classify_productivity(
        self,
        app_name: str,
        window_title: str,
        ocr_text_snippet: str = "",
        force_refresh: bool = False
    ) -> Dict[str, any]:
        """
        Classify whether the current screen/app appears to be work/productivity-related
        
        Args:
            app_name: Name of the active application
            window_title: Title of the active window
            ocr_text_snippet: Snippet of text extracted via OCR (can be empty)
            force_refresh: Force API call even if cached result exists
            
        Returns:
            Dictionary with:
                - is_productive (bool): Whether the screen appears work-related
                - confidence (str): "confident" or "unsure"
                - reasoning (str): Brief explanation from Gemini
                - cached (bool): Whether result came from cache
        """
        # Generate cache key
        cache_key = self._generate_cache_key(app_name, window_title, ocr_text_snippet)
        
        # Check cache first (unless forced refresh)
        if not force_refresh and cache_key in self.cache:
            cached_result = self.cache[cache_key].copy()
            cached_result['cached'] = True
            return cached_result
        
        # Prepare prompt for Gemini
        prompt = self._build_classification_prompt(
            app_name, window_title, ocr_text_snippet
        )
        
        try:
            # Call Gemini API
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Parse Gemini response
            classification = self._parse_gemini_response(result_text)
            
            # Store in cache
            classification['cached'] = False
            self.cache[cache_key] = classification.copy()
            self._save_cache()
            
            return classification
            
        except Exception as e:
            # On API error, return unsure classification
            return {
                'is_productive': False,
                'confidence': 'unsure',
                'reasoning': f'API error: {str(e)}',
                'cached': False
            }
    
    def _build_classification_prompt(
        self,
        app_name: str,
        window_title: str,
        ocr_text_snippet: str
    ) -> str:
        """Build the prompt sent to Gemini"""
        
        prompt = f"""Analyze the following computer screen context and determine if it appears to be a work or productivity-related environment.

Application Name: {app_name}
Window Title: {window_title}
Visible Text Content: {ocr_text_snippet[:500] if ocr_text_snippet else "(no text detected)"}

Please analyze this and respond in the following JSON format:
{{
    "is_productive": true/false,
    "confidence": "confident" or "unsure",
    "reasoning": "brief explanation of your classification"
}}

Consider indicators of productivity:
- Educational content (lectures, textbooks, assignments)
- Coding/development environments
- Office applications (Word, Excel, presentations)
- Research and writing
- Mathematical/scientific notation
- Professional tools

Respond ONLY with valid JSON, no additional text."""

        return prompt
    
    def _parse_gemini_response(self, response_text: str) -> Dict[str, any]:
        """
        Parse Gemini's response into structured classification
        
        Args:
            response_text: Raw response text from Gemini
            
        Returns:
            Dictionary with classification results
        """
        # Try to extract JSON from response
        try:
            # Look for JSON in the response
            import re
            json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                return {
                    'is_productive': bool(parsed.get('is_productive', False)),
                    'confidence': parsed.get('confidence', 'unsure').lower(),
                    'reasoning': parsed.get('reasoning', 'No reasoning provided')
                }
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # Fallback: try to infer from text if JSON parsing fails
        response_lower = response_text.lower()
        
        # Look for productivity indicators in text
        if any(word in response_lower for word in ['productive', 'work', 'professional', 'educational']):
            productive = 'not productive' not in response_lower
        else:
            productive = False
        
        # Determine confidence
        if 'confident' in response_lower:
            confidence = 'confident'
        else:
            confidence = 'unsure'
        
        return {
            'is_productive': productive,
            'confidence': confidence,
            'reasoning': response_text[:200]  # First 200 chars as reasoning
        }
    
    def clear_cache(self):
        """Clear the classification cache"""
        self.cache = {}
        if self.cache_file.exists():
            self.cache_file.unlink()
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get statistics about the cache"""
        return {
            'total_entries': len(self.cache),
            'cached_entries': sum(1 for entry in self.cache.values() if entry.get('cached', False)),
        }


def create_classifier(api_key: Optional[str] = None) -> GeminiClassifier:
    """
    Factory function to create a GeminiClassifier instance
    
    Args:
        api_key: Optional API key (defaults to GEMINI_API_KEY env var)
        
    Returns:
        Configured GeminiClassifier instance
    """
    return GeminiClassifier(api_key=api_key)


# Example usage function (for testing)
def classify_example():
    """Example of how to use the classifier"""
    try:
        classifier = create_classifier()
        
        # Example classification
        result = classifier.classify_productivity(
            app_name="Visual Studio Code",
            window_title="main.py - DeProductify - Visual Studio Code",
            ocr_text_snippet="import customtkinter as ctk\n\nclass DeProductifyGUI"
        )
        
        print("Classification Result:")
        print(f"  Is Productive: {result['is_productive']}")
        print(f"  Confidence: {result['confidence']}")
        print(f"  Reasoning: {result['reasoning']}")
        print(f"  Cached: {result['cached']}")
        
        return result
        
    except Exception as e:
        print(f"Error: {e}")
        return None


if __name__ == "__main__":
    # Test the classifier
    classify_example()
