# Image Placement Guide

## 🎯 Overview

The image placement system now **automatically scales to any screen size**! Place images once on any screen, and they'll scale proportionally to any resolution.

---

## 🎮 How to Use

### Step 1: Place Images Interactively

Run the placement tool:
```bash
python test_image_placement.py
```

**What happens:**
- Shows your screen dimensions at the top
- Click anywhere to place each image (11 total)
- Images appear with proper aspect ratios and sizes:
  - **Matcha & Cats**: 180px height (smaller, better quality)
  - **Vinyl, Tote, Earbuds**: 250px height
- Press **S** to save or **Q** to quit and save

**Output:** Creates `image_positions.json` with:
```json
{
  "screen_dimensions": {
    "width": 1920,
    "height": 1080
  },
  "positions": {
    "cat1-removebg-preview.png": {
      "x": 450,
      "y": 320,
      "type": "cat",
      "angle": -5.2
    },
    ...
  }
}
```

### Step 2: Test Your Placements

Run the test overlay:
```bash
python test_overlay.py
```

**What happens:**
- Automatically loads `image_positions.json`
- Detects your current screen dimensions
- **Scales positions proportionally** if screen size differs
- Shows scaling info in console:
  ```
  📍 Loaded positions from image_positions.json
     Original screen: 1920x1080
     Current screen: 2560x1440
     Scale factors: X=1.33, Y=1.33
  ✅ Scaled 11 positions to current screen
  ```

---

## 📐 How Scaling Works

### Example: 1920x1080 → 2560x1440

Original position: `(450, 320)`

Scaling factors:
- `scale_x = 2560 / 1920 = 1.33`
- `scale_y = 1440 / 1080 = 1.33`

New position:
- `x = 450 × 1.33 = 600`
- `y = 320 × 1.33 = 427`

### Example: 1920x1080 → 1366x768 (smaller screen)

Original position: `(450, 320)`

Scaling factors:
- `scale_x = 1366 / 1920 = 0.71`
- `scale_y = 768 / 1080 = 0.71`

New position:
- `x = 450 × 0.71 = 320`
- `y = 320 × 0.71 = 227`

---

## ✨ Features

### Aspect Ratio Preservation
- **Matcha** images: Scaled to 180px height
- **Cat** images: Scaled to 180px height
- **Vinyl, Tote, Earbuds**: Scaled to 250px height
- All maintain original width/height ratios

### Rotation Animation
- **Matcha only**: Rotates side-to-side when clicked (like shaking a drink)
- Sequence: -20°, +20°, -15°, +15°, -10°, +10°, back to original
- Smooth 60ms animation steps

### Cross-Platform
Works on any screen size:
- 🖥️  Desktop: 1920x1080, 2560x1440, 3840x2160 (4K)
- 💻 Laptop: 1366x768, 1440x900, 1920x1200
- 📱 Projector: Any resolution

---

## 🎨 Keyboard Shortcuts (Placement Tool)

| Key | Action |
|-----|--------|
| **Click** | Place next image |
| **R** | Reset all placements |
| **S** | Save positions to JSON |
| **Q** or **ESC** | Quit and save |

---

## 🔧 Integration with Main App

To use custom positions in your main app:

```python
from modules.overlay import PerformativeProtocol

# Option 1: Load from file automatically
protocol = PerformativeProtocol(load_from_file=True)
protocol.activate()

# Option 2: Load manually with scaling
import json

with open('image_positions.json', 'r') as f:
    data = json.load(f)

# Get current screen dimensions
screen_width = 1920  # Your current screen width
screen_height = 1080  # Your current screen height

# Scale positions
saved_width = data['screen_dimensions']['width']
saved_height = data['screen_dimensions']['height']
scale_x = screen_width / saved_width
scale_y = screen_height / saved_height

custom_positions = {}
for filename, pos in data['positions'].items():
    custom_positions[filename] = {
        'x': int(pos['x'] * scale_x),
        'y': int(pos['y'] * scale_y),
        'type': pos['type'],
        'angle': pos.get('angle', 0)
    }

protocol = PerformativeProtocol(custom_positions=custom_positions)
protocol.activate()
```

---

## 🐛 Troubleshooting

### Images appear in wrong positions
- Check that screen dimensions match in console output
- Verify scaling factors are being applied (should show in console)
- Re-run placement tool on your current screen

### Positions file not loading
- Make sure `image_positions.json` exists in project root
- Check JSON format is valid
- Look for error messages in console

### Images still overlapping
- Use the placement tool to manually position them
- Make sure you're placing them far enough apart
- Grid layout is disabled when using custom positions

---

## 💡 Tips

1. **Place on your primary screen** - Scaling works from any baseline
2. **Leave space** - Remember images rotate slightly (±8°)
3. **Test after placing** - Run `test_overlay.py` to preview
4. **Save often** - Press **S** while placing to save progress
5. **Iterate** - Press **R** to reset and try new layouts

---

## 📊 Technical Details

### Screen Detection
- Uses `tkinter.winfo_screenwidth()` and `winfo_screenheight()`
- Detects native resolution, not scaled/DPI-adjusted
- Works with multiple monitors (uses primary)

### Scaling Algorithm
- Linear interpolation: `new_pos = old_pos × (new_screen / old_screen)`
- Separate X and Y scaling factors
- Maintains relative positions perfectly

### File Format
```json
{
  "screen_dimensions": {
    "width": <number>,
    "height": <number>
  },
  "positions": {
    "<filename>": {
      "x": <number>,
      "y": <number>,
      "type": "<image_type>",
      "angle": <number>
    }
  }
}
```

---

**Happy placing!** 🎨✨

