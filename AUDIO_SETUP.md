# Audio Playback - Cross-Platform Guide

## Overview

The Performative Protocol now uses **local MP3 files** instead of YouTube links, with full cross-platform support for Windows, macOS, and Linux.

---

## How It Works

### Audio Files
- **Location**: `assets/audio/`
- **Count**: 16 indie songs (Laufey, Clairo, beabadoobee)
- **Format**: MP3
- **Selection**: Random song picked each time overlay activates
- **Playback**: Loops continuously until overlay dismissed

### Dismissal
- Click any **matcha image 3 times**
- Music **automatically stops** when overlay closes
- No manual cleanup required

---

## Platform-Specific Implementation

The app uses a **smart fallback system**:

### 1. Primary Method: pygame.mixer
- **Platforms**: Windows, Linux, sometimes macOS
- **Advantages**: Cross-platform, reliable, built-in looping
- **Initialization**: Automatically attempted on startup

### 2. Fallback Methods (if pygame fails)

#### macOS
- **Command**: `afplay`
- **Built-in**: Native macOS audio player
- **No installation required**

#### Windows  
- **Command**: PowerShell MediaPlayer
- **Built-in**: Uses Windows Media Foundation
- **No installation required**

#### Linux
- **Command**: `mpg123` or `mpg321`
- **Installation**: May need to install via package manager
  ```bash
  # Ubuntu/Debian
  sudo apt install mpg123
  
  # Fedora
  sudo dnf install mpg123
  
  # Arch
  sudo pacman -S mpg123
  ```

---

## Testing

### Quick Test
```bash
python test_overlay.py
```

This will:
1. Show your platform
2. Initialize audio system
3. Launch overlay with 11 aesthetic images
4. Play a random indie song
5. Wait for 3 matcha clicks to dismiss

### What You Should See
- Console output showing selected audio file
- Audio method used (pygame/afplay/PowerShell/mpg123)
- Fullscreen overlay with floating images
- Music playing in background

---

## Troubleshooting

### macOS: "CoreAudio error"
- This may happen with pygame on some macOS versions
- **Solution**: App automatically falls back to `afplay` (built-in)
- No action needed - it's handled automatically

### Windows: No sound
- Ensure PowerShell execution policy allows scripts
- **Alternative**: pygame should work as primary method
- Check system volume and audio output device

### Linux: "mpg123: command not found"
- Install mpg123 or mpg321 via package manager
- **Alternative**: pygame should work as primary method

---

## Technical Details

### Audio Process Management
- **pygame method**: Uses `pygame.mixer.music.play(-1)` for infinite loop
- **subprocess method**: Launches platform-specific player in background
- **Cleanup**: Properly terminates process or stops mixer on dismissal

### File Selection
- Random selection from all `.mp3` files in `assets/audio/`
- Uses `glob.glob()` for dynamic file discovery
- No hardcoded playlist - just add MP3s to the folder

### Looping Behavior
- **pygame**: Built-in infinite loop (`play(-1)`)
- **afplay**: Single playthrough (would need restart for loop)
- **PowerShell**: Embedded loop in command
- **mpg123/321**: `--loop -1` flag

---

## Adding More Songs

1. Download MP3 files
2. Place in `assets/audio/`
3. That's it! App automatically discovers all `.mp3` files

---

## Performance

- **Startup**: ~0.5-1s for pygame init
- **Playback**: Instant start with pygame, slight delay with subprocess methods
- **Memory**: Minimal - only one audio file loaded at a time
- **CPU**: Negligible - audio handled by system

---

## Future Enhancements

- [ ] Volume control from GUI
- [ ] Playlist customization
- [ ] Skip song button
- [ ] Audio visualizer overlay
- [ ] Fade in/out effects

