#!/usr/bin/env python3
"""
🌱 Punto de entrada principal para el CLI de evaluación de liveness.
"""

import sys
from src.commands.interactive import InteractiveCommand
from src.commands.evaluate import EvaluateCommand

class LivenessCLI:
    """CLI principal para la evaluación de liveness."""
    
    def __init__(self):
        self.interactive_cmd = InteractiveCommand()
        self.evaluate_cmd = EvaluateCommand()
    
    def run(self):
        """Ejecuta el CLI principal."""
        args = self.evaluate_cmd.parse_arguments()
        
        if args.interactive:
            return self.interactive_cmd.run()
        else:
            return self.evaluate_cmd.run(args)

def main():
    """Función principal que inicia el CLI."""
    cli = LivenessCLI()
    success = cli.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
