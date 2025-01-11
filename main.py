"""
AI Assistant - Main entry point

Usage:
    python main.py          - Run in backend mode (default)
    python main.py --mode frontend  - Run in frontend mode
"""

import argparse
from backend.src.voice_assistant import VoiceAssistant
from backend.start_frontend import start_frontend
from backend.src.state.state_manager import StateManager
from backend.src.state.state_schema import StateSchema

def start_backend():
    state_manager = StateManager()
    state_manager.set_state_schema(StateSchema)
    assistant = VoiceAssistant(state_manager)
    assistant.run()

def main():
    parser = argparse.ArgumentParser(description='AI Assistant')
    parser.add_argument('--mode', 
                       choices=['backend', 'frontend'],
                       default='backend',
                       help='Start mode: backend or frontend (default: backend)')

    args = parser.parse_args()

    if args.mode == 'frontend':
        start_frontend()
    else:
        start_backend()

if __name__ == "__main__":
    main()
