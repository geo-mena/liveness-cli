#!/usr/bin/env python3
"""
Comando para ejecutar el CLI en modo interactivo.
"""

import inquirer
from rich.console import Console

from src.utils.config import DEFAULT_SAAS_API_KEY, DEFAULT_WORKERS
from src.commands.evaluate import EvaluateCommand
from src.core.image_processor import ImageProcessor

class InteractiveCommand:
    """Comando para ejecutar el CLI en modo interactivo."""
    
    def __init__(self):
        self.console = Console()
        self.evaluate_cmd = EvaluateCommand()
    
    def run(self):
        """Ejecuta el CLI en modo interactivo."""
        self.console.print("[bold green]Evaluador de Passive Liveness - Modo Interactivo[/bold green]")
        
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
        image_answers = inquirer.prompt(image_questions)
        
        if image_answers['source'] == 'image':
            image_path_question = [
                inquirer.Path(
                    'path',
                    message='Ingrese la ruta a la imagen:',
                    exists=True,
                    path_type=inquirer.Path.FILE,
                ),
            ]
            image_path_answer = inquirer.prompt(image_path_question)
            image_path = image_path_answer['path']
            directory_path = None
        else:
            directory_path_question = [
                inquirer.Path(
                    'path',
                    message='Ingrese la ruta al directorio de imágenes:',
                    exists=True,
                    path_type=inquirer.Path.DIRECTORY,
                ),
            ]
            directory_path_answer = inquirer.prompt(directory_path_question)
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
        service_answers = inquirer.prompt(service_questions)
        
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
            saas_answers = inquirer.prompt(saas_questions)
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
            sdk_count_answer = inquirer.prompt(sdk_count_question)
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
                sdk_config_answers = inquirer.prompt(sdk_config_questions)
                
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
                    confirm_answer = inquirer.prompt(confirm_question)
                    if not confirm_answer['continue']:
                        continue
                
                sdk_ports.append(port)
                sdk_versions.append(sdk_config_answers['version'])
        
        # Configuración del informe
        report_questions = [
            inquirer.Path(
                'output',
                message='Ingrese la ruta donde guardar el informe:',
                default='informe_liveness.md',
                path_type=inquirer.Path.FILE,
            ),
        ]
        report_answers = inquirer.prompt(report_questions)
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
            jpeg_answers = inquirer.prompt(jpeg_questions)
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
        other_answers = inquirer.prompt(other_questions)
        workers = int(other_answers['workers'])
        verbose = other_answers['verbose']
        
        # Confirmar la configuración
        self.console.print("\n[bold blue]Resumen de configuración:[/bold blue]")
        if image_path:
            self.console.print(f"Imagen: {image_path}")
        if directory_path:
            self.console.print(f"Directorio: {directory_path}")
        if service_answers['use_saas']:
            self.console.print(f"SaaS API Key: {saas_api_key[:5]}...{saas_api_key[-5:]}")
        if service_answers['use_sdk']:
            for i, (port, version) in enumerate(zip(sdk_ports, sdk_versions)):
                self.console.print(f"SDK {i+1}: Puerto {port}, Versión {version}")
        self.console.print(f"Informe: {output_path}")
        self.console.print(f"Workers: {workers}")
        self.console.print(f"Verbose: {verbose}")
        self.console.print(f"Análisis JPEG: {'Habilitado' if jpeg_analysis else 'Deshabilitado'}")
        
        confirm_question = [
            inquirer.Confirm(
                'confirm',
                message='¿Desea ejecutar la evaluación con esta configuración?',
                default=True,
            ),
        ]
        confirm_answer = inquirer.prompt(confirm_question)
        
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
