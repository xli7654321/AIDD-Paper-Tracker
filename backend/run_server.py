#!/usr/bin/env python3
"""
FastAPI server startup script for AIDD Paper Tracker
"""
import uvicorn
import os
import sys

if __name__ == "__main__":
    # Add the parent directory to Python path
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    # Run the FastAPI server
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=["./", "../"],
        log_level="info"
    )