"""
DeProductify - Main orchestrator
Detects productivity and triggers Performative Protocol
"""
from modules.detection import ProductivityDetector
from modules.tracking import WindowTracker

def main():
    print("DeProductify starting...\n")
    
    # Initialize productivity detector (OCR + Visual Heuristics)
    detector = ProductivityDetector()
    
    print("Testing OCR and visual detection...")
    print("Make sure you have a document/IDE open on your screen!\n")
    
    # Analyze current screen
    results = detector.analyze_screen()
    
    if 'error' in results:
        print(f"{results['error']}")
        return
    
    # Print results
    print("\n=== Detection Results ===")
    print(f"Productivity Score: {results['productivity_score']:.2f}")
    print(f"Triggers Activated: {results['triggers_activated']}")
    print(f"\nDetails:")
    print(f"  - Brightness: {results['brightness']:.1f} {'(BRIGHT DOC)' if results['bright_document'] else ''}")
    print(f"  - Text Density: {results['text_density']} words")
    print(f"  - Work Keywords: {results['work_keyword_count']} found")
    print(f"  - Lecture Content: {'Yes' if results['lecture_detected'] else 'No'}")
    print(f"  - Math Notation: {'Yes' if results['math_detected'] else 'No'}")

if __name__ == "__main__":
    main()