"""
Test script for Window Tracking module
Run this to test window detection and tracking features
"""

import time
from modules.tracking import create_tracker


def test_window_detection():
    """Test basic window detection"""
    print("=" * 60)
    print("Test 1: Window Detection")
    print("=" * 60)
    
    tracker = create_tracker()
    
    window = tracker.get_active_window()
    if window:
        print(f"✓ Active Window Detected:")
        print(f"  App Name: {window.get('app_name')}")
        print(f"  Window Title: {window.get('window_title')}")
        print(f"  Timestamp: {window.get('timestamp')}")
    else:
        print("✗ No active window detected")
    
    return window


def test_app_interface_detection():
    """Test app interface detection"""
    print("\n" + "=" * 60)
    print("Test 2: App Interface Detection")
    print("=" * 60)
    
    tracker = create_tracker()
    window = tracker.get_active_window()
    
    if window:
        is_productive, app_name = tracker.detect_app_interface(window)
        print(f"Current App: {app_name}")
        print(f"Is Productive: {is_productive}")
        
        if is_productive:
            print("✓ Productive app detected!")
        else:
            print("✗ Not identified as productive app")
            print("  (This is normal if you're not in a productive app)")
    else:
        print("✗ No window to test")


def test_tab_parsing():
    """Test browser tab parsing"""
    print("\n" + "=" * 60)
    print("Test 3: Browser Tab Parsing")
    print("=" * 60)
    
    tracker = create_tracker()
    window = tracker.get_active_window()
    
    if window:
        window_title = window.get('window_title', '')
        tab_info = tracker.parse_tab_bar(window_title)
        
        print(f"Window Title: {window_title}")
        print(f"  Is Browser: {tab_info['is_browser']}")
        
        if tab_info['is_browser']:
            print(f"  Current Tab: {tab_info['current_tab']}")
            print(f"  Tab Count: {tab_info['tab_count']}")
            print(f"  Is Productive Tab: {tab_info['is_productive_tab']}")
            
            # Test overload
            is_overload = tracker.detect_tab_bar_overload(window_title, threshold=5)
            print(f"  Tab Overload (≥5 tabs): {is_overload}")
        else:
            print("  (Not a browser window)")
    else:
        print("✗ No window to test")


def test_focus_tracking():
    """Test focus duration tracking"""
    print("\n" + "=" * 60)
    print("Test 4: Focus Duration Tracking")
    print("=" * 60)
    
    tracker = create_tracker()
    
    print("Tracking window focus...")
    print("(This will show how long the current window has been focused)")
    
    # Initial check
    focus_info = tracker.track_window_focus()
    
    if focus_info['current_window']:
        print(f"\nCurrent Window: {focus_info['current_window'].get('app_name')}")
        print(f"Is Productive: {focus_info['is_productive_app']}")
        print(f"Focus Duration: {focus_info['focus_duration']:.2f} seconds")
        print(f"App Total Time: {focus_info['app_total_time']:.2f} seconds")
        print(f"Window Changed: {focus_info['window_changed']}")
        
        # Wait a moment and check again
        print("\nWaiting 2 seconds and checking again...")
        time.sleep(2)
        
        focus_info2 = tracker.track_window_focus()
        print(f"Focus Duration (after 2s): {focus_info2['focus_duration']:.2f} seconds")
        print(f"Window Changed: {focus_info2['window_changed']}")
    else:
        print("✗ No active window")


def test_protocol_trigger():
    """Test protocol trigger decision"""
    print("\n" + "=" * 60)
    print("Test 5: Protocol Trigger Decision")
    print("=" * 60)
    
    tracker = create_tracker(focus_duration_threshold=10.0)  # 10 seconds for testing
    
    # Test without requiring focus duration
    should_trigger, reason = tracker.should_trigger_protocol(require_focus_duration=False)
    print(f"Trigger (no duration req): {should_trigger}")
    print(f"Reason: {reason}")
    
    # Test with focus duration requirement
    should_trigger2, reason2 = tracker.should_trigger_protocol(require_focus_duration=True)
    print(f"\nTrigger (with duration req): {should_trigger2}")
    print(f"Reason: {reason2}")
    
    # Get focus info for details
    focus_info = tracker.track_window_focus()
    if focus_info['current_window']:
        print(f"\nCurrent focus duration: {focus_info['focus_duration']:.2f}s")
        print(f"Threshold: {tracker.focus_duration_threshold}s")


def test_custom_window():
    """Test with a custom window (simulated)"""
    print("\n" + "=" * 60)
    print("Test 6: Custom Window Simulation")
    print("=" * 60)
    
    tracker = create_tracker()
    
    # Simulate different window scenarios
    test_windows = [
        {'app_name': 'Visual Studio Code', 'window_title': 'main.py - DeProductify - Visual Studio Code'},
        {'app_name': 'Google Chrome', 'window_title': 'GitHub - How to use Git - Google Chrome'},
        {'app_name': 'Spotify', 'window_title': 'Spotify - Laufey Radio'},
        {'app_name': 'Quercus', 'window_title': 'Quercus - Student Portal - Assignments'},
    ]
    
    for test_window in test_windows:
        print(f"\nTesting: {test_window['window_title']}")
        
        # App interface detection
        is_productive, app_name = tracker.detect_app_interface(test_window)
        print(f"  App Detection: {is_productive} ({app_name})")
        
        # Tab parsing
        tab_info = tracker.parse_tab_bar(test_window['window_title'])
        if tab_info['is_browser']:
            print(f"  Tab Info: {tab_info['current_tab']} (productive: {tab_info['is_productive_tab']})")
        
        # Protocol trigger
        should_trigger, reason = tracker.should_trigger_protocol(require_focus_duration=False)
        print(f"  Should Trigger: {should_trigger} - {reason}")


def main():
    """Run all tests"""
    print("\n" + "🪟 Window Tracking Test Suite" + "\n")
    
    try:
        # Test 1: Basic detection
        test_window_detection()
        
        # Test 2: App interface detection
        test_app_interface_detection()
        
        # Test 3: Tab parsing
        test_tab_parsing()
        
        # Test 4: Focus tracking
        test_focus_tracking()
        
        # Test 5: Protocol trigger
        test_protocol_trigger()
        
        # Test 6: Custom scenarios
        test_custom_window()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
        print("\n💡 Tips:")
        print("  - Switch to different apps to see detection in action")
        print("  - Open a browser with multiple tabs to test tab parsing")
        print("  - Keep a productive app open for 10+ seconds to test focus duration")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

