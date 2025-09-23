#!/usr/bin/env python3
"""
🌱 Comando para ejecutar el CLI en modo interactivo.
"""

import inquirer
from inquirer.themes import GreenPassion
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.table import Table

from src.utils.config import DEFAULT_SAAS_API_KEY, DEFAULT_WORKERS
from src.commands.evaluate import EvaluateCommand
from src.core.image_processor import ImageProcessor

#! TEMA PERSONALIZADO PARA INQUIRER
class CustomTheme(GreenPassion):
    def __init__(self):
        super(CustomTheme, self).__init__()
        self.Question.mark_color = '\x1b[38;2;217;120;87m'
        self.Question.brackets_color = '\x1b[38;2;217;120;87m'
        self.List.selection_color = '\x1b[38;2;217;120;87m'
        self.List.selection_cursor = '❯'

class InteractiveCommand:
    """Comando para ejecutar el CLI en modo interactivo."""
    
    def __init__(self):
        self.console = Console()
        self.evaluate_cmd = EvaluateCommand()
        self.theme = CustomTheme()
    
    def run_liveness_flow(self):
        
        # Preguntar por la fuente de las imágenes
        image_questions = [
            inquirer.List(
                'source',
                message='¿Cómo desea proporcionar las imágenes?',
                choices=[
                    ('Imagen individual', 'image'),
                    ('Directorio de imágenes', 'directory'),
                ],
            ),
        ]
        image_answers = inquirer.prompt(image_questions, theme=self.theme)

        if not image_answers:
            return False

        if image_answers['source'] == 'image':
            image_path_question = [
                inquirer.Path(
                    'path',
                    message='Ingrese la ruta a la imagen:',
                    exists=True,
                    path_type=inquirer.Path.FILE,
                ),
            ]
            image_path_answer = inquirer.prompt(image_path_question, theme=self.theme)
            if not image_path_answer:
                return False
            image_path = image_path_answer['path']
            directory_path = None
        else:
            directory_path_question = [
                inquirer.Path(
                    'path',
                    message='Ingrese la ruta al directorio de imágenes',
                    exists=True,
                    path_type=inquirer.Path.DIRECTORY,
                ),
            ]
            directory_path_answer = inquirer.prompt(directory_path_question, theme=self.theme)
            if not directory_path_answer:
                return False
            directory_path = directory_path_answer['path']
            image_path = None
        
        # Preguntar por los servicios a utilizar
        service_questions = [
            inquirer.Confirm(
                'use_saas',
                message='¿Desea utilizar el servicio SaaS?',
                default=True,
            ),
            inquirer.Confirm(
                'use_sdk',
                message='¿Desea utilizar el servicio SDK local?',
                default=True,
            ),
        ]
        service_answers = inquirer.prompt(service_questions, theme=self.theme)
        if not service_answers:
            return False
        
        # Configuración del SaaS
        saas_api_key = DEFAULT_SAAS_API_KEY
        if service_answers['use_saas']:
            saas_questions = [
                inquirer.Text(
                    'api_key',
                    message='Ingrese la API key para el servicio SaaS:',
                    default=DEFAULT_SAAS_API_KEY,
                ),
            ]
            saas_answers = inquirer.prompt(saas_questions, theme=self.theme)
            if not saas_answers:
                return False
            saas_api_key = saas_answers['api_key']
        
        # Configuración del SDK
        sdk_ports = []
        sdk_versions = []
        if service_answers['use_sdk']:
            # Preguntar por el número de versiones SDK a usar
            sdk_count_question = [
                inquirer.List(
                    'count',
                    message='¿Cuántas versiones del SDK desea utilizar?',
                    choices=[
                        ('1 versión', 1),
                        ('2 versiones', 2),
                        ('3 versiones', 3),
                    ],
                ),
            ]
            sdk_count_answer = inquirer.prompt(sdk_count_question, theme=self.theme)
            if not sdk_count_answer:
                return False
            sdk_count = sdk_count_answer['count']
            
            # Configurar cada versión del SDK
            image_processor = ImageProcessor()
            for i in range(sdk_count):
                sdk_config_questions = [
                    inquirer.Text(
                        'port',
                        message=f'Ingrese el puerto para la versión {i+1} del SDK:',
                        validate=lambda _, x: x.isdigit() and 1 <= int(x) <= 65535,
                    ),
                    inquirer.Text(
                        'version',
                        message=f'Ingrese la versión del SDK {i+1}:',
                        default=f"v{i+1}",
                    ),
                ]
                sdk_config_answers = inquirer.prompt(sdk_config_questions, theme=self.theme)
                if not sdk_config_answers:
                    return False

                # Verificar si el puerto está abierto
                port = int(sdk_config_answers['port'])
                if not image_processor.check_port_open(port):
                    self.console.print(f"[bold yellow]Advertencia: El puerto {port} parece estar cerrado. Asegúrese de que el servicio SDK esté ejecutándose en ese puerto.[/bold yellow]")
                    confirm_question = [
                        inquirer.Confirm(
                            'continue',
                            message='¿Desea continuar de todos modos?',
                            default=False,
                        ),
                    ]
                    confirm_answer = inquirer.prompt(confirm_question, theme=self.theme)
                    if not confirm_answer:
                        return False
                    if not confirm_answer['continue']:
                        continue
                
                sdk_ports.append(port)
                sdk_versions.append(sdk_config_answers['version'])
        
        # Configuración del informe
        report_questions = [
            inquirer.Path(
                'output',
                message='Ingrese la ruta donde guardar el informe:',
                default='reports/informe_liveness.md',
                path_type=inquirer.Path.FILE,
            ),
        ]
        report_answers = inquirer.prompt(report_questions, theme=self.theme)
        if not report_answers:
            return False
        output_path = report_answers['output']
        
        # Configuración de análisis JPEG
        jpeg_analysis = False
        if image_path or directory_path:
            jpeg_questions = [
                inquirer.Confirm(
                    'analyze_jpeg',
                    message='¿Desea analizar la calidad JPEG de las imágenes?',
                    default=False,
                ),
            ]
            jpeg_answers = inquirer.prompt(jpeg_questions, theme=self.theme)
            if not jpeg_answers:
                return False
            jpeg_analysis = jpeg_answers['analyze_jpeg']
        
        # Otras configuraciones
        other_questions = [
            inquirer.Text(
                'workers',
                message='Ingrese el número de workers para procesamiento paralelo:',
                default=str(DEFAULT_WORKERS),
                validate=lambda _, x: x.isdigit() and int(x) > 0,
            ),
            inquirer.Confirm(
                'verbose',
                message='¿Desea mostrar información detallada durante la ejecución?',
                default=False,
            ),
        ]
        other_answers = inquirer.prompt(other_questions, theme=self.theme)
        if not other_answers:
            return False
        workers = int(other_answers['workers'])
        verbose = other_answers['verbose']
        
        # Confirmar la configuración
        table = Table(title="Resumen de configuración", border_style="rgb(217,120,87)")
        table.add_column("Configuración")
        table.add_column("Valor", style="dim white")
        
        if image_path:
            table.add_row("Imagen", image_path)
        if directory_path:
            table.add_row("Directorio", directory_path)
        if service_answers['use_saas']:
            table.add_row("SaaS API Key", f"{saas_api_key[:5]}...{saas_api_key[-5:]}")
        if service_answers['use_sdk']:
            for i, (port, version) in enumerate(zip(sdk_ports, sdk_versions)):
                table.add_row(f"SDK {i+1}", f"Puerto {port}, Versión {version}")
        table.add_row("Informe", output_path)
        table.add_row("Workers", str(workers))
        table.add_row("Verbose", "Sí" if verbose else "No")
        table.add_row("Análisis JPEG", "Habilitado" if jpeg_analysis else "Deshabilitado")
        
        self.console.print(table)
        
        confirm_question = [
            inquirer.Confirm(
                'confirm',
                message='¿Desea ejecutar la evaluación con esta configuración?',
                default=True,
            ),
        ]
        confirm_answer = inquirer.prompt(confirm_question, theme=self.theme)
        if not confirm_answer:
            return False

        if not confirm_answer['confirm']:
            self.console.print("[bold yellow]Operación cancelada por el usuario.[/bold yellow]")
            return False
        
        # Ejecutar la evaluación
        return self.evaluate_cmd.run_evaluation(
            image_path=image_path,
            directory_path=directory_path,
            use_saas=service_answers['use_saas'],
            saas_api_key=saas_api_key,
            use_sdk=service_answers['use_sdk'],
            sdk_ports=sdk_ports,
            sdk_versions=sdk_versions,
            output_path=output_path,
            workers=workers,
            verbose=verbose,
            analyze_jpeg_quality=jpeg_analysis,
        )

    def run(self):
        from src.commands.menu import MenuCommand
        menu_cmd = MenuCommand()
        return menu_cmd.run()
