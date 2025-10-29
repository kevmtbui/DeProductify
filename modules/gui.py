"""
GUI Module - Main interface for DeProductify
Modern sleek design using CustomTkinter
"""

import customtkinter as ctk
from tkinter import messagebox
import queue
import threading

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
    def __init__(self, orchestrator=None):
        # Create main window
        self.root = ctk.CTk()
        self.root.title("DeProductify")
        self.root.geometry("480x320")
        self.root.resizable(False, False)
        
        # Override default theme colors with our palette
        self.root.configure(fg_color=COLORS['clairo_linen'])
        
        # State variables
        self.is_running = False
        self.status_queue = queue.Queue()
        self.orchestrator = orchestrator
        self.monitoring_thread = None
        
        # Default settings
        self.settings = {}
        
        self.setup_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start checking for status updates
        self.check_status_updates()
        
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
        
        # Score display
        score_frame = ctk.CTkFrame(
            self.root,
            fg_color="transparent",
            corner_radius=0
        )
        score_frame.pack(pady=(10, 0))
        
        self.score_label = ctk.CTkLabel(
            score_frame,
            text="Productivity Score: 0.00 | Baseline: 0.0",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['vinyl_dusk']
        )
        self.score_label.pack()
        
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
        if not self.is_running and self.orchestrator:
            self.is_running = True
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.status_label.configure(text="● Running", text_color=COLORS['matcha_foam'])
            
            # Start monitoring in separate thread to keep GUI responsive
            self.monitoring_thread = threading.Thread(
                target=self._run_monitoring,
                daemon=True
            )
            self.monitoring_thread.start()
            
    def stop_monitoring(self):
        """Stop the monitoring process"""
        if self.is_running:
            self.is_running = False
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            self.status_label.configure(text="● Stopped", text_color=COLORS['labubu_lilac'])
            
            # Stop the orchestrator monitoring
            if self.orchestrator:
                self.orchestrator.stop_monitoring()
    
    def _run_monitoring(self):
        """Run monitoring in background thread"""
        try:
            if self.orchestrator:
                self.orchestrator.start_monitoring_with_gui(self.status_queue)
        except Exception as e:
            self.status_queue.put(("error", str(e)))
    
    def check_status_updates(self):
        """Check for status updates from monitoring thread"""
        try:
            while not self.status_queue.empty():
                msg_type, data = self.status_queue.get_nowait()
                
                if msg_type == "score":
                    # Update score display
                    score, baseline, raw = data
                    self.score_label.configure(
                        text=f"Score: {score:.2f} (Raw: {raw:.2f} + Baseline: {baseline:.1f})"
                    )
                elif msg_type == "stopped":
                    # Monitoring stopped
                    self.is_running = False
                    self.start_button.configure(state="normal")
                    self.stop_button.configure(state="disabled")
                    self.status_label.configure(text="● Stopped", text_color=COLORS['labubu_lilac'])
                elif msg_type == "error":
                    messagebox.showerror("Error", f"Monitoring error: {data}")
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.check_status_updates)
            
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
