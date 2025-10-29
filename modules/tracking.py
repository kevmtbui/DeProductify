"""
Tracking module - Window and system activity monitoring
Handles active window detection, app persistence tracking, and tab bar parsing
"""

import time
import re
import subprocess
from typing import Dict, Optional, Tuple, List
from collections import deque
import pygetwindow as gw
import numpy as np

# Optional audio detection - gracefully handle if not available
try:
    import sounddevice as sd
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    sd = None


class WindowTracker:
    """Tracks active windows and detects productivity indicators"""
    
    # Productive app patterns (case-insensitive matching)
    PRODUCTIVE_APPS = {
        # IDEs and Code Editors
        'visual studio code', 'vscode', 'pycharm', 'intellij', 'xcode',
        'sublime text', 'atom', 'vim', 'emacs', 'code editor',
        'cursor', 'cursor editor',
        
        # Document Editors
        'microsoft word', 'word', 'google docs', 'pages',
        'microsoft excel', 'excel', 'google sheets', 'numbers',
        'microsoft powerpoint', 'powerpoint', 'keynote', 'presentation',
        
        # Note-taking and Study
        'notion', 'obsidian', 'onenote', 'evernote', 'roam research',
        'anki', 'quizlet', 'canvas', 'blackboard', 'moodle',
        'quercus', 'student portal', 'course',
        
        # Communication (work-related)
        'slack', 'microsoft teams', 'zoom', 'webex', 'google meet',
        
        # PDF and Research
        'adobe acrobat', 'pdf reader', 'zotero', 'mendeley', 'refworks',
        
        # Terminal and System
        'terminal', 'iterm', 'warp', 'command line',
        
        # Browsers (will check tabs separately)
        'chrome', 'google chrome', 'firefox', 'safari', 'edge',
        'brave', 'opera', 'arc'
    }
    
    # Non-productive app patterns (for filtering)
    NON_PRODUCTIVE_APPS = {
        'spotify', 'apple music', 'music', 'itunes',
        'netflix', 'youtube', 'disney+', 'hulu', 'prime video',
        'instagram', 'facebook', 'twitter', 'tiktok', 'reddit',
        'games', 'steam', 'epic games'
    }
    
    # Productive website patterns (for browser tab detection)
    PRODUCTIVE_SITES = {
        'github', 'gitlab', 'stack overflow', 'stackoverflow',
        'docs.google.com', 'drive.google.com', 'classroom.google.com',
        'canvas', 'blackboard', 'moodle', 'quercus',
        'notion', 'obsidian', 'overleaf', 'latex',
        'jupyter', 'colab', 'kaggle',
        'coursera', 'edx', 'udemy', 'khan academy',
        'wikipedia', 'scholar.google.com', 'pubmed',
        'arxiv.org', 'ieee', 'acm.org'
    }
    
    # Non-productive site patterns
    NON_PRODUCTIVE_SITES = {
        'youtube.com', 'youtu.be', 'netflix.com', 'hulu.com',
        'instagram.com', 'facebook.com', 'twitter.com', 'x.com',
        'reddit.com', 'tiktok.com', 'pinterest.com',
        'spotify.com', 'soundcloud.com'
    }
    
    def __init__(self, focus_duration_threshold: float = 60.0, 
                 silence_duration_threshold: float = 10.0,
                 silence_volume_threshold: float = 0.01):
        """
        Initialize window tracker
        
        Args:
            focus_duration_threshold: Seconds of continuous focus before considering it productive (default: 1 minute)
            silence_duration_threshold: Seconds of silence before flagging (default: 10 seconds)
            silence_volume_threshold: Volume level below which is considered silent (0.0-1.0)
        """
        self.focus_duration_threshold = focus_duration_threshold
        self.silence_duration_threshold = silence_duration_threshold
        self.silence_volume_threshold = silence_volume_threshold
        
        # Track window history
        self.window_history: deque = deque(maxlen=100)  # Store last 100 window states
        self.current_window: Optional[Dict] = None
        self.window_start_time: Optional[float] = None
        
        # Track app persistence
        self.app_persistence: Dict[str, float] = {}  # app_name -> total_time_focused
        
        # Track silence
        self.last_audio_detection_time: Optional[float] = None
        self.silence_start_time: Optional[float] = None
        
    def get_active_window(self) -> Optional[Dict]:
        """
        Get the currently active window
        
        Returns:
            Dictionary with:
                - app_name: Name of the application
                - window_title: Full window title
                - timestamp: When window was detected
            Returns None if no window is active
        """
        try:
            windows = gw.getActiveWindow()
            
            if windows:
                # Get window title
                window_title = ''
                if hasattr(windows, 'title'):
                    title_attr = windows.title
                    if callable(title_attr):
                        window_title = title_attr()
                    else:
                        window_title = str(title_attr)
                else:
                    window_title = str(windows)
                
                # Get app name
                app_name = window_title  # Default to title
                
                # Try to get proper app name (better on macOS/Linux)
                try:
                    if hasattr(windows, 'app_name'):
                        app_name_attr = windows.app_name
                        if callable(app_name_attr):
                            app_name = app_name_attr()
                        else:
                            app_name = str(app_name_attr)
                    elif hasattr(windows, 'process'):
                        process_attr = windows.process
                        if callable(process_attr):
                            app_name = process_attr()
                        else:
                            app_name = str(process_attr)
                except Exception:
                    pass
                
                # Extract app name from title if needed (e.g., "Document - App Name")
                if ' - ' in window_title:
                    parts = window_title.split(' - ')
                    if len(parts) > 1:
                        app_name = parts[-1].strip()
                
                window_info = {
                    'app_name': app_name,
                    'window_title': window_title,
                    'timestamp': time.time()
                }
                
                return window_info
                
        except Exception as e:
            # Window tracking may fail silently
            return None
            
        return None
    
    def detect_app_interface(self, window_info: Optional[Dict] = None) -> Tuple[bool, str]:
        """
        Detect if the active window is a productive app interface
        
        Args:
            window_info: Window info dict (if None, gets current window)
            
        Returns:
            Tuple of (is_productive, app_name)
        """
        if window_info is None:
            window_info = self.get_active_window()
            
        if not window_info:
            return False, "Unknown"
        
        app_name = window_info.get('app_name', '').lower()
        window_title = window_info.get('window_title', '').lower()
        
        # Check against productive apps
        for productive_app in self.PRODUCTIVE_APPS:
            if productive_app in app_name or productive_app in window_title:
                # Skip if it's a non-productive match (e.g., "spotify" in "spotify")
                if app_name in self.NON_PRODUCTIVE_APPS:
                    continue
                return True, window_info.get('app_name', 'Unknown')
        
        # Check against non-productive apps
        for non_productive in self.NON_PRODUCTIVE_APPS:
            if non_productive in app_name or non_productive in window_title:
                return False, window_info.get('app_name', 'Unknown')
        
        return False, window_info.get('app_name', 'Unknown')
    
    def parse_tab_bar(self, window_title: str) -> Dict[str, any]:
        """
        Parse browser tab information from window title
        
        Args:
            window_title: Full window title from browser
            
        Returns:
            Dictionary with:
                - is_browser: Whether this is a browser window
                - tab_count: Number of tabs (if detectable)
                - current_tab: Current tab title/URL
                - is_productive_tab: Whether current tab appears productive
        """
        title_lower = window_title.lower()
        result = {
            'is_browser': False,
            'tab_count': 0,
            'current_tab': '',
            'is_productive_tab': False
        }
        
        # Detect browser patterns
        browser_patterns = ['chrome', 'firefox', 'safari', 'edge', 'brave', 'opera', 'arc']
        is_browser = any(pattern in title_lower for pattern in browser_patterns)
        
        if not is_browser:
            return result
        
        result['is_browser'] = True
        
        # Extract tab information
        # Common patterns:
        # "Page Title - Google Chrome"
        # "Page Title | Website - Browser"
        # "Tab Name - Browser"
        
        # Remove browser name from title to get tab info
        for browser in browser_patterns:
            if browser in title_lower:
                tab_part = window_title
                # Remove browser suffix
                patterns_to_remove = [
                    f' - {browser.title()}',
                    f' | {browser.title()}',
                    f' - {browser}',
                    f' | {browser}'
                ]
                for pattern in patterns_to_remove:
                    if window_title.endswith(pattern):
                        tab_part = window_title[:-len(pattern)].strip()
                        break
                
                result['current_tab'] = tab_part
                
                # Check if tab is productive
                tab_lower = tab_part.lower()
                
                # Check productive sites
                for site in self.PRODUCTIVE_SITES:
                    if site in tab_lower:
                        result['is_productive_tab'] = True
                        break
                
                # Check non-productive sites
                if not result['is_productive_tab']:
                    for site in self.NON_PRODUCTIVE_SITES:
                        if site in tab_lower:
                            result['is_productive_tab'] = False
                            break
                
                # Try to detect tab count (some browsers show "Tab Name (2) - Browser")
                tab_count_match = re.search(r'\((\d+)\)', window_title)
                if tab_count_match:
                    result['tab_count'] = int(tab_count_match.group(1))
                
                break
        
        return result
    
    def detect_tab_bar_overload(self, window_title: str, threshold: int = 5) -> bool:
        """
        Detect if browser has too many tabs (tab bar overload)
        
        Args:
            window_title: Window title to analyze
            threshold: Minimum number of tabs to consider "overload" (default: 5)
            
        Returns:
            True if tab bar appears overloaded
        """
        tab_info = self.parse_tab_bar(window_title)
        
        if not tab_info['is_browser']:
            return False
        
        # If we can detect tab count directly
        if tab_info['tab_count'] > 0:
            return tab_info['tab_count'] >= threshold
        
        # Heuristic: If title is very long, might indicate multiple tabs
        # Browser titles can get long with many tabs
        if len(window_title) > 100:  # Arbitrary threshold
            return True
        
        return False
    
    def track_window_focus(self, window_info: Optional[Dict] = None) -> Dict[str, any]:
        """
        Track active window focus and persistence
        
        Args:
            window_info: Window info dict (if None, gets current window)
            
        Returns:
            Dictionary with:
                - current_window: Current window info
                - is_productive_app: Whether app is productive
                - focus_duration: How long current window has been focused
                - app_total_time: Total time this app has been focused
                - window_changed: Whether window changed since last check
        """
        if window_info is None:
            window_info = self.get_active_window()
        
        result = {
            'current_window': window_info,
            'is_productive_app': False,
            'focus_duration': 0.0,
            'app_total_time': 0.0,
            'window_changed': False
        }
        
        if not window_info:
            self.window_start_time = None
            return result
        
        current_time = time.time()
        app_name = window_info.get('app_name', 'Unknown')
        
        # Check if window changed
        window_changed = False
        if self.current_window is None:
            window_changed = True
        elif self.current_window.get('app_name') != app_name:
            window_changed = True
        elif self.current_window.get('window_title') != window_info.get('window_title'):
            window_changed = True
        
        if window_changed:
            self.window_start_time = current_time
            self.current_window = window_info
        
        # Calculate focus duration
        if self.window_start_time:
            result['focus_duration'] = current_time - self.window_start_time
        
        # Update app persistence tracking
        if app_name not in self.app_persistence:
            self.app_persistence[app_name] = 0.0
        
        # Increment total time (approximate - updates on each check)
        if not window_changed and result['focus_duration'] > 0:
            self.app_persistence[app_name] = result['focus_duration']
        
        result['app_total_time'] = self.app_persistence.get(app_name, 0.0)
        
        # Detect if productive
        is_productive, _ = self.detect_app_interface(window_info)
        result['is_productive_app'] = is_productive
        
        # Add to history
        self.window_history.append({
            'window': window_info,
            'timestamp': current_time,
            'is_productive': is_productive
        })
        
        return result
    
    def get_continuous_focus_duration(self, app_name: Optional[str] = None) -> float:
        """
        Get how long the current app has been continuously focused
        
        Args:
            app_name: Specific app to check (if None, uses current window)
            
        Returns:
            Duration in seconds
        """
        if not self.window_start_time:
            return 0.0
        
        if app_name:
            if self.current_window and self.current_window.get('app_name') == app_name:
                return time.time() - self.window_start_time
            return 0.0
        
        return time.time() - self.window_start_time if self.window_start_time else 0.0
    
    def should_trigger_protocol(self, 
                                require_focus_duration: bool = True,
                                min_focus_seconds: Optional[float] = None) -> Tuple[bool, str]:
        """
        Determine if performative protocol should be triggered based on window tracking
        
        Args:
            require_focus_duration: Whether to require minimum focus duration
            min_focus_seconds: Minimum seconds of focus (defaults to focus_duration_threshold)
            
        Returns:
            Tuple of (should_trigger, reason)
        """
        focus_info = self.track_window_focus()
        
        if not focus_info['current_window']:
            return False, "No active window"
        
        # Check if productive app
        if focus_info['is_productive_app']:
            # Check focus duration if required
            if require_focus_duration:
                min_duration = min_focus_seconds or self.focus_duration_threshold
                if focus_info['focus_duration'] >= min_duration:
                    return True, f"Productive app '{focus_info['current_window'].get('app_name')}' focused for {focus_info['focus_duration']:.1f}s"
                return False, f"Productive app but only focused for {focus_info['focus_duration']:.1f}s"
            return True, f"Productive app detected: {focus_info['current_window'].get('app_name')}"
        
        # Check tab bar overload (browser with many tabs)
        window_title = focus_info['current_window'].get('window_title', '')
        if self.detect_tab_bar_overload(window_title):
            tab_info = self.parse_tab_bar(window_title)
            if tab_info['is_productive_tab']:
                return True, f"Browser with overloaded tabs + productive site: {tab_info['current_tab']}"
        
        return False, "No productivity indicators detected"
    
    def detect_system_audio_output(self) -> Tuple[bool, float]:
        """
        Detect if system audio output is playing (macOS)
        
        Returns:
            Tuple of (is_playing, volume_level)
            is_playing: True if audio is detected
            volume_level: Volume level (0.0-1.0)
        """
        try:
            # On macOS, check system audio output levels
            result = subprocess.run(
                ['osascript', '-e', 'output volume of (get volume settings)'],
                capture_output=True,
                text=True,
                timeout=1
            )
            if result.returncode == 0:
                volume = int(result.stdout.strip()) / 100.0  # Convert to 0-1 scale
                # If volume is muted or very low, consider it silent
                if volume < self.silence_volume_threshold:
                    return False, volume
                
                # Check if audio is actually playing (requires additional check)
                # For now, if volume is up, assume audio might be playing
                # This is a heuristic - perfect detection would require more complex system calls
                return volume > self.silence_volume_threshold, volume
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError, ValueError):
            pass
        
        # Default: assume no audio if we can't detect
        return False, 0.0
    
    def detect_microphone_audio(self, sample_duration: float = 0.5) -> Tuple[bool, float]:
        """
        Detect if microphone is picking up audio
        
        Args:
            sample_duration: How long to sample audio in seconds (default: 0.5s)
            
        Returns:
            Tuple of (has_audio, max_volume)
            has_audio: True if audio above threshold detected
            max_volume: Maximum volume level detected (0.0-1.0)
        """
        if not AUDIO_AVAILABLE:
            # If sounddevice not available, return no audio
            return False, 0.0
        
        try:
            # Sample rate and duration
            sample_rate = 44100
            samples = int(sample_duration * sample_rate)
            
            # Record audio sample
            audio_data = sd.rec(
                samples,
                samplerate=sample_rate,
                channels=1,
                dtype='float32'
            )
            sd.wait()  # Wait for recording to finish
            
            # Calculate maximum volume (absolute value)
            max_volume = float(np.abs(audio_data).max())
            
            # Check if above threshold
            has_audio = max_volume > self.silence_volume_threshold
            
            return has_audio, max_volume
            
        except Exception:
            # If audio detection fails, assume no audio
            return False, 0.0
    
    def detect_silence(self) -> Dict[str, any]:
        """
        Detect if there's lack of system sounds and mic audio (silence)
        
        Returns:
            Dictionary with:
                - is_silent: True if silence detected
                - system_audio_playing: Whether system audio is detected
                - mic_audio_detected: Whether mic audio is detected
                - system_volume: System volume level (0.0-1.0)
                - mic_volume: Mic volume level detected (0.0-1.0)
                - silence_duration: How long silence has been detected
        """
        current_time = time.time()
        
        # Check system audio
        system_playing, system_volume = self.detect_system_audio_output()
        
        # Check microphone
        mic_detected, mic_volume = self.detect_microphone_audio(sample_duration=0.3)
        
        # Determine if silent
        is_silent = not system_playing and not mic_detected
        
        # Track silence duration
        if is_silent:
            if self.silence_start_time is None:
                self.silence_start_time = current_time
            silence_duration = current_time - self.silence_start_time
        else:
            self.silence_start_time = None
            silence_duration = 0.0
        
        self.last_audio_detection_time = current_time
        
        return {
            'is_silent': is_silent,
            'system_audio_playing': system_playing,
            'mic_audio_detected': mic_detected,
            'system_volume': system_volume,
            'mic_volume': mic_volume,
            'silence_duration': silence_duration
        }
    
    def should_trigger_protocol(self, 
                                require_focus_duration: bool = True,
                                min_focus_seconds: Optional[float] = None,
                                include_silence_check: bool = True) -> Tuple[bool, str]:
        """
        Determine if performative protocol should be triggered based on window tracking
        
        Args:
            require_focus_duration: Whether to require minimum focus duration
            min_focus_seconds: Minimum seconds of focus (defaults to focus_duration_threshold)
            include_silence_check: Whether to check for silence as a trigger
            
        Returns:
            Tuple of (should_trigger, reason)
        """
        focus_info = self.track_window_focus()
        
        if not focus_info['current_window']:
            return False, "No active window"
        
        # Check if productive app
        if focus_info['is_productive_app']:
            # Check focus duration if required
            if require_focus_duration:
                min_duration = min_focus_seconds or self.focus_duration_threshold
                if focus_info['focus_duration'] >= min_duration:
                    # Check silence if enabled
                    if include_silence_check:
                        silence_info = self.detect_silence()
                        if silence_info['is_silent'] and silence_info['silence_duration'] >= self.silence_duration_threshold:
                            return True, f"Productive app focused + silence detected ({silence_info['silence_duration']:.1f}s)"
                    return True, f"Productive app '{focus_info['current_window'].get('app_name')}' focused for {focus_info['focus_duration']:.1f}s"
                return False, f"Productive app but only focused for {focus_info['focus_duration']:.1f}s"
            
            # Check silence if enabled and no duration required
            if include_silence_check:
                silence_info = self.detect_silence()
                if silence_info['is_silent'] and silence_info['silence_duration'] >= self.silence_duration_threshold:
                    return True, f"Productive app + silence detected ({silence_info['silence_duration']:.1f}s)"
            
            return True, f"Productive app detected: {focus_info['current_window'].get('app_name')}"
        
        # Check tab bar overload (browser with many tabs)
        window_title = focus_info['current_window'].get('window_title', '')
        if self.detect_tab_bar_overload(window_title):
            tab_info = self.parse_tab_bar(window_title)
            if tab_info['is_productive_tab']:
                return True, f"Browser with overloaded tabs + productive site: {tab_info['current_tab']}"
        
        return False, "No productivity indicators detected"


