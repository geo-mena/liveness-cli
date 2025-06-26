#!/usr/bin/env python3
"""
Punto de entrada principal para el CLI de evaluación de liveness.
"""

import sys
from cli_interface import LivenessEvaluatorCLI

def main():
    """Función principal que inicia el CLI."""
    cli = LivenessEvaluatorCLI()
    success = cli.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()