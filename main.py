#!/usr/bin/env python3
"""
Signal Hunter Root Entry Point.
Adds backend module paths and runs the main orchestrator CLI.
"""

import os
import sys

# Compute the absolute path to the backend directory
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(CURRENT_DIR, "signal-hunter")

# Insert backend directory at front of sys.path
sys.path.insert(0, BACKEND_DIR)

from main import main

if __name__ == "__main__":
    main()
