"""
AI Assistant - Main entry point

Usage:
    python main.py          - Run in backend mode (default)
    python main.py --mode frontend  - Run in frontend mode
"""

import argparse
from backend.src.core_components import CoreComponents  # Import CoreComponents
from backend.start_frontend import start_frontend
import logging

def start_backend(core: CoreComponents):
    core.assistant.run()

def main():
    parser = argparse.ArgumentParser(description='AI Assistant')
    parser.add_argument('--mode', 
                       choices=['backend', 'frontend'],
                       default='backend',
                       help='Start mode: backend or frontend (default: backend)')

    args = parser.parse_args()

    core = CoreComponents.get_instance()

    if args.mode == 'frontend':
        start_frontend(core)
    else:
        start_backend(core)

if __name__ == "__main__":
    main()
