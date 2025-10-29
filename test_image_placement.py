"""
Interactive Image Placement Tool

Click anywhere on the screen to place the next image.
Images will be placed in order with proper aspect ratios.
Positions are saved to 'image_positions.json' when you close the window.

Controls:
- Click: Place next image
- 'r': Reset all placements
- 's': Save positions to JSON
- 'q' or Escape: Quit and save
"""

import tkinter as tk
from tkinter import Canvas
from PIL import Image, ImageTk
import os
import json
import random

class ImagePlacementTool:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Image Placement Tool - Click to Place Images")
        
        # Make fullscreen
        self.root.attributes('-fullscreen', True)
        
        # Get screen dimensions
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        
        # Create canvas
        self.canvas = Canvas(
            self.root,
            width=self.screen_width,
            height=self.screen_height,
            bg='#F5F1E8',  # clairo_linen
            highlightthickness=0
        )
        self.canvas.pack(fill='both', expand=True)
        
        # State
        self.loaded_images = []
        self.placed_images = []
        self.current_index = 0
        self.positions = {}
        self.max_height = 250
        
        # Instructions
        self._show_instructions()
        
        # Load images
        self._load_images()
        
        # Bind events
        self.canvas.bind('<Button-1>', self._on_click)
        self.root.bind('r', self._reset)
        self.root.bind('s', self._save_positions)
        self.root.bind('q', self._quit)
        self.root.bind('<Escape>', self._quit)
        
        print(f"\n🎨 Image Placement Tool")
        print(f"📂 Loaded {len(self.loaded_images)} images")
        print(f"🖥️  Screen: {self.screen_width}x{self.screen_height}")
        print(f"\n✨ Click anywhere to place the next image!")
        print(f"   Current: {self.current_index + 1}/{len(self.loaded_images)}")
    
    def _show_instructions(self):
        """Display instructions on screen"""
        instructions = [
            "🎨 Image Placement Tool",
            f"📐 Screen: {self.screen_width} x {self.screen_height}",
            "",
            "Click anywhere to place the next image",
            "",
            "Keyboard shortcuts:",
            "  R - Reset all placements",
            "  S - Save positions to JSON",
            "  Q or ESC - Quit and save",
        ]
        
        y_offset = 50
        for line in instructions:
            self.canvas.create_text(
                self.screen_width // 2,
                y_offset,
                text=line,
                font=('Arial', 16 if line.startswith('🎨') else 14),
                fill='#4A3F35'
            )
            y_offset += 30
    
    def _load_images(self):
        """Load all overlay images"""
        images_dir = os.path.join(os.path.dirname(__file__), 'assets', 'images')
        
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
        
        for filename in image_files:
            filepath = os.path.join(images_dir, filename)
            if os.path.exists(filepath):
                try:
                    img = Image.open(filepath)
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    
                    # Determine image type
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
                    
                    self.loaded_images.append({
                        'image': img,
                        'type': img_type,
                        'filename': filename
                    })
                except Exception as e:
                    print(f"❌ Failed to load {filename}: {e}")
    
    def _on_click(self, event):
        """Handle click to place image"""
        if self.current_index >= len(self.loaded_images):
            print("✅ All images placed!")
            return
        
        x, y = event.x, event.y
        
        # Get current image
        img_data = self.loaded_images[self.current_index]
        img = img_data['image']
        img_type = img_data['type']
        filename = img_data['filename']
        original_size = img.size
        
        # Resize maintaining aspect ratio
        # Scale down matcha and cat images for better quality
        if img_type in ['matcha', 'cat']:
            new_height = 180  # Smaller size for matcha and cats
        else:
            new_height = self.max_height
        
        aspect_ratio = original_size[0] / original_size[1]
        new_width = int(new_height * aspect_ratio)
        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Random rotation
        angle = random.uniform(-8, 8)
        rotated_img = resized_img.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
        
        # Convert to PhotoImage
        photo = ImageTk.PhotoImage(rotated_img)
        
        # Place on canvas
        item_id = self.canvas.create_image(x, y, image=photo, anchor='center')
        
        # Store
        self.placed_images.append({
            'photo': photo,
            'item_id': item_id,
            'x': x,
            'y': y,
            'type': img_type,
            'filename': filename,
            'angle': angle,
            'size': (new_width, new_height)
        })
        
        # Save position
        self.positions[filename] = {
            'x': x,
            'y': y,
            'angle': angle,
            'type': img_type
        }
        
        print(f"✅ Placed {filename} at ({x}, {y})")
        
        # Move to next image
        self.current_index += 1
        
        if self.current_index < len(self.loaded_images):
            print(f"   Next: {self.current_index + 1}/{len(self.loaded_images)} - {self.loaded_images[self.current_index]['filename']}")
        else:
            print(f"\n🎉 All images placed! Press 'S' to save or 'Q' to quit and save.")
    
    def _reset(self, event=None):
        """Reset all placements"""
        # Remove all placed images
        for img_data in self.placed_images:
            self.canvas.delete(img_data['item_id'])
        
        self.placed_images = []
        self.positions = {}
        self.current_index = 0
        
        print("\n🔄 Reset! Click to place images again.")
        print(f"   Current: {self.current_index + 1}/{len(self.loaded_images)}")
    
    def _save_positions(self, event=None):
        """Save positions to JSON file with screen dimensions"""
        output_file = 'image_positions.json'
        
        # Create data structure with screen dimensions and positions
        data = {
            'screen_dimensions': {
                'width': self.screen_width,
                'height': self.screen_height
            },
            'positions': self.positions
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n💾 Saved {len(self.positions)} positions to {output_file}")
        print(f"📐 Screen dimensions: {self.screen_width}x{self.screen_height}")
        print(f"   Positions will scale to any screen size!")
        
        # Also print Python code to use these positions
        print("\n📋 Copy this code to use these positions:")
        print("```python")
        print("CUSTOM_POSITIONS = {")
        for filename, pos in self.positions.items():
            print(f"    '{filename}': ({pos['x']}, {pos['y']}),")
        print("}")
        print("```")
    
    def _quit(self, event=None):
        """Quit and save"""
        if self.positions:
            self._save_positions()
        print("\n👋 Goodbye!")
        self.root.destroy()
    
    def run(self):
        """Run the tool"""
        self.root.mainloop()

if __name__ == "__main__":
    tool = ImagePlacementTool()
    tool.run()

