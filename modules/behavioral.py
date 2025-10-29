"""
Behavioral detection module - Keyboard activity and typing patterns
Tracks keypress frequency and typing duration to detect productivity
"""

import time
from typing import Dict, Optional, Tuple
from collections import deque
from threading import Thread, Event

# Try to import keyboard monitoring library
try:
    from pynput import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
    keyboard = None
    print("Warning: pynput not available. Install with: pip install pynput")


class KeyboardTracker:
    """
    Tracks keyboard activity and detects productive typing patterns.
    
    Features:
    - Counts total keypresses (doesn't log content)
    - Tracks typing frequency
    - Detects steady typing for long periods
    - Flags productive typing activity
    """
    
    def __init__(self, 
                 steady_typing_threshold: float = 15.0,  # seconds of steady typing
                 keypress_rate_threshold: float = 2.0,  # keys per second for "steady"
                 word_detection_threshold: int = 5):  # minimum keypresses to consider a word
        """
        Initialize keyboard tracker.
        
        Args:
            steady_typing_threshold: How many seconds of steady typing to flag as productive
            keypress_rate_threshold: Minimum keys per second to consider "steady typing"
            word_detection_threshold: Minimum keypresses to consider typing a word
        """
        self.steady_typing_threshold = steady_typing_threshold
        self.keypress_rate_threshold = keypress_rate_threshold
        self.word_detection_threshold = word_detection_threshold
        
        # Tracking state
        self.total_keypresses = 0
        self.keypress_history: deque = deque(maxlen=1000)  # Store timestamps of last 1000 keypresses
        self.typing_start_time: Optional[float] = None
        self.last_keypress_time: Optional[float] = None
        
        # Threading for background monitoring
        self.monitoring = False
        self.monitor_thread: Optional[Thread] = None
        self.stop_event = Event()
        
        # Statistics
        self.statistics = {
            'total_keypresses': 0,
            'keys_per_second': 0.0,
            'current_typing_duration': 0.0,
            'is_typing_steadily': False,
            'word_estimate': 0  # Estimate based on keypresses (rough: ~5 keys per word)
        }
    
    def _on_keypress(self, key):
        """Callback for keypress events (internal use)."""
        try:
            # Only count printable keys, ignore modifiers
            if hasattr(key, 'char') and key.char is not None:
                # Regular character key
                self.total_keypresses += 1
                current_time = time.time()
                self.keypress_history.append(current_time)
                self.last_keypress_time = current_time
                
                # Track typing start
                if self.typing_start_time is None:
                    self.typing_start_time = current_time
                
            elif key == keyboard.Key.space or key == keyboard.Key.enter:
                # Space and Enter also count as productive keypresses
                self.total_keypresses += 1
                current_time = time.time()
                self.keypress_history.append(current_time)
                self.last_keypress_time = current_time
                
                if self.typing_start_time is None:
                    self.typing_start_time = current_time
                    
        except Exception as e:
            # Silently ignore errors to prevent breaking the listener
            pass
    
    def _update_statistics(self):
        """Update internal statistics from keypress history."""
        current_time = time.time()
        
        # Calculate keys per second from recent history
        if len(self.keypress_history) > 1:
            time_window = 5.0  # Look at last 5 seconds
            cutoff_time = current_time - time_window
            
            recent_keypresses = [
                ts for ts in self.keypress_history 
                if ts >= cutoff_time
            ]
            
            if len(recent_keypresses) > 0:
                time_span = recent_keypresses[-1] - recent_keypresses[0]
                if time_span > 0:
                    self.statistics['keys_per_second'] = len(recent_keypresses) / time_span
                else:
                    self.statistics['keys_per_second'] = len(recent_keypresses)
            else:
                self.statistics['keys_per_second'] = 0.0
        else:
            self.statistics['keys_per_second'] = 0.0
        
        # Calculate current typing duration
        if self.typing_start_time:
            self.statistics['current_typing_duration'] = current_time - self.typing_start_time
        else:
            self.statistics['current_typing_duration'] = 0.0
        
        # Check if typing steadily (high rate + long duration)
        keys_per_sec = self.statistics['keys_per_second']
        typing_duration = self.statistics['current_typing_duration']
        
        self.statistics['is_typing_steadily'] = (
            keys_per_sec >= self.keypress_rate_threshold and
            typing_duration >= self.steady_typing_threshold
        )
        
        # Estimate words typed (rough: ~5 keypresses per word)
        self.statistics['word_estimate'] = self.total_keypresses // 5
        
        self.statistics['total_keypresses'] = self.total_keypresses
    
    def start_monitoring(self):
        """Start background keyboard monitoring."""
        if not KEYBOARD_AVAILABLE:
            raise ImportError("pynput library is required. Install with: pip install pynput")
        
        if self.monitoring:
            return  # Already monitoring
        
        self.monitoring = True
        self.stop_event.clear()
        
        # Start keyboard listener in a separate thread
        def monitor_keyboard():
            try:
                with keyboard.Listener(on_press=self._on_keypress) as listener:
                    while not self.stop_event.is_set():
                        self._update_statistics()
                        time.sleep(0.1)  # Update stats every 100ms
                    listener.stop()
            except Exception as e:
                print(f"Error in keyboard monitoring: {e}")
        
        self.monitor_thread = Thread(target=monitor_keyboard, daemon=True)
        self.monitor_thread.start()
        
        print("⌨️  Keyboard activity tracking started")
    
    def stop_monitoring(self):
        """Stop background keyboard monitoring."""
        if not self.monitoring:
            return
        
        self.monitoring = False
        self.stop_event.set()
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        
        print("⌨️  Keyboard activity tracking stopped")
    
    def reset_typing_session(self):
        """Reset current typing session (when window changes or activity stops)."""
        self.typing_start_time = None
        self.last_keypress_time = None
    
    def get_typing_statistics(self) -> Dict:
        """
        Get current typing statistics.
        
        Returns:
            Dictionary with:
            - total_keypresses: Total keypresses since start
            - keys_per_second: Current typing rate
            - current_typing_duration: How long current typing session has lasted
            - is_typing_steadily: Whether typing steadily for long period
            - word_estimate: Rough estimate of words typed
        """
        self._update_statistics()
        return self.statistics.copy()
    
    def detect_productive_typing(self) -> Tuple[bool, str]:
        """
        Detect if user is typing productively.
        
        Returns:
            Tuple of (is_productive, reason):
            - is_productive: True if productive typing detected
            - reason: String explaining why
        """
        self._update_statistics()
        
        stats = self.statistics
        
        # Check for steady typing over long period
        if stats['is_typing_steadily']:
            return True, f"Steady typing for {stats['current_typing_duration']:.1f}s ({stats['keys_per_second']:.1f} keys/sec)"
        
        # Check for high typing rate (many words/sentences)
        if stats['keys_per_second'] >= self.keypress_rate_threshold * 2:  # Very fast typing
            return True, f"High typing rate: {stats['keys_per_second']:.1f} keys/sec"
        
        # Check for many total keypresses (lots of words typed)
        if stats['word_estimate'] >= 100:  # ~100+ words typed
            return True, f"Many words typed: ~{stats['word_estimate']} words"
        
        return False, "No productive typing pattern detected"
    
    def get_activity_score(self) -> float:
        """
        Get productivity score based on keyboard activity (0.0 - 1.0).
        
        Returns:
            Score from 0.0 to 1.0 based on typing patterns
        """
        self._update_statistics()
        
        stats = self.statistics
        score = 0.0
        
        # Steady typing for long period (0.4 points)
        if stats['is_typing_steadily']:
            score += 0.4
        
        # High typing rate (0.3 points)
        if stats['keys_per_second'] >= self.keypress_rate_threshold * 1.5:
            score += 0.3
        
        # Many words typed (0.2 points)
        if stats['word_estimate'] >= 50:
            score += 0.2
        
        # Recent activity (0.1 points)
        if stats['current_typing_duration'] > 0 and stats['keys_per_second'] > 0:
            score += 0.1
        
        return min(score, 1.0)

