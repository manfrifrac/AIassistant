"""
AI Assistant - Main entry point

Usage:
    python main.py          - Run in backend mode (default)
    python main.py --mode frontend  - Run in frontend mode
"""

import argparse
import logging
import uvicorn
import asyncio
from backend.src.core_components import CoreComponents  # Import CoreComponents
from backend.src.app import app  # Import FastAPI app
from backend.start_frontend import start_frontend

async def start_backend_async(core: CoreComponents):
    config = uvicorn.Config(app, host="0.0.0.0", port=8000)
    server = uvicorn.Server(config)
    await server.serve()

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
        asyncio.run(start_backend_async(core))

if __name__ == "__main__":
    main()
