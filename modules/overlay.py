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
from typing import List

class PerformativeProtocol:
    def __init__(self):
        self.overlay_window = None
        self.canvas = None
        self.images = []
        self.matcha_clicks = 0
        
        # Color palette
        self.bg_color = '#F5F1E8'  # clairo_linen (white background)
        
        # Audio playback
        self.audio_process = None
        self.using_pygame = False
        
        # Try to initialize pygame for audio (works better on Windows)
        try:
            import pygame
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.using_pygame = True
            print("✅ Pygame audio initialized")
        except Exception as e:
            print(f"⚠️  Pygame audio not available, using system commands: {e}")
            self.using_pygame = False
        
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
        
        print(f"✅ Loaded {len(loaded_images)} images")
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
    
    def _wobble_rotate(self, item_id, original_angle, canvas_obj):
        """Animate a quick shake/wobble on click"""
        angles = [original_angle - 15, original_angle + 15, original_angle - 10, original_angle + 10, original_angle]
        
        def animate_step(step=0):
            if step < len(angles):
                # This is a simplified animation - in practice, you'd need to re-create the image
                # For now, just schedule the next step
                canvas_obj.after(50, lambda: animate_step(step + 1))
        
        animate_step()
    
    def _on_matcha_click(self, event, item_id, img_data, canvas_obj):
        """Handle click on matcha image"""
        self.matcha_clicks += 1
        print(f"🍵 Matcha click {self.matcha_clicks}/3")
        
        # Trigger wobble animation
        self._wobble_rotate(item_id, img_data.get('angle', 0), canvas_obj)
        
        # Dismiss after 3 clicks
        if self.matcha_clicks >= 3:
            print("✅ 3 matcha clicks! Dismissing overlay...")
            self.dismiss()
    
    def activate(self):
        """Launch the performative protocol overlay"""
        print("\n🎭 Activating Performative Protocol...")
        
        # Create fullscreen overlay window
        self.overlay_window = tk.Toplevel()
        self.overlay_window.attributes('-fullscreen', True)
        self.overlay_window.attributes('-topmost', True)
        self.overlay_window.overrideredirect(True)
        
        # Set transparency (0.85 = 85% opaque)
        self.overlay_window.attributes('-alpha', 0.85)
        
        # Get screen dimensions
        screen_width = self.overlay_window.winfo_screenwidth()
        screen_height = self.overlay_window.winfo_screenheight()
        
        # Create canvas with white background
        self.canvas = Canvas(
            self.overlay_window,
            width=screen_width,
            height=screen_height,
            bg=self.bg_color,
            highlightthickness=0
        )
        self.canvas.pack(fill='both', expand=True)
        
        # Block all interactions except matcha clicks
        self.overlay_window.grab_set()
        
        # Load images
        loaded_images = self._load_images()
        
        # Place images on canvas with proper spacing
        placed_positions = []
        base_size = 200  # Standard size for all images
        
        for img_data in loaded_images:
            img = img_data['image']
            img_type = img_data['type']
            
            # Get non-overlapping position
            x, y = self._get_random_position(screen_width, screen_height, placed_positions)
            placed_positions.append((x, y))
            
            # Resize image
            img = img.resize((base_size, base_size), Image.Resampling.LANCZOS)
            
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
                'item_id': item_id,
                'type': img_type,
                'angle': angle
            })
            
            # Bind click event for matcha images
            if img_type == 'matcha':
                self.canvas.tag_bind(
                    item_id,
                    '<Button-1>',
                    lambda e, iid=item_id, idata=self.images[-1]: self._on_matcha_click(e, iid, idata, self.canvas)
                )
        
        # Play music
        self._play_music()
        
        print(f"✅ Overlay active with {len(loaded_images)} images")
        print("🍵 Click matcha 3 times to dismiss!")
    
    def dismiss(self):
        """Dismiss the overlay and stop music"""
        print("\n👋 Dismissing Performative Protocol...")
        
        # Stop music
        self._stop_music()
        
        # Close overlay window
        if self.overlay_window:
            self.overlay_window.grab_release()
            self.overlay_window.destroy()
            self.overlay_window = None
        
        # Clear images
        self.images = []
        self.matcha_clicks = 0
        
        print("✅ Overlay dismissed!")
