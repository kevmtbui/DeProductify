"""
Overlay module - Performative Protocol visual and audio elements
"""

import tkinter as tk
from tkinter import Canvas
from PIL import Image, ImageTk
import random
import os
import glob
import time
import subprocess
import sys
import platform
import json
import psutil
from typing import List

class PerformativeProtocol:
    def __init__(self, custom_positions=None, load_from_file=False):
        self.overlay_window = None
        self.canvas = None
        self.images = []
        self.matcha_clicks = 0
        self.custom_positions = custom_positions  # Dict of {filename: {x, y, ...}}
        self.load_from_file = load_from_file
        self.animation_running = False
        self.screen_width = 0
        self.screen_height = 0
        
        # Color palette
        self.bg_color = '#F5F1E8'  # clairo_linen (white background)
        
        # Audio playback
        self.audio_process = None
        self.using_pygame = False
        self.shake_sound = None
        
        # Try to initialize pygame for audio (works better on Windows)
        try:
            import pygame
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.using_pygame = True
            print("Pygame audio initialized")
        except Exception as e:
            print(f"Warning: Pygame audio not available, using system commands: {e}")
            self.using_pygame = False
        
        # Load shake sound effect (works with or without pygame)
        self._load_shake_sound()
        
    def _load_shake_sound(self):
        """Load the shake sound effect"""
        sfx_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'sfx')
        sfx_files = glob.glob(os.path.join(sfx_dir, '*.mp3'))
        
        if not sfx_files:
            print("Warning: No shake sound effect found in assets/sfx/")
            print("   Add a shake sound MP3 to enable sound effects!")
            return
        
        # Check if file is valid (not empty)
        sound_file = sfx_files[0]
        if os.path.getsize(sound_file) == 0:
            print(f"Warning: Shake sound file is empty: {os.path.basename(sound_file)}")
            print("   Please download a valid shake sound effect MP3")
            return
        
        try:
            if self.using_pygame:
                import pygame
                
                # Try to create a faster, louder version using pydub
                processed_file = self._process_shake_sound(sound_file)
                
                if processed_file and os.path.exists(processed_file):
                    # Load the processed version
                    self.shake_sound = pygame.mixer.Sound(processed_file)
                    print(f"Loaded shake sound: {os.path.basename(sound_file)} (2x speed, louder)")
                else:
                    # Load original and increase volume
                    self.shake_sound = pygame.mixer.Sound(sound_file)
                    print(f"Loaded shake sound: {os.path.basename(sound_file)} (louder)")
                
                print(f"   Duration: {self.shake_sound.get_length():.2f}s")
            else:
                # Store path for platform-specific playback
                self.shake_sound = sound_file
                print(f"Shake sound ready: {os.path.basename(sound_file)}")
        except Exception as e:
            print(f"Warning: Could not load shake sound: {e}")
            print(f"   File: {os.path.basename(sound_file)}")
            print(f"   Make sure it's a valid MP3 file")
    
    def _process_shake_sound(self, sound_file):
        """Process shake sound to be 2x faster and louder"""
        try:
            from pydub import AudioSegment
            
            # Create processed file path
            sfx_dir = os.path.dirname(sound_file)
            processed_file = os.path.join(sfx_dir, 'shake_processed.wav')
            
            # Check if already processed
            if os.path.exists(processed_file):
                return processed_file
            
            print("🎵 Processing shake sound (2x speed, +6dB louder)...")
            
            # Load the audio
            audio = AudioSegment.from_mp3(sound_file)
            
            # Speed up 2x (change frame rate)
            audio_fast = audio._spawn(audio.raw_data, overrides={
                "frame_rate": int(audio.frame_rate * 2.0)
            })
            audio_fast = audio_fast.set_frame_rate(44100)
            
            # Increase volume by 6dB
            audio_loud = audio_fast + 6
            
            # Export as WAV for faster loading
            audio_loud.export(processed_file, format='wav')
            print(f"Processed sound saved: {os.path.basename(processed_file)}")
            
            return processed_file
            
        except ImportError:
            print("Warning: pydub not available - using original sound with higher volume")
            return None
        except Exception as e:
            print(f"Warning: Could not process sound: {e}")
            return None
    
    def _play_shake_sound(self):
        """Play the shake sound effect"""
        if not self.shake_sound:
            return
        
        try:
            if self.using_pygame:
                import pygame
                # Set volume to maximum (1.5 = 150% for extra loudness)
                self.shake_sound.set_volume(1.5)
                # Play sound effect (doesn't interfere with music)
                self.shake_sound.play()
            else:
                # Use platform-specific command for quick playback
                system = platform.system()
                
                if system == 'Darwin':  # macOS
                    # Use afplay in background (non-blocking)
                    subprocess.Popen(
                        ['afplay', self.shake_sound],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                elif system == 'Windows':
                    # Use PowerShell SoundPlayer for quick playback
                    subprocess.Popen(
                        ['powershell', '-c', f'(New-Object Media.SoundPlayer "{self.shake_sound}").PlaySync()'],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                    )
                else:  # Linux
                    # Use mpg123 or similar
                    try:
                        subprocess.Popen(
                            ['mpg123', '-q', self.shake_sound],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                    except FileNotFoundError:
                        pass
        except Exception as e:
            print(f"Warning: Could not play shake sound: {e}")
    
    def _load_scaled_positions(self, screen_width, screen_height):
        """Load positions from JSON file and scale to current screen dimensions"""
        positions_file = 'image_positions.json'
        if not os.path.exists(positions_file):
            return None
        
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
                
                print(f"Scaling positions from {saved_width}x{saved_height} to {screen_width}x{screen_height}")
                print(f"   Scale factors: X={scale_x:.2f}, Y={scale_y:.2f}")
                
                # Scale all positions
                scaled_positions = {}
                for filename, pos_data in saved_positions.items():
                    scaled_x = int(pos_data['x'] * scale_x)
                    scaled_y = int(pos_data['y'] * scale_y)
                    scaled_positions[filename] = {
                        'x': scaled_x,
                        'y': scaled_y,
                        'type': pos_data['type'],
                        'angle': pos_data.get('angle', 0)
                    }
                return scaled_positions
            else:
                # Old format without screen dimensions
                return data
        except Exception as e:
            print(f"Warning: Could not load positions: {e}")
            return None
    
    def _load_images(self):
        """Load all overlay images from assets/images/"""
        images_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'images')
        
        # Load specific images
        image_files = [
            'cat1-removebg-preview.png',
            'cat2-removebg-preview.png',
            'cat4-removebg-preview.png',
            'earebuds copy.png',
            'matcha-removebg-preview(1).png',
            'matcha2-removebg-preview.png',
            'tote.png',
            'tote2-removebg-preview.png',
            'vinyl-removebg-preview.png',
            'vinyl2-removebg-preview.png',
            'vinyl3-removebg-preview.png'
        ]
        
        loaded_images = []
        for filename in image_files:
            filepath = os.path.join(images_dir, filename)
            if os.path.exists(filepath):
                try:
                    img = Image.open(filepath)
                    # Ensure RGBA mode for transparency
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    
                    # Determine image type for categorization
                    img_type = 'other'
                    if 'matcha' in filename.lower():
                        img_type = 'matcha'
                    elif 'cat' in filename.lower():
                        img_type = 'cat'
                    elif 'tote' in filename.lower():
                        img_type = 'tote'
                    elif 'vinyl' in filename.lower():
                        img_type = 'vinyl'
                    elif 'earebud' in filename.lower() or 'earbud' in filename.lower():
                        img_type = 'earbuds'
                    
                    loaded_images.append({
                        'image': img,
                        'type': img_type,
                        'filename': filename
                    })
                except Exception as e:
                    print(f"Failed to load {filename}: {e}")
        
        print(f"Loaded {len(loaded_images)} images")
        return loaded_images
    
    def _get_random_audio_file(self):
        """Get a random audio file from assets/audio/"""
        audio_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'audio')
        audio_files = glob.glob(os.path.join(audio_dir, '*.mp3'))
        
        if not audio_files:
            print("❌ No audio files found!")
            return None
        
        selected = random.choice(audio_files)
        print(f"🎵 Selected: {os.path.basename(selected)}")
        return selected
    
    def _play_music(self):
        """Play a random audio file from local assets (cross-platform)"""
        audio_file = self._get_random_audio_file()
        
        if not audio_file:
            return
        
        try:
            # Try pygame first (works well on Windows, sometimes on macOS)
            if self.using_pygame:
                import pygame
                pygame.mixer.music.load(audio_file)
                pygame.mixer.music.play(-1)  # Loop indefinitely
                print(f"🎵 Playing (pygame): {os.path.basename(audio_file)}")
                return
            
            # Fall back to platform-specific commands
            system = platform.system()
            
            if system == 'Darwin':  # macOS
                # Use afplay (macOS built-in audio player)
                self.audio_process = subprocess.Popen(
                    ['afplay', audio_file],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                print(f"🎵 Playing (macOS/afplay): {os.path.basename(audio_file)}")
                
            elif system == 'Windows':
                # Use Windows Media Player via PowerShell
                # This runs asynchronously in the background
                cmd = f'Add-Type -AssemblyName presentationCore; $mediaPlayer = New-Object system.windows.media.mediaplayer; $mediaPlayer.open("{audio_file}"); $mediaPlayer.Play(); while($true){{Start-Sleep 1}}'
                self.audio_process = subprocess.Popen(
                    ['powershell', '-WindowStyle', 'Hidden', '-Command', cmd],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
                print(f"🎵 Playing (Windows/PowerShell): {os.path.basename(audio_file)}")
                
            else:  # Linux or other
                # Try mpg123 or mpg321 (common on Linux)
                try:
                    self.audio_process = subprocess.Popen(
                        ['mpg123', '-q', '--loop', '-1', audio_file],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    print(f"🎵 Playing (Linux/mpg123): {os.path.basename(audio_file)}")
                except FileNotFoundError:
                    # Fallback to mpg321
                    self.audio_process = subprocess.Popen(
                        ['mpg321', '-q', '--loop', '0', audio_file],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    print(f"🎵 Playing (Linux/mpg321): {os.path.basename(audio_file)}")
        except Exception as e:
            print(f"❌ Failed to play music: {e}")
            print(f"   Platform: {platform.system()}")
    
    def _stop_music(self):
        """Stop the currently playing music"""
        try:
            if self.using_pygame:
                import pygame
                pygame.mixer.music.stop()
                print("⏹️ Music stopped (pygame)")
            elif self.audio_process and self.audio_process.poll() is None:
                # Process is still running, terminate it
                self.audio_process.terminate()
                self.audio_process.wait(timeout=2)
                print("⏹️ Music stopped (subprocess)")
                self.audio_process = None
        except Exception as e:
            print(f"❌ Failed to stop music: {e}")
    
    def _check_overlap(self, x, y, placed_positions, margin=350):
        """Check if a position overlaps with any placed images"""
        for px, py in placed_positions:
            distance = ((x - px) ** 2 + (y - py) ** 2) ** 0.5
            if distance < margin:
                return True
        return False
    
    def _get_random_position(self, screen_width, screen_height, placed_positions):
        """
        Get a random non-overlapping position using a strict grid layout.
        Uses 4x3 grid with 200px spacing between grid cells and ±15px jitter.
        """
        # Define grid: 4 columns x 3 rows with 200px spacing
        grid_cols = 4
        grid_rows = 3
        spacing = 200  # spacing between grid cells
        
        # Calculate total grid dimensions
        total_grid_width = (grid_cols - 1) * spacing
        total_grid_height = (grid_rows - 1) * spacing
        
        # Center the grid on screen
        start_x = (screen_width - total_grid_width) // 2
        start_y = (screen_height - total_grid_height) // 2
        
        # Create all possible grid positions
        grid_positions = []
        for row in range(grid_rows):
            for col in range(grid_cols):
                grid_x = start_x + col * spacing
                grid_y = start_y + row * spacing
                grid_positions.append((grid_x, grid_y))
        
        # Shuffle to randomize which grid cell gets used
        random.shuffle(grid_positions)
        
        # Try each grid position with small jitter
        for grid_x, grid_y in grid_positions:
            # Add small random jitter (±15px)
            jitter_x = random.randint(-15, 15)
            jitter_y = random.randint(-15, 15)
            x = grid_x + jitter_x
            y = grid_y + jitter_y
            
            # Check if this position is already used (with large margin)
            if not self._check_overlap(x, y, placed_positions, margin=350):
                return x, y
        
        # Fallback: return a grid position even if overlap
        if grid_positions:
            grid_x, grid_y = grid_positions[0]
            return grid_x + random.randint(-15, 15), grid_y + random.randint(-15, 15)
        
        # Ultimate fallback
        return screen_width // 2, screen_height // 2
    
    def _shake_matcha(self, img_index, canvas_obj):
        """Animate matcha rotating side-to-side 3 times (like shaking a drink)"""
        img_data = self.images[img_index]
        item_id = img_data['item_id']
        original_x = img_data['x']
        original_y = img_data['y']
        original_angle = img_data['angle']
        original_img = img_data['original_img']
        img_type = img_data['type']
        
        # Rotation sequence: tilt left, tilt right - repeated 3 times
        single_shake = [
            original_angle - 20,   # Tilt left
            original_angle + 20,   # Tilt right
            original_angle - 15,   # Tilt left
            original_angle + 15,   # Tilt right
            original_angle - 10,   # Tilt left
            original_angle + 10,   # Tilt right
        ]
        
        # Repeat the shake sequence 3 times, then return to original
        rotation_angles = single_shake * 3 + [original_angle]
        
        # Determine size based on image type
        if img_type in ['matcha', 'cat']:
            new_height = 180
        else:
            new_height = 250
        
        original_size = original_img.size
        aspect_ratio = original_size[0] / original_size[1]
        new_width = int(new_height * aspect_ratio)
        
        def animate_step(step=0):
            if step < len(rotation_angles):
                # Resize and rotate
                resized = original_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                rotated = resized.rotate(rotation_angles[step], resample=Image.Resampling.BICUBIC, expand=True)
                
                # Convert to PhotoImage
                new_photo = ImageTk.PhotoImage(rotated)
                
                # Update the image on canvas
                canvas_obj.itemconfig(item_id, image=new_photo)
                
                # Store reference to prevent garbage collection
                img_data['photo'] = new_photo
                
                # Schedule next step (50ms delay for faster, more energetic shaking)
                canvas_obj.after(50, lambda: animate_step(step + 1))
        
        animate_step()
    
    def _on_matcha_click(self, event, item_id, img_index, canvas_obj):
        """Handle click on matcha image"""
        self.matcha_clicks += 1
        print(f"Matcha click {self.matcha_clicks}/3")
        
        # Play shake sound effect
        self._play_shake_sound()
        
        # Trigger shake animation
        self._shake_matcha(img_index, canvas_obj)
        
        # Dismiss after 3 clicks
        if self.matcha_clicks >= 3:
            print("3 matcha clicks! Dismissing overlay...")
            self.dismiss()
    
    def _close_all_apps(self):
        """Close all applications except DeProductify and essential system apps"""
        print("\nClosing all applications except DeProductify...")
        
        # List of apps/processes to keep running (besides DeProductify)
        keep_running = {
            # System processes (macOS)
            'Finder', 'SystemUIServer', 'Dock', 'WindowServer', 'loginwindow',
            'kernel_task', 'launchd', 'UserEventAgent', 'coreaudiod',
            # System processes (Windows)
            'explorer.exe', 'dwm.exe', 'csrss.exe', 'services.exe', 'winlogon.exe',
            'lsass.exe', 'smss.exe', 'svchost.exe', 'System', 'Registry',
            'conhost.exe', 'RuntimeBroker.exe',
            # System processes (Linux)
            'systemd', 'init', 'gnome-shell', 'plasma-desktop', 'xfce4-panel',
            'kwin_x11', 'Xorg', 'gdm', 'lightdm',
            # Terminals (macOS)
            'Terminal', 'iTerm2', 'iTerm', 'Alacritty', 'Kitty', 'Hyper',
            'Warp', 'Tabby', 'WezTerm',
            # Command Prompts/Shells (Windows)
            'cmd.exe', 'powershell.exe', 'WindowsTerminal.exe', 'pwsh.exe',
            'mintty.exe', 'ConEmu64.exe', 'ConEmu.exe',
            # Terminals (Linux)
            'gnome-terminal', 'konsole', 'xterm', 'terminator', 'tilix',
            'kitty', 'alacritty', 'rxvt', 'urxvt', 'sakura', 'terminology',
            # Shells (all platforms)
            'bash', 'zsh', 'fish', 'sh', 'tcsh', 'ksh',
            # Python/DeProductify processes
            'python', 'python3', 'Python', 'python.exe', 'python3.exe',
        }
        
        closed_count = 0
        system_type = platform.system()
        
        try:
            if system_type == 'Darwin':  # macOS
                # Get list of running applications
                script = 'tell application "System Events" to get name of every process whose background only is false'
                result = subprocess.run(
                    ['osascript', '-e', script],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    apps = result.stdout.strip().split(', ')
                    
                    for app in apps:
                        # Skip if in keep_running list or if it's a system/terminal app
                        if app in keep_running or 'System' in app or 'Python' in app:
                            continue
                        
                        # Extra protection for terminals (case-insensitive check)
                        app_lower = app.lower()
                        if any(term in app_lower for term in ['terminal', 'iterm', 'console', 'shell', 'prompt']):
                            continue
                        
                        try:
                            # Quit the application
                            quit_script = f'tell application "{app}" to quit'
                            subprocess.run(
                                ['osascript', '-e', quit_script],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                                timeout=2
                            )
                            print(f"  Closed: {app}")
                            closed_count += 1
                        except Exception:
                            pass  # Ignore errors for individual apps
            
            elif system_type == 'Windows':
                # Use psutil to get processes on Windows
                for proc in psutil.process_iter(['pid', 'name', 'exe']):
                    try:
                        proc_name = proc.info['name']
                        proc_name_lower = proc_name.lower()
                        
                        # Skip system processes and DeProductify
                        if proc_name in keep_running or proc_name_lower.startswith(('system', 'windows', 'microsoft')):
                            continue
                        
                        # Extra protection for terminals and command prompts
                        if any(term in proc_name_lower for term in ['cmd', 'powershell', 'terminal', 'console', 'conhost', 'pwsh']):
                            continue
                        
                        # Skip if it's a console/background process
                        if proc.info['exe'] and 'Windows' in proc.info['exe']:
                            continue
                        
                        # Check if it has a window (GUI app)
                        try:
                            if proc.num_threads() > 0:
                                proc.terminate()
                                proc.wait(timeout=2)
                                print(f"  Closed: {proc_name}")
                                closed_count += 1
                        except psutil.NoSuchProcess:
                            pass
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            
            else:  # Linux
                # Use psutil for Linux as well
                for proc in psutil.process_iter(['pid', 'name', 'exe']):
                    try:
                        proc_name = proc.info['name']
                        proc_name_lower = proc_name.lower()
                        
                        # Skip system processes and DeProductify
                        if proc_name in keep_running or proc_name.startswith(('gvfs', 'dbus', 'systemd')):
                            continue
                        
                        # Extra protection for terminals
                        if any(term in proc_name_lower for term in ['terminal', 'konsole', 'xterm', 'gnome-terminal', 'shell']):
                            continue
                        
                        # Only close GUI applications (those with DISPLAY)
                        try:
                            if proc.environ().get('DISPLAY'):
                                proc.terminate()
                                proc.wait(timeout=2)
                                print(f"  Closed: {proc_name}")
                                closed_count += 1
                        except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
                            pass
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            
            print(f"Closed {closed_count} applications")
            
        except Exception as e:
            print(f"Warning: Could not close all apps: {e}")
    
    def activate(self):
        """Launch the performative protocol overlay"""
        print("\nActivating Performative Protocol...")
        
        # Close all other applications first
        self._close_all_apps()
        
        # Give a moment for apps to close
        time.sleep(0.5)
        
        # Create fullscreen overlay window
        self.overlay_window = tk.Toplevel()
        self.overlay_window.attributes('-fullscreen', True)
        self.overlay_window.attributes('-topmost', True)
        self.overlay_window.overrideredirect(True)
        
        # Get screen dimensions
        self.screen_width = self.overlay_window.winfo_screenwidth()
        self.screen_height = self.overlay_window.winfo_screenheight()
        
        # Load positions from file if requested
        if self.load_from_file and not self.custom_positions:
            self.custom_positions = self._load_scaled_positions(self.screen_width, self.screen_height)
        
        # Make background fully transparent
        # Use a unique color for transparency (bright green that won't appear in images)
        transparency_color = '#00FF00'
        
        # Platform-specific transparency setup
        try:
            # macOS and some Linux systems support -transparentcolor
            self.overlay_window.attributes('-transparentcolor', transparency_color)
        except tk.TclError:
            try:
                # Windows alternative
                self.overlay_window.wm_attributes('-transparentcolor', transparency_color)
            except tk.TclError:
                # Fallback: use alpha for semi-transparency if true transparency not supported
                self.overlay_window.attributes('-alpha', 0.95)
                transparency_color = self.bg_color
        
        # Create canvas with the transparency color as background
        self.canvas = Canvas(
            self.overlay_window,
            width=self.screen_width,
            height=self.screen_height,
            bg=transparency_color,
            highlightthickness=0
        )
        self.canvas.pack(fill='both', expand=True)
        
        # Block all interactions except matcha clicks
        self.overlay_window.grab_set()
        
        # Load images
        loaded_images = self._load_images()
        
        # Place images on canvas with proper spacing
        placed_positions = []
        max_height = 250  # Max height for images (preserves aspect ratio)
        
        for img_data in loaded_images:
            img = img_data['image']
            img_type = img_data['type']
            filename = img_data['filename']
            original_size = img.size
            
            # Check if we have custom positions for this file
            if self.custom_positions and filename in self.custom_positions:
                pos_data = self.custom_positions[filename]
                if isinstance(pos_data, dict):
                    x, y = pos_data['x'], pos_data['y']
                else:
                    x, y = pos_data
                print(f"Using custom position for {filename}: ({x}, {y})")
            else:
                # Get non-overlapping position
                x, y = self._get_random_position(self.screen_width, self.screen_height, placed_positions)
            
            placed_positions.append((x, y))
            
            # Random velocity for bouncing animation (pixels per frame)
            x_velocity = random.uniform(-2, 2)
            y_velocity = random.uniform(-2, 2)
            
            # Resize image maintaining aspect ratio
            # Scale down matcha and cat images for better quality
            if img_type in ['matcha', 'cat']:
                new_height = 180  # Smaller size for matcha and cats
            else:
                new_height = max_height
            
            aspect_ratio = original_size[0] / original_size[1]
            new_width = int(new_height * aspect_ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Random rotation (±8 degrees)
            angle = random.uniform(-8, 8)
            img = img.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(img)
            
            # Place on canvas
            item_id = self.canvas.create_image(x, y, image=photo, anchor='center')
            
            # Store reference to prevent garbage collection
            self.images.append({
                'photo': photo,
                'original_img': img_data['image'],
                'item_id': item_id,
                'type': img_type,
                'angle': angle,
                'x': x,
                'y': y,
                'x_velocity': x_velocity,
                'y_velocity': y_velocity,
                'size': (new_width, new_height)
            })
            
            # Bind click event for ONLY the first matcha image (matcha-removebg-preview(1).png)
            if img_type == 'matcha' and 'matcha-removebg-preview(1)' in filename:
                self.canvas.tag_bind(
                    item_id,
                    '<Button-1>',
                    lambda e, iid=item_id, idx=len(self.images)-1: self._on_matcha_click(e, iid, idx, self.canvas)
                )
        
        # Play music
        self._play_music()
        
        # Start animation loop
        self.animation_running = True
        self._animate_images()
        
        print(f"Overlay active with {len(loaded_images)} images")
        print("Click the FIRST matcha (matcha-removebg-preview) 3 times to dismiss!")
        print("   Note: matcha2 is just decoration, won't respond to clicks")
        print("Images are floating and bouncing!")
    
    def _animate_images(self):
        """Animate images to move around and bounce off walls"""
        if not self.animation_running or not self.canvas:
            return
        
        for img_data in self.images:
            # Get current position and velocity
            x = img_data['x']
            y = img_data['y']
            x_velocity = img_data['x_velocity']
            y_velocity = img_data['y_velocity']
            item_id = img_data['item_id']
            width, height = img_data['size']
            
            # Update position
            new_x = x + x_velocity
            new_y = y + y_velocity
            
            # Bounce off walls (with some padding for image size)
            padding = max(width, height) // 2
            
            # Left/right walls
            if new_x - padding <= 0 or new_x + padding >= self.screen_width:
                x_velocity = -x_velocity
                # Keep within bounds
                new_x = max(padding, min(self.screen_width - padding, new_x))
            
            # Top/bottom walls
            if new_y - padding <= 0 or new_y + padding >= self.screen_height:
                y_velocity = -y_velocity
                # Keep within bounds
                new_y = max(padding, min(self.screen_height - padding, new_y))
            
            # Update stored position and velocity
            img_data['x'] = new_x
            img_data['y'] = new_y
            img_data['x_velocity'] = x_velocity
            img_data['y_velocity'] = y_velocity
            
            # Move the image on canvas
            self.canvas.coords(item_id, new_x, new_y)
        
        # Schedule next frame (approximately 60 FPS)
        if self.canvas:
            self.canvas.after(16, self._animate_images)
    
    def dismiss(self):
        """Dismiss the overlay and stop music"""
        print("\nDismissing Performative Protocol...")
        
        # Stop animation
        self.animation_running = False
        
        # Stop music
        self._stop_music()
        
        # Close overlay window
        if self.overlay_window:
            self.overlay_window.grab_release()
            
            # Get the root window before destroying overlay
            root = self.overlay_window.master
            
            self.overlay_window.destroy()
            self.overlay_window = None
        
        # Close the root window and quit the application
        if root:
            root.quit()
            root.destroy()
        
        # Clear images
        self.images = []
        self.matcha_clicks = 0
        
        print("Overlay dismissed! App closing...")


# Helper functions for integration with other modules

def launch_performative_protocol(reason: str, productivity_score: float) -> bool:
    """
    Launch the Performative Protocol overlay.
    
    This function provides a simple interface for other modules to trigger the protocol.
    
    Args:
        reason: Why the protocol was triggered
        productivity_score: Combined productivity score (0.0-1.0)
    
    Returns:
        True if protocol completed successfully, False otherwise
    """
    import tkinter as tk
    
    try:
        # Create root window
        root = tk.Tk()
        root.withdraw()
        
        print(f"\nLaunching Performative Protocol...")
        print(f"  Reason: {reason}")
        print(f"  Score: {productivity_score:.2f}")
        
        # Create and activate protocol
        protocol = PerformativeProtocol()
        protocol.activate()
        
        # Start event loop
        root.mainloop()
        
        return True
    except Exception as e:
        print(f"❌ Failed to launch protocol: {e}")
        return False


def stop_protocol():
    """Stop any running protocol overlay."""
    # The protocol auto-stops when dismissed via matcha clicks
    # This is kept for compatibility with other modules
    pass
