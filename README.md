# DeProductify

> "Detects when you're working too hard — and makes it look like you're not."

DeProductify is an AI-powered anti-productivity agent that monitors your screen and system activity to detect signs of serious focus — then automatically launches the **Performative Protocol™**, a carefully curated aesthetic intervention that replaces your grindset with a vibe.

Instead of blocking productivity, DeProductify masks it with an online persona: it turns your screen into the visual equivalent of a "study playlist girlie," complete with indie music, matcha, vinyls, and totebags.

---

## Objective

1. **Detect** when users are being too productive (studying, coding, writing reports)
2. **Trigger** the Performative Protocol, overlaying a soothing, curated "creative aesthetic"
3. **Use AI** (Gemini) to semantically understand unfamiliar productive screens
4. **Build** a technically impressive pipeline for screen monitoring + AI inference + visual overlay

---

## Core Features

### 1. Screen Monitoring Engine
**Description:** Captures screen frames & active window data in real time  
**Tools:** `mss`, `opencv-python`

### 2. OCR Text Extraction
**Description:** Reads visible text from screen to detect density and work keywords  
**Tools:** `pytesseract`

### 3. Heuristic Productivity Detection
**Description:** Identifies text-heavy or bright document screens, math notation, lecture slides, or IDEs  
**Tools:** OpenCV + heuristics

### 4. Active Window Tracking
**Description:** Monitors foreground application  
**Tools:** `pygetwindow`, OS APIs

### 5. Gemini Integration
**Description:** Classifies unknown pages or apps semantically ("does this look like work?")  
**Tools:** Gemini API

### 6. Performative Protocol Activation
**Description:** Plays "performative" music (Laufey, Clairo, Daniel Caesar, beabadoobee) and overlays aesthetic items (matcha, labubu, vinyls, books)  
**Tools:** `pygame`, `tkinter`, `webbrowser`, `pyautogui`

---

## Detection Triggers

DeProductify uses multiple detection methods across 4 modules to identify productivity:

| Trigger | Module | Detection Method |
|---------|--------|------------------|
| **Text-heavy screen** | OCR | Word density per frame |
| **Work keywords** | OCR | Keyword search |
| **App interface detection** | Window Tracker | Active window name |
| **Bright white document** | OpenCV | Average brightness threshold |
| **Tab bar overload** | Window Tracker | Window title parsing |
| **Lecture content** | OCR | Keywords: "Lecture", "Slide", "Chapter" |
| **Mathematical notation** | OCR | Keywords: "∫", "Σ", "θ", "proof", "equation" |
| **Active window focus** | Window Tracker | Track app persistence |
| **Typing / keypress** | Pyautogui | Event frequency (low priority) |
| **Continuous focus** | Timer | No window change for X minutes |
| **Silence** | Optional | Lack of music/video tab |
| **Gemini fallback** | AI Integration | Semantic classification of unknown screens |

---

## Technical Stack

### Screen Capture & Image Processing
- **mss** - Fast screen capture
- **opencv-python** - Image processing and analysis

### Text Recognition
- **pytesseract** - OCR for text extraction from screenshots

### System Tracking
- **pygetwindow** - Window and application tracking
- **pyautogui** - System automation and input detection

### GUI & Visual Overlay
- **pygame** - Audio playback and visual rendering
- **tkinter** - GUI framework (built into Python)
- **webbrowser** - Optional browser integration

### AI Integration
- **google-generativeai** - Gemini API client
- **requests** - HTTP requests

### Utilities
- **numpy** - Numerical operations
- **Pillow** - Image manipulation

---

## Project Structure

```
DeProductify/
├── modules/
│   ├── __init__.py
│   ├── detection.py      # OCR and heuristic productivity detection
│   ├── tracking.py       # Window and system activity monitoring
│   ├── ai_integration.py # Gemini API for semantic classification
│   └── overlay.py        # Performative Protocol visual/audio elements
├── assets/
│   ├── images/           # Overlay assets (matcha, vinyl, totebag, labubu, books)
│   └── audio/            # Music files (Laufey, Clairo, Daniel Caesar, beabadoobee)
├── main.py               # Main orchestrator
├── requirements.txt      # Python dependencies
└── venv/                 # Virtual environment
```

---

## Setup Instructions

### 1. Install Tesseract OCR (Required)

DeProductify requires Tesseract for OCR functionality. Install it via Homebrew:

```bash
brew install tesseract

# Verify installation
tesseract --version
```

### 2. Activate Virtual Environment

```bash
source venv/bin/activate
```

### 3. Install Python Dependencies

All dependencies are already installed in the virtual environment. If you need to reinstall:

```bash
pip install -r requirements.txt
```

### 4. Configure Gemini API

You'll need a Gemini API key for AI-based detection. Set it as an environment variable:

```bash
export GEMINI_API_KEY="your-api-key-here"
```

Or configure it in the `ai_integration.py` module.

### 5. Add Assets

Place your overlay assets in the appropriate directories:
- **Images:** `assets/images/` (PNG/JPG files for matcha, vinyl, totebag, labubu, books)
- **Audio:** `assets/audio/` (MP3/WAV files for music)

### 6. Run the App

```bash
python main.py
```

---

## Performative Protocol

When productivity is detected, DeProductify activates the Performative Protocol:

### Visual Elements
- **Aesthetic overlays**: Transparent overlays of matcha cups, vinyl records, totebags, labubu figurines, and books
- **Positioning**: Random or configurable positions on screen
- **Non-intrusive**: Overlays don't block user interaction

### Audio Elements
- **Indie music playlist**: Laufey, Clairo, Daniel Caesar, beabadoobee
- **Local playback**: Music files stored in `assets/audio/`
- **Ambient soundtrack**: Curated to match the "study playlist girlie" aesthetic

---

## Configuration

Default thresholds (temporary - will be configurable):

- **Text density**: >50 words per frame
- **Brightness threshold**: >200 (0-255 scale)
- **Focus duration**: 5+ minutes on same window
- **Work keywords**: 3+ matches in OCR text

These can be adjusted later based on testing and user preferences.

---

## Notes

- This is a hackathon project, not a production application
- Privacy: Screen capture may involve sensitive data
- Performance: Screen monitoring runs in background threads to keep GUI responsive
- Platform: macOS (with potential cross-platform support)

---

## Future Enhancements

- Configurable detection thresholds
- Customizable overlay assets
- Music playlist management
- User preferences panel
- Activity logging and analytics

---

## License

Hackathon project - for demonstration purposes only.

