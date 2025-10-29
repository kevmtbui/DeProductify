"""
Test script for Performative Protocol overlay with local audio
Cross-platform support: Windows, macOS, Linux
"""

import tkinter as tk
import platform
from modules.overlay import PerformativeProtocol

def test_overlay():
    # Create root window (hidden)
    root = tk.Tk()
    root.withdraw()
    
    print(f"\n🖥️  Platform: {platform.system()}")
    print("=" * 50)
    
    # Create and activate protocol
    protocol = PerformativeProtocol()
    protocol.activate()
    
    print("\n✅ Overlay launched!")
    print("🍵 Click any matcha image 3 times to dismiss")
    print("🎵 Local audio file should be playing")
    print("\nOverlay features:")
    print("  • 11 aesthetic images (matcha, cat, vinyl, tote, earbuds)")
    print("  • Random rotation (±8°)")
    print("  • Grid layout with proper spacing (no overlap)")
    print("  • Random local MP3 playback (16 indie songs)")
    print("  • Music stops automatically when overlay dismissed")
    print("\nAudio methods:")
    print("  • Primary: pygame.mixer (Windows/cross-platform)")
    print("  • macOS fallback: afplay")
    print("  • Windows fallback: PowerShell MediaPlayer")
    print("  • Linux fallback: mpg123/mpg321")
    
    # Start event loop
    root.mainloop()

if __name__ == "__main__":
    test_overlay()