def create_tracker(focus_duration_threshold: float = 60.0,
                   silence_duration_threshold: float = 10.0) -> WindowTracker:
    """
    Factory function to create a WindowTracker instance
    
    Args:
        focus_duration_threshold: Seconds of continuous focus before considering productive (default: 1 minute)
        silence_duration_threshold: Seconds of silence before flagging (default: 10 seconds)
        
    Returns:
        Configured WindowTracker instance
    """
    return WindowTracker(
        focus_duration_threshold=focus_duration_threshold,
        silence_duration_threshold=silence_duration_threshold
    )

# Example usage
if __name__ == "__main__":
    tracker = create_tracker()
    
    print("Testing Window Tracker...")
    print("=" * 60)
    
    # Get current window
    window = tracker.get_active_window()
    if window:
        print(f"Current Window: {window.get('app_name')} - {window.get('window_title')}")
        
        # Test app interface detection
        is_productive, app_name = tracker.detect_app_interface(window)
        print(f"App Interface Detection: {is_productive} ({app_name})")
        
        # Test tab bar parsing
        tab_info = tracker.parse_tab_bar(window.get('window_title', ''))
        print(f"Tab Info: {tab_info}")
        
        # Test focus tracking
        focus_info = tracker.track_window_focus(window)
        print(f"Focus Duration: {focus_info['focus_duration']:.1f}s")
        
        # Test protocol trigger
        should_trigger, reason = tracker.should_trigger_protocol(require_focus_duration=False)
        print(f"Should Trigger: {should_trigger} - {reason}")
        
        # Test silence detection
        silence_info = tracker.detect_silence()
        print(f"\nSilence Detection:")
        print(f"  Is Silent: {silence_info['is_silent']}")
        print(f"  System Audio Playing: {silence_info['system_audio_playing']}")
        print(f"  Mic Audio Detected: {silence_info['mic_audio_detected']}")
        print(f"  System Volume: {silence_info['system_volume']:.2f}")
        print(f"  Mic Volume: {silence_info['mic_volume']:.2f}")
        print(f"  Silence Duration: {silence_info['silence_duration']:.1f}s")
    else:
        print("No active window detected")

