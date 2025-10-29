"""
GUI Module - Main interface for DeProductify
Modern sleek design using CustomTkinter
"""

import customtkinter as ctk
from tkinter import messagebox
import queue

# Color palette
COLORS = {
    'matcha_foam': '#C8D3A7',      # soft green tea cream
    'matcha_foam_dark': '#9BA588', # darker matcha foam for slider knobs
    'vinyl_dusk': '#4A3F35',       # worn brown-black vinyl warmth
    'laufey_blush': '#E2B8B8',     # vintage rose, romantic
    'labubu_lilac': '#B2A1D5',     # dreamy lavender whimsy (darker)
    'clairo_linen': '#F3EDE4',     # muted beige, bedroom-wall softness
    'beabadoobee_denim': '#809BBF', # washed blue, nostalgic
    'record_needle_black': '#1E1E1E' # grounding, lo-fi edge
}

# Configure CustomTkinter appearance
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class DeProductifyGUI:
    def __init__(self):
        # Create main window
        self.root = ctk.CTk()
        self.root.title("DeProductify")
        self.root.geometry("480x245")
        self.root.resizable(False, False)
        
        # Override default theme colors with our palette
        self.root.configure(fg_color=COLORS['clairo_linen'])
        
        # State variables
        self.is_running = False
        self.status_queue = queue.Queue()
        
        # Default settings
        self.settings = {}
        
        self.setup_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_ui(self):
        """Create the GUI layout"""
        
        # Title section
        title_frame = ctk.CTkFrame(
            self.root,
            fg_color="transparent",
            corner_radius=0
        )
        title_frame.pack(pady=30, fill="x", padx=20)
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="DeProductify",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=COLORS['vinyl_dusk']
        )
        title_label.pack()
        
        subtitle_label = ctk.CTkLabel(
            title_frame,
            text="Anti-Productivity Agent",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['vinyl_dusk']
        )
        subtitle_label.pack(pady=(5, 1))
        
        # Status indicator
        status_frame = ctk.CTkFrame(
            self.root,
            fg_color="transparent",
            corner_radius=0
        )
        status_frame.pack(pady=(2, 0))
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="● Stopped",
            font=ctk.CTkFont(size=13),
            text_color=COLORS['labubu_lilac']
        )
        self.status_label.pack()
        
        # Control buttons
        button_frame = ctk.CTkFrame(
            self.root,
            fg_color="transparent",
            corner_radius=0
        )
        button_frame.pack(pady=(20, 0), fill="x", padx=30)
        
        self.start_button = ctk.CTkButton(
            button_frame,
            text="Start Monitoring",
            command=self.start_monitoring,
            fg_color=COLORS['matcha_foam'],
            hover_color=COLORS['vinyl_dusk'],
            text_color=COLORS['vinyl_dusk'],
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            corner_radius=12,
            border_width=0
        )
        self.start_button.pack(side="left", padx=8, fill="x", expand=True)
        
        self.stop_button = ctk.CTkButton(
            button_frame,
            text="Stop Monitoring",
            command=self.stop_monitoring,
            fg_color=COLORS['labubu_lilac'],
            hover_color=COLORS['vinyl_dusk'],
            text_color=COLORS['vinyl_dusk'],
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            corner_radius=12,
            border_width=0,
            state="disabled"
        )
        self.stop_button.pack(side="left", padx=8, fill="x", expand=True)
        
    def start_monitoring(self):
        """Start the monitoring process"""
        if not self.is_running:
            self.is_running = True
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.status_label.configure(text="● Running", text_color=COLORS['matcha_foam'])
            
            # TODO: Start actual monitoring thread here
            # This is where you'd initialize and start the detection modules
            
    def stop_monitoring(self):
        """Stop the monitoring process"""
        if self.is_running:
            self.is_running = False
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            self.status_label.configure(text="● Stopped", text_color=COLORS['labubu_lilac'])
            
            # TODO: Stop monitoring thread and cleanup here
            
    def get_settings(self):
        """Get current settings dictionary"""
        return self.settings.copy()
        
    def on_closing(self):
        """Handle window close event"""
        if self.is_running:
            if messagebox.askokcancel("Quit", "Monitoring is active. Do you want to stop and quit?"):
                self.stop_monitoring()
                self.root.quit()
        else:
            self.root.quit()
            
    def run(self):
        """Start the GUI main loop"""
        self.root.mainloop()


def main():
    """Entry point for running the GUI standalone"""
    app = DeProductifyGUI()
    app.run()


if __name__ == "__main__":
    main()
