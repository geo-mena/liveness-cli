#!/usr/bin/env python3

import inquirer
from inquirer.themes import GreenPassion
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align

from src.commands.interactive import InteractiveCommand

try:
    from src.commands.s3 import S3Command
    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False

class CustomTheme(GreenPassion):
    def __init__(self):
        super(CustomTheme, self).__init__()
        self.Question.mark_color = '\x1b[38;2;217;120;87m'
        self.Question.brackets_color = '\x1b[38;2;217;120;87m'
        self.List.selection_color = '\x1b[38;2;217;120;87m'
        self.List.selection_cursor = '❯'

class MenuCommand:

    def __init__(self):
        self.console = Console()
        self.theme = CustomTheme()
        self.interactive_cmd = InteractiveCommand()
        if S3_AVAILABLE:
            self.s3_cmd = S3Command()
        else:
            self.s3_cmd = None

    def show_banner(self):

        content = Text()
        content.append("\n")
        content.append("███████╗██╗   ██╗██████╗ ██████╗  ██████╗ ██████╗ ████████╗\n", style="bold rgb(217,120,87)")
        content.append("██╔════╝██║   ██║██╔══██╗██╔══██╗██╔═══██╗██╔══██╗╚══██╔══╝\n", style="bold rgb(217,120,87)")
        content.append("███████╗██║   ██║██████╔╝██████╔╝██║   ██║██████╔╝   ██║   \n", style="bold rgb(217,120,87)")
        content.append("╚════██║██║   ██║██╔═══╝ ██╔═══╝ ██║   ██║██╔══██╗   ██║   \n", style="bold rgb(217,120,87)")
        content.append("███████║╚██████╔╝██║     ██║     ╚██████╔╝██║  ██║   ██║   \n", style="bold rgb(217,120,87)")
        content.append("╚══════╝ ╚═════╝ ╚═╝     ╚═╝      ╚═════╝ ╚═╝  ╚═╝   ╚═╝   \n", style="bold rgb(217,120,87)")
        content.append("\n")
        content.append("                   v1.0 | CLI Tool Backend", style="dim white")

        panel = Panel(
            Align.center(content),
            border_style="rgb(217,120,87)",
            padding=(1, 2),
            title="[bold bright_white]Bienvenido[/bold bright_white]",
            title_align="center"
        )

        self.console.print("\n")
        self.console.print(panel)
        self.console.print("\n")

    def show_menu(self):
        choices = [('Prueba de vida', 'liveness')]

        if S3_AVAILABLE:
            choices.append(('S3', 's3'))

        choices.append(('Salir', 'exit'))

        menu_question = [
            inquirer.List(
                'option',
                message='Seleccione una opción:',
                choices=choices,
            ),
        ]
        return inquirer.prompt(menu_question, theme=self.theme)

    def run(self):
        self.show_banner()

        while True:
            menu_answer = self.show_menu()

            if not menu_answer or menu_answer['option'] == 'exit':
                self.console.print("[bold green]¡Hasta luego![/bold green]")
                return True

            if menu_answer['option'] == 'liveness':
                success = self.interactive_cmd.run_liveness_flow()
                if not success:
                    self.console.print("[bold green]¡Hasta luego![/bold green]")
                    return True

                continue_question = [
                    inquirer.Confirm(
                        'continue',
                        message='¿Desea volver al menú principal?',
                        default=True,
                    ),
                ]
                continue_answer = inquirer.prompt(continue_question, theme=self.theme)

                if not continue_answer or not continue_answer['continue']:
                    self.console.print("[bold green]¡Hasta luego![/bold green]")
                    return True

            elif menu_answer['option'] == 's3':
                try:
                    success = self.s3_cmd.run_s3_flow()
                    if not success:
                        self.console.print("[bold green]¡Hasta luego![/bold green]")
                        return True

                    continue_question = [
                        inquirer.Confirm(
                            'continue',
                            message='¿Desea volver al menú principal?',
                            default=True,
                        ),
                    ]
                    continue_answer = inquirer.prompt(continue_question, theme=self.theme)

                    if not continue_answer or not continue_answer['continue']:
                        self.console.print("[bold green]¡Hasta luego![/bold green]")
                        return True
                except KeyboardInterrupt:
                    self.console.print("[yellow]Proceso cancelado por el usuario[/yellow]")
                except Exception as e:
                    self.console.print(f"[bold red]Error inesperado: {e}[/bold red]")

        return True