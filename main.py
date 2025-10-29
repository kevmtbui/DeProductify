"""
DeProductify - Main orchestrator
Detects productivity and triggers Performative Protocol
"""

from modules.gui import DeProductifyGUI


def main():
    """Main entry point for DeProductify"""
    app = DeProductifyGUI()
    app.run()


if __name__ == "__main__":
    main()

