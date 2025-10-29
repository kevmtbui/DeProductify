"""
Tracking module - Window and system activity monitoring
Handles active window detection, app persistence tracking, and tab bar parsing
"""

import time
import re
from typing import Dict, Optional, Tuple, List
from collections import deque
import pygetwindow as gw


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
    
    def __init__(self, focus_duration_threshold: float = 300.0):
        """
        Initialize window tracker
        
        Args:
            focus_duration_threshold: Seconds of continuous focus before considering it productive (default: 5 minutes)
        """
        self.focus_duration_threshold = focus_duration_threshold
        
        # Track window history
        self.window_history: deque = deque(maxlen=100)  # Store last 100 window states
        self.current_window: Optional[Dict] = None
        self.window_start_time: Optional[float] = None
        
        # Track app persistence
        self.app_persistence: Dict[str, float] = {}  # app_name -> total_time_focused
        
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


def create_tracker(focus_duration_threshold: float = 300.0) -> WindowTracker:
    """
    Factory function to create a WindowTracker instance
    
    Args:
        focus_duration_threshold: Seconds of continuous focus before considering productive
        
    Returns:
        Configured WindowTracker instance
    """
    return WindowTracker(focus_duration_threshold=focus_duration_threshold)


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
    else:
        print("No active window detected")
