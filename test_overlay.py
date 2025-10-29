"""
Test script for Performative Protocol overlay with local audio
Cross-platform support: Windows, macOS, Linux
"""

import tkinter as tk
import platform
import json
import os
from modules.overlay import PerformativeProtocol

def test_overlay():
    # Create root window (hidden)
    root = tk.Tk()
    root.withdraw()
    
    # Get screen dimensions
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    
    print(f"\n🖥️  Platform: {platform.system()}")
    print(f"📐 Screen: {screen_width} x {screen_height}")
    print("=" * 50)
    
    # Try to load custom positions with scaling
    custom_positions = None
    positions_file = 'image_positions.json'
    if os.path.exists(positions_file):
        try:
            with open(positions_file, 'r') as f:
                data = json.load(f)
            
            # Check if we have the new format with screen dimensions
            if isinstance(data, dict) and 'screen_dimensions' in data and 'positions' in data:
                saved_width = data['screen_dimensions']['width']
                saved_height = data['screen_dimensions']['height']
                saved_positions = data['positions']
                
                # Calculate scaling factors
                scale_x = screen_width / saved_width
                scale_y = screen_height / saved_height
                
                print(f"📍 Loaded positions from {positions_file}")
                print(f"   Original screen: {saved_width}x{saved_height}")
                print(f"   Current screen: {screen_width}x{screen_height}")
                print(f"   Scale factors: X={scale_x:.2f}, Y={scale_y:.2f}")
                
                # Scale all positions
                custom_positions = {}
                for filename, pos_data in saved_positions.items():
                    scaled_x = int(pos_data['x'] * scale_x)
                    scaled_y = int(pos_data['y'] * scale_y)
                    custom_positions[filename] = {
                        'x': scaled_x,
                        'y': scaled_y,
                        'type': pos_data['type'],
                        'angle': pos_data.get('angle', 0)
                    }
                print(f"✅ Scaled {len(custom_positions)} positions to current screen")
            else:
                # Old format without screen dimensions
                custom_positions = data
                print(f"📍 Loaded {len(custom_positions)} positions (no scaling - old format)")
        except Exception as e:
            print(f"⚠️  Could not load positions: {e}")
    
    # Create and activate protocol
    protocol = PerformativeProtocol(custom_positions=custom_positions)
    protocol.activate()
    
    print("\n✅ Overlay launched!")
    print("🍵 Click the FIRST matcha image 3 times to dismiss")
    print("   (matcha-removebg-preview(1).png is the clickable one)")
    print("🎵 Local audio file should be playing")
    print("🎈 Images are floating and bouncing!")
    print("\nOverlay features:")
    print("  • 11 aesthetic images (matcha, cat, vinyl, tote, earbuds)")
    print("  • Bouncing animation - images float around and bounce off walls")
    print("  • First matcha shake animation when clicked (3x rotation)")
    print("  • Second matcha (matcha2) is decoration only")
    print("  • 🔊 Shake sound effect plays on each matcha click")
    print("  • Random rotation (±8°)")
    print("  • Random local MP3 playback (16 indie songs)")
    print("  • Music stops automatically when overlay dismissed")
    print("  • App closes completely after 3 matcha clicks")
    print("\nAudio methods:")
    print("  • Primary: pygame.mixer (Windows/cross-platform)")
    print("  • macOS fallback: afplay")
    print("  • Windows fallback: PowerShell MediaPlayer")
    print("  • Linux fallback: mpg123/mpg321")
    
    # Start event loop
    root.mainloop()

if __name__ == "__main__":
    test_overlay()

