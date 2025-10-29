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

def trigger_performative_protocol(reason: str, productivity_score: float):
    """
    Trigger the Performative Protocol overlay.
    
    Displays:
    - Matcha clickable overlay (user must click to dismiss)
    - Random indie music (Laufey, Clairo, Daniel Caesar, beabadoobee)
    - Aesthetic items (vinyls, totebag, labubu, books)
    
    Args:
        reason: Why the protocol was triggered
        productivity_score: Combined productivity score that triggered it
    """
    try:
        from modules.overlay import launch_performative_protocol
        # Launch the Performative Protocol overlay
        launch_performative_protocol(reason, productivity_score)
    except Exception as e:
        # Log error but don't crash the monitoring loop
        print(f"\n❌ Error launching Performative Protocol: {e}")
        print("Monitoring will continue...\n")


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
        
        # Baseline score system - accumulates and never decreases
        self.baseline_score = 0.0  # Current baseline (minimum score)
        self.previous_triggers = set()  # Track which triggers we've seen to avoid duplicate logging
        
        # Warning system - notifications for every 0.1 threshold
        self.last_warning_level = 0
        self.warning_cooldown = 5.0  # Short cooldown between warnings (5s)
        self.last_warning_time = 0
        
        print("\nDeProductify ready! Monitoring your productivity...\n")
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
                    # Log individual detection triggers
                    trigger_id = f"detection_{triggers_count}"
                    if trigger_id not in self.previous_triggers:
                        self.previous_triggers.add(trigger_id)
                        print(f"  [TRIGGER] Detection: {triggers_count} visual triggers activated (Score: {detection_score:.2f})")
                        if detection_results.get('bright_document'):
                            print(f"    → Bright white document detected")
                        if detection_results.get('text_density', 0) >= 300:
                            print(f"    → Text-heavy screen ({detection_results.get('text_density', 0)} words)")
                        if detection_results.get('work_keyword_count', 0) >= 3:
                            print(f"    → Work keywords found ({detection_results.get('work_keyword_count', 0)} keywords)")
                        if detection_results.get('lecture_detected'):
                            print(f"    → Lecture content detected")
                        if detection_results.get('math_detected'):
                            print(f"    → Mathematical notation detected")
                        if detection_results.get('gemini_used'):
                            gemini = detection_results.get('gemini_classification', {})
                            print(f"    → AI (Gemini) detected productivity ({gemini.get('confidence', 'unsure')})")
                    
                    results['triggers'].append(f"Visual detection: {triggers_count} triggers")
                    if detection_results.get('gemini_used'):
                        results['triggers'].append("AI (Gemini) detected productivity")
        
        except Exception as e:
            print(f"Warning: Detection module error: {e}")
        
        # 2. Tracking Module (Window Focus) - Weight: 40%
        try:
            # Get focus info for debugging and scoring
            focus_info = self.tracker.track_window_focus()
            
            should_trigger, reason = self.tracker.should_trigger_protocol(
                require_focus_duration=True
            )
            
            if should_trigger:
                tracking_score = 0.8  # High score if window tracking says productive
                focus_duration = focus_info.get('focus_duration', 0)
                focus_duration_min = focus_info.get('focus_duration_minutes', 0)
                app_name = focus_info.get('current_window', {}).get('app_name', 'Unknown')
                window_title = focus_info.get('current_window', {}).get('window_title', '')
                is_productive = focus_info.get('is_productive_app', False)
                
                # Log tracking trigger with productivity status
                trigger_id = f"tracking_{app_name}_{int(focus_duration)}"
                if trigger_id not in self.previous_triggers:
                    self.previous_triggers.add(trigger_id)
                    print(f"  [TRIGGER] Tracking: Productive app detected")
                    print(f"    → App: '{app_name}'")
                    print(f"    → Window: '{window_title[:50]}...'")
                    print(f"    → Focus duration: {focus_duration:.0f}s ({focus_duration_min:.1f} min)")
                    print(f"    → Score: {tracking_score:.2f}")
                
                results['tracking_score'] = tracking_score
                results['triggers'].append(f"Active app focus: {app_name} ({focus_duration:.0f}s)")
            else:
                # No trigger from tracking - only productive apps trigger, not duration alone
                # Check for tab overload
                window_title = focus_info.get('current_window', {}).get('window_title', '')
                if self.tracker.detect_tab_bar_overload(window_title):
                    tab_info = self.tracker.parse_tab_bar(window_title)
                    if tab_info.get('is_productive_tab'):
                        trigger_id = f"tab_overload_{tab_info.get('tab_count', 0)}"
                        if trigger_id not in self.previous_triggers:
                            self.previous_triggers.add(trigger_id)
                            print(f"  [TRIGGER] Tracking: Tab overload detected ({tab_info.get('tab_count', 0)} tabs on productive site)")
                        
                        results['triggers'].append(f"Tab overload: {tab_info.get('tab_count', 0)} tabs")
                        # Boost tracking score for tab overload
                        if tracking_score < 0.7:
                            tracking_score = 0.7
                            results['tracking_score'] = tracking_score
        
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
                        # Log keyboard trigger
                        trigger_id = f"keyboard_{kb_reason[:30]}"
                        if trigger_id not in self.previous_triggers:
                            self.previous_triggers.add(trigger_id)
                            print(f"  [TRIGGER] Keyboard: {kb_reason} (Score: {keyboard_score:.2f})")
                        
                        results['triggers'].append(f"Keyboard: {kb_reason}")
        
        except Exception as e:
            print(f"Warning: Keyboard tracking error: {e}")
        
        # Combine scores (weighted average)
        # Detection: 40%, Tracking: 40%, Keyboard: 20%
        raw_score = (
            results['detection_score'] * 0.4 +
            results['tracking_score'] * 0.4 +
            results['keyboard_score'] * 0.2
        )
        
        # Apply baseline system: baseline is the highest 0.1 threshold ever reached
        # It acts as a "floor" - you can never score below your highest threshold
        # Update baseline if raw score crosses a new threshold
        current_threshold = int(raw_score * 10) / 10.0  # Round down to nearest 0.1
        if current_threshold > self.baseline_score:
            old_baseline = self.baseline_score
            self.baseline_score = current_threshold
            print(f"  [BASELINE] Score baseline increased: {old_baseline:.1f} → {self.baseline_score:.1f}")
        
        # Combined score is the max of baseline or raw score
        # This ensures once you hit a threshold, you can never drop below it
        combined_score = max(self.baseline_score, raw_score)
        
        # Cap at 1.0
        results['combined_score'] = min(combined_score, 1.0)
        results['baseline_score'] = self.baseline_score
        results['raw_score'] = raw_score
        
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
        Check productivity score and send warning notifications at every 0.1 threshold
        
        Args:
            productivity_score: Current combined productivity score (0.0-1.0)
        """
        current_time = time.time()
        
        # Don't spam warnings - respect cooldown
        if current_time - self.last_warning_time < self.warning_cooldown:
            return
        
        # Calculate current threshold (every 0.1)
        current_threshold = int(productivity_score * 10) / 10.0  # Round down to nearest 0.1
        
        # Send notification if we crossed a new 0.1 threshold
        if current_threshold > self.last_warning_level and current_threshold >= 0.1:
            # Generate message based on threshold
            percentage = int(current_threshold * 100)
            if percentage >= 40:
                message = f"⚠️ Productivity at {percentage}% - Protocol imminent!"
            elif percentage >= 30:
                message = f"⚠️ Productivity rising: {percentage}%"
            elif percentage >= 20:
                message = f"Productivity detected: {percentage}%"
            else:
                message = f"Productivity level: {percentage}%"
            
            # Send notification
            self.send_notification("DeProductify Alert", message)
            
            # Update state
            self.last_warning_level = current_threshold
            self.last_warning_time = current_time
            
            # Log to console too
            print(f"\n{'='*60}")
            print(f"WARNING: Productivity at {percentage}%")
            print(f"   {message}")
            print(f"{'='*60}\n")
    
    def should_trigger_protocol(self, productivity_data: Optional[Dict] = None) -> Tuple[bool, str, float]:
        """
        Determine if Performative Protocol should be triggered.
        
        Args:
            productivity_data: Optional pre-computed productivity data (to avoid double computation)
        
        Returns:
            Tuple of (should_trigger, reason, productivity_score)
        """
        # Check cooldown
        current_time = time.time()
        if self.is_in_cooldown:
            time_remaining = self.cooldown_seconds - (current_time - self.last_trigger_time)
            if time_remaining > 0:
                return False, f"Cooldown active ({time_remaining:.0f}s remaining)", 0.0
            else:
                self.is_in_cooldown = False
        
        # Get combined productivity score (if not provided)
        if productivity_data is None:
            productivity_data = self.get_combined_productivity_score()
        combined_score = productivity_data['combined_score']
        
        # Check threshold
        if combined_score >= self.productivity_threshold:
            reason = f"Productivity detected: {productivity_data['reason']}"
            return True, reason, combined_score
        
        return False, productivity_data['reason'], combined_score
    
    def start_monitoring_with_gui(self, status_queue=None):
        """Start monitoring with GUI support (sends updates to queue)"""
        self.monitoring = True
        print(f"Monitoring started (threshold: {self.productivity_threshold}, interval: {self.check_interval}s)")
        if not status_queue:
            print("Press Ctrl+C to stop\n")
        
        try:
            while self.monitoring:
                # Get productivity data first (needed for display, baseline tracking, and trigger check)
                productivity_data = self.get_combined_productivity_score()
                
                # Check if we should trigger (pass data to avoid recomputing)
                should_trigger, reason, score = self.should_trigger_protocol(productivity_data)
                
                # Print status with baseline info
                baseline = productivity_data.get('baseline_score', 0.0)
                raw = productivity_data.get('raw_score', 0.0)
                if baseline > 0:
                    print(f"[{time.strftime('%H:%M:%S')}] Score: {score:.2f} (Raw: {raw:.2f} + Baseline: {baseline:.1f}) | {reason[:50]}")
                else:
                    print(f"[{time.strftime('%H:%M:%S')}] Productivity Score: {score:.2f} | {reason[:60]}")
                
                # Send status to GUI if queue provided
                if status_queue:
                    try:
                        status_queue.put(("score", (score, baseline, raw)))
                    except:
                        pass
                
                # Check for warnings (before triggering)
                if not should_trigger and not self.is_in_cooldown and score > 0:
                    self.check_and_send_warnings(score)
                
                if should_trigger:
                    # Send final warning before triggering
                    self.send_notification(
                        "DeProductify - Protocol Activated!",
                        "You've been too productive! Time for the Performative Protocol..."
                    )
                    
                    print(f"\n{'='*70}")
                    print(f"🎀 PERFORMATIVE PROTOCOL™ ACTIVATING")
                    print(f"{'='*70}")
                    print(f"Reason: {reason}")
                    baseline = productivity_data.get('baseline_score', 0.0)
                    raw = productivity_data.get('raw_score', 0.0)
                    print(f"Productivity Score: {score:.2f} (Raw: {raw:.2f} + Baseline: {baseline:.1f})")
                    print(f"{'='*70}\n")
                    
                    # Trigger the Performative Protocol (overlay)
                    self.last_trigger_time = time.time()
                    self.is_in_cooldown = True
                    
                    # Reset all tracking state
                    print(f"  [RESET] Resetting all productivity tracking...")
                    print(f"    • Baseline: {self.baseline_score:.1f} → 0.0")
                    print(f"    • Warning level: {self.last_warning_level:.1f} → 0.0")
                    print(f"    • Trigger history cleared")
                    
                    self.baseline_score = 0.0
                    self.last_warning_level = 0
                    self.last_warning_time = 0
                    self.previous_triggers.clear()
                    
                    # Auto-stop monitoring when overlay is triggered
                    print("  [MONITORING] Auto-stopping monitoring...")
                    self.monitoring = False
                    
                    # Update GUI if present
                    if status_queue:
                        try:
                            status_queue.put(("stopped", None))
                        except:
                            pass
                    
                    # Launch overlay (this will show matcha button, play music, etc.)
                    trigger_performative_protocol(reason, score)
                    
                    print(f"\nMonitoring stopped. Restart monitoring from GUI when ready.\n")
                    print(f"All scores reset - fresh start when you resume!\n")
                
                # Wait before next check
                time.sleep(self.check_interval)
        
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped by user")
        finally:
            self.stop_monitoring()
            if status_queue:
                try:
                    status_queue.put(("stopped", None))
                except:
                    pass
    
    def start_monitoring(self):
        """Start continuous productivity monitoring loop (console mode)."""
        self.start_monitoring_with_gui(status_queue=None)
    
    def stop_monitoring(self):
        """Stop monitoring and clean up."""
        self.monitoring = False
        
        if self.keyboard_tracker:
            self.keyboard_tracker.stop_monitoring()
        
        print("DeProductify stopped.")


def main():
    """Main entry point - launches GUI."""
    # Import GUI here to avoid circular imports
    from modules.gui import DeProductifyGUI
    
    print("="*60)
    print("DeProductify")
    print("Detects when you're working too hard — and makes it look like you're not.")
    print("="*60 + "\n")
    
    # Create orchestrator with custom settings
    orchestrator = DeProductifyOrchestrator(
        productivity_threshold=0.4,      # Trigger at 40% productivity (easier for demos)
        check_interval=0.5,              # Check every 0.5 seconds (faster updates)
        use_keyboard_tracking=True,      # Enable keyboard tracking
        cooldown_seconds=120.0          # 2 minute cooldown after triggering
    )
    
    # Launch GUI
    print("Launching GUI...\n")
    gui = DeProductifyGUI(orchestrator=orchestrator)
    gui.run()


if __name__ == "__main__":
    main()