# Convenience function for testing
def test_keyboard_tracking(duration: float = 30.0):
    """
    Test keyboard tracking for a specified duration.
    
    Args:
        duration: How long to track (seconds)
    """
    if not KEYBOARD_AVAILABLE:
        print("pynput library not available!")
        print("Install with: pip install pynput")
        return
    
    tracker = KeyboardTracker()
    tracker.start_monitoring()
    
    print(f"\nTracking keyboard activity for {duration} seconds...")
    print("Start typing to see activity detected!\n")
    
    start_time = time.time()
    last_print = 0
    
    try:
        while (time.time() - start_time) < duration:
            time.sleep(1)
            
            stats = tracker.get_typing_statistics()
            is_productive, reason = tracker.detect_productive_typing()
            
            # Print stats every 3 seconds
            if int(time.time() - last_print) >= 3:
                print(f"Keys: {stats['total_keypresses']} | "
                      f"Rate: {stats['keys_per_second']:.1f} keys/sec | "
                      f"Duration: {stats['current_typing_duration']:.1f}s | "
                      f"Words: ~{stats['word_estimate']}")
                
                if is_productive:
                    print(f"PRODUCTIVE: {reason}")
                
                last_print = time.time()
    
    except KeyboardInterrupt:
        pass
    finally:
        tracker.stop_monitoring()
        
        final_stats = tracker.get_typing_statistics()
        print(f"\nFinal Statistics:")
        print(f"  Total keypresses: {final_stats['total_keypresses']}")
        print(f"  Words typed: ~{final_stats['word_estimate']}")
        print(f"  Average rate: {final_stats['keys_per_second']:.1f} keys/sec")


if __name__ == "__main__":
    # Test keyboard tracking
    print("DeProductify - Keyboard Activity Tracking Test\n")
    test_keyboard_tracking(duration=30)


