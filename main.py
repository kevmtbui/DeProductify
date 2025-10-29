"""
DeProductify - Main orchestrator
Detects productivity and triggers Performative Protocol

Combines all detection modules:
- Detection (OCR + Visual Heuristics)
- Tracking (Window + Focus)
- Behavioral (Keyboard Activity)
- AI Integration (Gemini fallback)
"""

import time
import platform
import subprocess
from typing import Dict, Optional, Tuple
from modules.detection import ProductivityDetector
from modules.tracking import WindowTracker
from modules.behavioral import KeyboardTracker

# Placeholder for overlay module (will be implemented by friend)
def trigger_performative_protocol(reason: str, productivity_score: float):
    """
    Trigger the Performative Protocol overlay.
    
    When overlay.py is ready, this will display:
    - Matcha clickable overlay (user must click to dismiss)
    - Random indie music (Laufey, Clairo, Daniel Caesar, beabadoobee)
    - Aesthetic items (vinyls, totebag, labubu, books)
    
    Args:
        reason: Why the protocol was triggered
        productivity_score: Combined productivity score that triggered it
    """
    # Try to use overlay module if available
    try:
        from modules.overlay import launch_performative_protocol
        # When overlay.py is fully implemented, this will launch it
        launch_performative_protocol(reason, productivity_score)
    except (ImportError, NotImplementedError):
        # Fallback placeholder until overlay is ready
        print("\n" + "="*60)
        print("PERFORMATIVE PROTOCOL™ ACTIVATED")
        print("="*60)
        print(f"Reason: {reason}")
        print(f"Productivity Score: {productivity_score:.2f}")
        print("\n[PLACEHOLDER] Overlay module will display:")
        print("  - Matcha clickable button (must click to dismiss)")
        print("  - Random music playback (indie playlist)")
        print("  - Aesthetic overlay elements")
        print("="*60 + "\n")


