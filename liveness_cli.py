#!/usr/bin/env python3
"""
Punto de entrada principal para el CLI de evaluación de liveness.
"""

import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

from src.cli import main

if __name__ == "__main__":
    main()