class DeProductifyOrchestrator:
    """
    Main orchestrator that combines all detection modules
    and decides when to trigger the Performative Protocol.
    """
    
    def __init__(self, 
                 productivity_threshold: float = 0.5,
                 check_interval: float = 2.0,
                 use_keyboard_tracking: bool = True,
                 cooldown_seconds: float = 120.0):
        """
        Initialize the orchestrator.
        
        Args:
            productivity_threshold: Combined score threshold to trigger protocol (0.0-1.0)
            check_interval: Seconds between productivity checks
            use_keyboard_tracking: Whether to track keyboard activity
            cooldown_seconds: Seconds to wait after triggering before checking again
        """
        self.productivity_threshold = productivity_threshold
        self.check_interval = check_interval
        self.cooldown_seconds = cooldown_seconds
        
        # Initialize all detection modules
        print("Initializing detection modules...")
        
        # OCR + Visual Detection
        self.detector = ProductivityDetector(use_gemini_fallback=True)
        print("  ✓ Detection module ready")
        
        # Window Tracking
        self.tracker = WindowTracker()
        print("  ✓ Window tracking ready")
        
        # Keyboard Tracking (optional)
        self.keyboard_tracker = None
        if use_keyboard_tracking:
            try:
                self.keyboard_tracker = KeyboardTracker()
                self.keyboard_tracker.start_monitoring()
                print("  ✓ Keyboard tracking ready")
            except Exception as e:
                print(f"  ⚠ Keyboard tracking unavailable: {e}")
        
        # State tracking
        self.last_trigger_time = 0
        self.is_in_cooldown = False
        self.monitoring = False
        self.game_detected = False
        self.last_game_check_time = 0
        self.game_check_interval = 5.0  # Check for games every 5 seconds
        
        # Warning system
        self.warning_thresholds = {
            0.3: "You're starting to look productive...",
            0.4: "Productivity levels rising... take a break?",
            0.45: "Warning: You're looking TOO productive!",
        }
        self.last_warning_level = 0
        self.warning_cooldown = 30.0  # Don't spam warnings (30s between warnings)
        self.last_warning_time = 0
        
        print("\nDeProductify ready! Monitoring your productivity...\n")
        print("Game detection enabled - triggers disabled while gaming")
        print("Warning notifications enabled - you'll be alerted as productivity climbs\n")
    
    def get_combined_productivity_score(self) -> Dict:
        """
        Aggregate scores from all detection modules.
        
        Returns:
            Dictionary with:
            - combined_score: Total productivity score (0.0-1.0)
            - detection_score: OCR/visual detection score
            - tracking_score: Window tracking score
            - keyboard_score: Keyboard activity score
            - triggers: List of active triggers
            - reason: Human-readable reason for score
        """
        results = {
            'combined_score': 0.0,
            'detection_score': 0.0,
            'tracking_score': 0.0,
            'keyboard_score': 0.0,
            'triggers': [],
            'reason': ''
        }
        
        # 1. Detection Module (OCR + Visual) - Weight: 40%
        try:
            # Get window info for better context
            window_info = self.tracker.get_active_window()
            app_name = window_info.get('app_name', '') if window_info else ''
            window_title = window_info.get('window_title', '') if window_info else ''
            
            detection_results = self.detector.analyze_screen(
                app_name=app_name,
                window_title=window_title
            )
            
            detection_score = detection_results.get('productivity_score', 0.0)
            results['detection_score'] = detection_score
            results['detection_details'] = detection_results
            
            if detection_score > 0:
                triggers_count = detection_results.get('triggers_activated', 0)
                if triggers_count > 0:
                    results['triggers'].append(f"Visual detection: {triggers_count} triggers")
                    if detection_results.get('gemini_used'):
                        results['triggers'].append("AI (Gemini) detected productivity")
        
        except Exception as e:
            print(f"Warning: Detection module error: {e}")
        
        # 2. Tracking Module (Window Focus) - Weight: 40%
        try:
            should_trigger, reason = self.tracker.should_trigger_protocol(
                require_focus_duration=True
            )
            
            if should_trigger:
                tracking_score = 0.8  # High score if window tracking says productive
                focus_info = self.tracker.track_window_focus()
                focus_duration = focus_info.get('focus_duration', 0)
                app_name = focus_info.get('current_window', {}).get('app_name', 'Unknown')
                
                results['tracking_score'] = tracking_score
                results['triggers'].append(f"Active app focus: {app_name} ({focus_duration:.0f}s)")
            else:
                # Calculate partial score based on focus duration
                focus_info = self.tracker.track_window_focus()
                focus_duration = focus_info.get('focus_duration', 0)
                focus_duration_min = focus_info.get('focus_duration_minutes', 0)
                
                # Scale from 0-0.6 based on focus duration (max at 5 minutes)
                if focus_duration > 0:
                    tracking_score = min(focus_duration_min / 5.0 * 0.6, 0.6)
                    results['tracking_score'] = tracking_score
                    
                    if focus_duration_min > 1:
                        results['triggers'].append(f"Focus duration: {focus_duration_min:.1f} min")
        
        except Exception as e:
            print(f"Warning: Tracking module error: {e}")
        
        # 3. Keyboard Tracking Module - Weight: 20%
        try:
            if self.keyboard_tracker:
                keyboard_stats = self.keyboard_tracker.get_typing_statistics()
                keyboard_score = self.keyboard_tracker.get_activity_score()
                
                results['keyboard_score'] = keyboard_score
                
                if keyboard_score > 0:
                    is_productive, kb_reason = self.keyboard_tracker.detect_productive_typing()
                    if is_productive:
                        results['triggers'].append(f"Keyboard: {kb_reason}")
        
        except Exception as e:
            print(f"Warning: Keyboard tracking error: {e}")
        
        # Combine scores (weighted average)
        # Detection: 40%, Tracking: 40%, Keyboard: 20%
        combined_score = (
            results['detection_score'] * 0.4 +
            results['tracking_score'] * 0.4 +
            results['keyboard_score'] * 0.2
        )
        
        # Cap at 1.0
        results['combined_score'] = min(combined_score, 1.0)
        
        # Build reason string
        if results['triggers']:
            results['reason'] = " | ".join(results['triggers'])
        else:
            results['reason'] = "No productivity indicators detected"
        
        return results
    
    def send_notification(self, title: str, message: str):
        """
        Send a system notification (cross-platform)
        
        Args:
            title: Notification title
            message: Notification message
        """
        try:
            system = platform.system()
            
            if system == 'Darwin':  # macOS
                # Use osascript to show notification
                script = f'display notification "{message}" with title "{title}"'
                subprocess.run(
                    ['osascript', '-e', script],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            elif system == 'Windows':
                # Use PowerShell to show notification
                script = f'''
                [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
                $Template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
                $RawXml = [xml] $Template.GetXml()
                ($RawXml.toast.visual.binding.text|where {{$_.id -eq "1"}}).AppendChild($RawXml.CreateTextNode("{title}")) > $null
                ($RawXml.toast.visual.binding.text|where {{$_.id -eq "2"}}).AppendChild($RawXml.CreateTextNode("{message}")) > $null
                $SerializedXml = New-Object Windows.Data.Xml.Dom.XmlDocument
                $SerializedXml.LoadXml($RawXml.OuterXml)
                $Toast = [Windows.UI.Notifications.ToastNotification]::new($SerializedXml)
                $Toast.Tag = "DeProductify"
                $Toast.Group = "DeProductify"
                $Notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("DeProductify")
                $Notifier.Show($Toast);
                '''
                subprocess.run(
                    ['powershell', '-Command', script],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
            else:  # Linux
                # Use notify-send if available
                try:
                    subprocess.run(
                        ['notify-send', title, message],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                except FileNotFoundError:
                    # Fallback to console if notify-send not available
                    print(f"\nNOTIFICATION: {title}")
                    print(f"   {message}\n")
        except Exception as e:
            # Fallback to console output
            print(f"\nNOTIFICATION: {title}")
            print(f"   {message}\n")
    
    def check_and_send_warnings(self, productivity_score: float):
        """
        Check productivity score and send warning notifications at thresholds
        
        Args:
            productivity_score: Current combined productivity score (0.0-1.0)
        """
        current_time = time.time()
        
        # Don't spam warnings - respect cooldown
        if current_time - self.last_warning_time < self.warning_cooldown:
            return
        
        # Check each threshold in order (low to high)
        for threshold, message in sorted(self.warning_thresholds.items()):
            # Only warn if:
            # 1. Score crossed this threshold
            # 2. Haven't warned at this level yet
            # 3. This is higher than last warning
            if productivity_score >= threshold and threshold > self.last_warning_level:
                # Send notification
                self.send_notification("DeProductify Alert", message)
                
                # Update state
                self.last_warning_level = threshold
                self.last_warning_time = current_time
                
                # Log to console too
                print(f"\n{'='*60}")
                print(f"WARNING: Productivity at {productivity_score:.0%}")
                print(f"   {message}")
                print(f"{'='*60}\n")
                
                # Only send one warning at a time
                break
        
        # Reset warning level if score drops below all thresholds
        if productivity_score < min(self.warning_thresholds.keys()):
            self.last_warning_level = 0
    
    def check_for_game(self) -> Tuple[bool, str]:
        """
        Check if user is currently playing a game using Gemini AI.
        
        Returns:
            Tuple of (is_game: bool, game_name: str)
        """
        current_time = time.time()
        
        # Only check periodically to save API calls
        if current_time - self.last_game_check_time < self.game_check_interval:
            return self.game_detected, ""
        
        self.last_game_check_time = current_time
        
        try:
            # Get current window info
            window_info = self.tracker.get_active_window()
            if not window_info:
                self.game_detected = False
                return False, ""
            
            app_name = window_info.get('app_name', '')
            window_title = window_info.get('window_title', '')
            
            # Use Gemini to detect if it's a game
            if hasattr(self.detector, 'gemini_classifier') and self.detector.gemini_classifier:
                is_game, reasoning = self.detector.gemini_classifier.is_game(app_name, window_title)
                self.game_detected = is_game
                
                if is_game:
                    game_name = app_name or window_title
                    return True, game_name
            
            self.game_detected = False
            return False, ""
            
        except Exception as e:
            print(f"Warning: Game detection error: {e}")
            self.game_detected = False
            return False, ""
    
    def should_trigger_protocol(self) -> Tuple[bool, str, float]:
        """
        Determine if Performative Protocol should be triggered.
        
        Returns:
            Tuple of (should_trigger, reason, productivity_score)
        """
        # Check if user is playing a game - disable all triggers if so
        is_game, game_name = self.check_for_game()
        if is_game:
            return False, f"Game detected: {game_name} - triggers disabled", 0.0
        
        # Check cooldown
        current_time = time.time()
        if self.is_in_cooldown:
            time_remaining = self.cooldown_seconds - (current_time - self.last_trigger_time)
            if time_remaining > 0:
                return False, f"Cooldown active ({time_remaining:.0f}s remaining)", 0.0
            else:
                self.is_in_cooldown = False
        
        # Get combined productivity score
        productivity_data = self.get_combined_productivity_score()
        combined_score = productivity_data['combined_score']
        
        # Check threshold
        if combined_score >= self.productivity_threshold:
            reason = f"Productivity detected: {productivity_data['reason']}"
            return True, reason, combined_score
        
        return False, productivity_data['reason'], combined_score
    
    def start_monitoring(self):
        """Start continuous productivity monitoring loop."""
        self.monitoring = True
        print(f"Monitoring started (threshold: {self.productivity_threshold}, interval: {self.check_interval}s)")
        print("Press Ctrl+C to stop\n")
        
        try:
            while self.monitoring:
                # Check if we should trigger
                should_trigger, reason, score = self.should_trigger_protocol()
                
                # Print status
                print(f"[{time.strftime('%H:%M:%S')}] Productivity Score: {score:.2f} | {reason[:60]}")
                
                # Check for warnings (before triggering)
                if not should_trigger and not self.is_in_cooldown and score > 0:
                    self.check_and_send_warnings(score)
                
                if should_trigger:
                    # Send final warning before triggering
                    self.send_notification(
                        "DeProductify - Protocol Activated!",
                        "You've been too productive! Time for the Performative Protocol..."
                    )
                    
                    # Trigger the Performative Protocol
                    self.last_trigger_time = time.time()
                    self.is_in_cooldown = True
                    
                    # Reset warning level after triggering
                    self.last_warning_level = 0
                    
                    trigger_performative_protocol(reason, score)
                    
                    print(f"Cooldown active for {self.cooldown_seconds} seconds...")
                
                # Wait before next check
                time.sleep(self.check_interval)
        
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped by user")
        finally:
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """Stop monitoring and clean up."""
        self.monitoring = False
        
        if self.keyboard_tracker:
            self.keyboard_tracker.stop_monitoring()
        
        print("DeProductify stopped.")


def main():
    """Main entry point."""
    print("="*60)
    print("DeProductify")
    print("Detects when you're working too hard — and makes it look like you're not.")
    print("="*60 + "\n")
    
    # Create orchestrator with custom settings
    orchestrator = DeProductifyOrchestrator(
        productivity_threshold=0.5,      # Trigger at 50% productivity
        check_interval=3.0,              # Check every 3 seconds
        use_keyboard_tracking=True,      # Enable keyboard tracking
        cooldown_seconds=120.0          # 2 minute cooldown after triggering
    )
    
    # Start monitoring
    orchestrator.start_monitoring()


if __name__ == "__main__":
    main()
