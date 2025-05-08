#!/usr/bin/env python3
import os
import sys
import base64
import requests
import argparse
import pandas as pd
from typing import List, Dict, Tuple, Optional, Union
from concurrent.futures import ThreadPoolExecutor
import time
import re
from PIL import Image
import socket
from pathlib import Path
import json
import urllib.parse
import inquirer
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TimeElapsedColumn
from rich import print as rprint

console = Console()

# Configuración por defecto
DEFAULT_SAAS_URL = "https://api.identity-platform.io/services/evaluatePassiveLivenessToken"
DEFAULT_SAAS_API_KEY = "M4D1KZ6bj2LBhXupHWbnnk8E93AmhpGxVPNXY9R4"
DEFAULT_SDK_BASE_URL = "http://localhost:"
DEFAULT_SDK_ENDPOINT = "/api/v1/selphid/passive-liveness/evaluate"
DEFAULT_WORKERS = 5

class ImageProcessor:
    """Clase para procesar y evaluar imágenes con servicios de liveness."""
    
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.console = Console()
    
    def convert_image_to_base64(self, image_path: str) -> Optional[str]:
        """Convierte una imagen a formato base64."""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            if self.verbose:
                self.console.print(f"[bold red]Error al convertir la imagen {image_path}: {str(e)}[/bold red]")
            return None
    
    def get_image_info(self, image_path: str) -> Dict:
        """Obtiene información de la imagen (resolución y tamaño)."""
        try:
            img = Image.open(image_path)
            size_bytes = os.path.getsize(image_path)
            size_kb = size_bytes / 1024
            
            return {
                "resolution": f"{img.width} x {img.height}",
                "size": f"{size_kb:.0f} KB"
            }
        except Exception as e:
            if self.verbose:
                self.console.print(f"[bold red]Error al obtener información de la imagen {image_path}: {str(e)}[/bold red]")
            return {
                "resolution": "N/A",
                "size": "N/A"
            }
    
    def evaluate_with_saas(self, image_path: str, api_url: str, api_key: str) -> Dict:
        """Evalúa una imagen con el servicio SaaS de liveness."""
        try:
            # Convertir imagen a base64
            image_base64 = self.convert_image_to_base64(image_path)
            if not image_base64:
                return {"error": "Error al convertir imagen a base64"}
            
            # Preparar datos para la solicitud
            payload = {
                "imageBuffer": image_base64
            }
            
            # Configurar encabezados
            headers = {
                "x-api-key": api_key,
                "Content-Type": "application/json"
            }
            
            # Enviar solicitud a la API
            response = requests.post(api_url, json=payload, headers=headers)
            
            # Verificar si la solicitud fue exitosa
            if response.status_code == 200:
                result = response.json()
                return {
                    "status": "success",
                    "diagnostic": result.get("serviceResultLog", "Sin resultado")
                }
            else:
                return {
                    "status": "error",
                    "diagnostic": f"Error: {response.status_code} - {response.text}"
                }
        
        except Exception as e:
            return {
                "status": "error",
                "diagnostic": f"Error: {str(e)}"
            }
    
    def evaluate_with_sdk(self, image_path: str, sdk_url: str) -> Dict:
        """Evalúa una imagen con el servicio SDK de liveness."""
        try:
            # Convertir imagen a base64
            image_base64 = self.convert_image_to_base64(image_path)
            if not image_base64:
                return {"error": "Error al convertir imagen a base64"}
            
            # Preparar datos para la solicitud
            payload = {
                "image": image_base64
            }
            
            # Enviar solicitud a la API
            response = requests.post(sdk_url, json=payload)
            
            # Verificar si la solicitud fue exitosa
            if response.status_code == 200:
                result = response.json()
                return {
                    "status": "success",
                    "diagnostic": result.get("diagnostic", "Sin diagnóstico")
                }
            else:
                return {
                    "status": "error",
                    "diagnostic": f"Error: {response.status_code} - {response.text}"
                }
        
        except requests.exceptions.ConnectionError:
            return {
                "status": "error",
                "diagnostic": f"Error de conexión: No se pudo conectar a {sdk_url}. Verifique que el servicio esté activo en ese puerto."
            }
        except Exception as e:
            return {
                "status": "error",
                "diagnostic": f"Error: {str(e)}"
            }

    def check_port_open(self, port: int) -> bool:
        """Comprueba si un puerto está abierto."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = False
        try:
            sock.settimeout(2)
            result = sock.connect_ex(('localhost', port)) == 0
        except:
            pass
        finally:
            sock.close()
        return result


class MarkdownReportGenerator:
    """Clase para generar informes en formato Markdown."""
    
    def __init__(self, output_path: str, image_dir: str):
        self.output_path = output_path
        self.image_dir = image_dir
        
    def generate_report(self, results: List[Dict]) -> str:
        """Genera un informe en formato Markdown con los resultados de la evaluación."""
        
        # Crear directorio de salida si no existe
        os.makedirs(os.path.dirname(os.path.abspath(self.output_path)), exist_ok=True)
        
        # Determinar columnas basadas en el primer resultado que debería tener todas las columnas
        if not results:
            return ""
        
        # Crear encabezado de la tabla
        header = "| Title | "
        header_separator = "| ----- | "
        
        # Añadir columnas fijas
        fixed_columns = ["Foto", "Resolución", "Tamaño"]
        header += " | ".join(fixed_columns) + " | "
        header_separator += " | ".join(["-" * len(col) for col in fixed_columns]) + " | "
        
        # Añadir columnas dinámicas (SaaS y SDK versiones)
        dynamic_columns = [col for col in results[0].keys() if col.startswith("Diagnostic")]
        if dynamic_columns:
            header += " | ".join(dynamic_columns) + " |"
            header_separator += " | ".join(["-" * len(col) for col in dynamic_columns]) + " |"
        else:
            # Eliminar el último " | " si no hay columnas dinámicas
            header = header[:-3] + " |"
            header_separator = header_separator[:-3] + " |"
        
        # Iniciar contenido del informe
        report_content = f"{header}\n{header_separator}\n"
        
        # Añadir filas
        for result in results:
            row = f"| {result['Title']} | "
            
            # Añadir columnas fijas
            row += f"![Foto]({result['ImagePath']}) | {result['Resolución']} | {result['Tamaño']} | "
            
            # Añadir columnas dinámicas
            if dynamic_columns:
                row += " | ".join([result[col] for col in dynamic_columns]) + " |"
            else:
                # Eliminar el último " | " si no hay columnas dinámicas
                row = row[:-3] + " |"
            
            report_content += f"{row}\n"
        
        # Guardar informe
        with open(self.output_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        
        return report_content


class LivenessEvaluatorCLI:
    """CLI para evaluar imágenes con servicios de liveness."""
    
    def __init__(self):
        self.image_processor = ImageProcessor()
        self.console = Console()
        
    def parse_arguments(self):
        """Parsea los argumentos de línea de comandos."""
        parser = argparse.ArgumentParser(
            description="CLI para evaluar imágenes con servicios de liveness.",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        
        # Argumentos para el modo de ejecución
        parser.add_argument("--interactive", "-i", action="store_true", 
                          help="Ejecuta el CLI en modo interactivo")
        
        # Argumentos para las imágenes
        image_group = parser.add_argument_group("Configuración de imágenes")
        image_source = image_group.add_mutually_exclusive_group()
        image_source.add_argument("--image", "-img", type=str,
                               help="Ruta a una imagen individual para evaluar")
        image_source.add_argument("--directory", "-dir", type=str,
                                help="Directorio que contiene imágenes para evaluar")
        
        # Argumentos para el servicio SaaS
        saas_group = parser.add_argument_group("Configuración de SaaS")
        saas_group.add_argument("--use-saas", action="store_true",
                             help="Usar el servicio SaaS para la evaluación")
        saas_group.add_argument("--saas-api-key", type=str, default=DEFAULT_SAAS_API_KEY,
                              help="API key para el servicio SaaS")
        
        # Argumentos para el servicio SDK
        sdk_group = parser.add_argument_group("Configuración de SDK")
        sdk_group.add_argument("--use-sdk", action="store_true",
                            help="Usar el servicio SDK local para la evaluación")
        sdk_group.add_argument("--sdk-port", type=int, nargs="+",
                             help="Puerto(s) donde se ejecuta el servicio SDK local (máximo 3)")
        sdk_group.add_argument("--sdk-version", type=str, nargs="+",
                             help="Versión(es) del SDK correspondiente a cada puerto (debe coincidir con el número de puertos)")
        
        # Argumentos para el informe
        report_group = parser.add_argument_group("Configuración del informe")
        report_group.add_argument("--output", "-o", type=str, default="informe_liveness.md",
                                help="Ruta donde guardar el informe generado")
        
        # Otros argumentos
        parser.add_argument("--workers", "-w", type=int, default=DEFAULT_WORKERS,
                          help="Número de workers para procesamiento paralelo")
        parser.add_argument("--verbose", "-v", action="store_true",
                          help="Mostrar información detallada durante la ejecución")
        
        return parser.parse_args()
    
    def interactive_mode(self):
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
                if not self.image_processor.check_port_open(port):
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
            return
        
        # Ejecutar la evaluación
        return self.run_evaluation(
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
        )
    
    def run_evaluation(self, image_path=None, directory_path=None, use_saas=False, 
                      saas_api_key=DEFAULT_SAAS_API_KEY, use_sdk=False, sdk_ports=None, 
                      sdk_versions=None, output_path="informe_liveness.md", workers=DEFAULT_WORKERS, 
                      verbose=False):
        """Ejecuta la evaluación de imágenes."""
        # Configurar el procesador de imágenes con verbosidad
        self.image_processor = ImageProcessor(verbose=verbose)
        
        # Recopilar imágenes para procesar
        images = []
        
        if image_path:
            if os.path.isfile(image_path):
                images.append(image_path)
            else:
                self.console.print(f"[bold red]Error: La imagen {image_path} no existe o no es accesible.[/bold red]")
                return False
        
        elif directory_path:
            if os.path.isdir(directory_path):
                for filename in os.listdir(directory_path):
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                        images.append(os.path.join(directory_path, filename))
                
                if not images:
                    self.console.print(f"[bold red]Error: No se encontraron imágenes en el directorio {directory_path}.[/bold red]")
                    return False
            else:
                self.console.print(f"[bold red]Error: El directorio {directory_path} no existe o no es accesible.[/bold red]")
                return False
        
        else:
            self.console.print("[bold red]Error: Debe proporcionar una imagen o un directorio de imágenes.[/bold red]")
            return False
        
        # Verificar que al menos un servicio esté habilitado
        if not use_saas and not use_sdk:
            self.console.print("[bold red]Error: Debe habilitar al menos un servicio (SaaS o SDK).[/bold red]")
            return False
        
        # Verificar la configuración del SDK
        if use_sdk:
            if not sdk_ports or len(sdk_ports) == 0:
                self.console.print("[bold red]Error: Debe proporcionar al menos un puerto para el servicio SDK.[/bold red]")
                return False
            
            if len(sdk_ports) > 3:
                self.console.print("[bold red]Error: Puede proporcionar como máximo 3 puertos para el servicio SDK.[/bold red]")
                return False
            
            if sdk_versions and len(sdk_versions) != len(sdk_ports):
                self.console.print("[bold red]Error: El número de versiones del SDK debe coincidir con el número de puertos.[/bold red]")
                return False
            
            # Si no se proporcionaron versiones, usar valores por defecto
            if not sdk_versions:
                sdk_versions = [f"v{i+1}" for i in range(len(sdk_ports))]
            
            # Verificar si los puertos están abiertos
            for port in sdk_ports:
                if not self.image_processor.check_port_open(port):
                    self.console.print(f"[bold yellow]Advertencia: El puerto {port} parece estar cerrado. Asegúrese de que el servicio SDK esté ejecutándose en ese puerto.[/bold yellow]")
        
        # Crear directorio temporal para imágenes procesadas (si no existe)
        output_dir = os.path.dirname(os.path.abspath(output_path))
        temp_img_dir = os.path.join(output_dir, "temp_images")
        os.makedirs(temp_img_dir, exist_ok=True)
        
        # Iniciar procesamiento de imágenes
        self.console.print(f"[bold green]Iniciando evaluación de {len(images)} imágenes...[/bold green]")
        
        results = []
        start_time = time.time()
        
        # Función para procesar una imagen
        def process_image(image_path):
            try:
                base_filename = os.path.basename(image_path)
                image_title = os.path.splitext(base_filename)[0]
                
                # Copiar imagen al directorio temporal
                temp_img_path = os.path.join(temp_img_dir, base_filename)
                with open(image_path, "rb") as src_file, open(temp_img_path, "wb") as dst_file:
                    dst_file.write(src_file.read())
                
                # URL relativa para el informe
                relative_img_path = os.path.join("temp_images", base_filename)
                
                # Obtener información de la imagen
                image_info = self.image_processor.get_image_info(image_path)
                
                result = {
                    "Title": image_title,
                    "ImagePath": relative_img_path,
                    "Resolución": image_info["resolution"],
                    "Tamaño": image_info["size"]
                }
                
                # Evaluar con SaaS
                if use_saas:
                    saas_result = self.image_processor.evaluate_with_saas(
                        image_path, DEFAULT_SAAS_URL, saas_api_key
                    )
                    result["Diagnostic SaaS"] = saas_result.get("diagnostic", "Error")
                
                # Evaluar con SDK
                if use_sdk:
                    for i, (port, version) in enumerate(zip(sdk_ports, sdk_versions)):
                        sdk_url = f"{DEFAULT_SDK_BASE_URL}{port}{DEFAULT_SDK_ENDPOINT}"
                        sdk_result = self.image_processor.evaluate_with_sdk(image_path, sdk_url)
                        result[f"Diagnostic SDK {version}"] = sdk_result.get("diagnostic", "Error")
                
                return result
            
            except Exception as e:
                if verbose:
                    self.console.print(f"[bold red]Error al procesar la imagen {image_path}: {str(e)}[/bold red]")
                return {
                    "Title": os.path.basename(image_path),
                    "ImagePath": "N/A",
                    "Resolución": "N/A",
                    "Tamaño": "N/A",
                    **{f"Diagnostic {service}": "Error" for service in 
                      (["SaaS"] if use_saas else []) + 
                      ([f"SDK {v}" for v in sdk_versions] if use_sdk else [])}
                }
        
        # Procesar imágenes en paralelo con barra de progreso
        with Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[bold green]{task.completed}/{task.total}"),
            TimeElapsedColumn(),
        ) as progress:
            task = progress.add_task("[bold green]Procesando imágenes...", total=len(images))
            
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = []
                for image_path in images:
                    futures.append(executor.submit(process_image, image_path))
                
                for future in futures:
                    results.append(future.result())
                    progress.update(task, advance=1)
        
        # Ordenar resultados por título
        results.sort(key=lambda x: x["Title"])
        
        # Generar informe
        self.console.print("[bold green]Generando informe...[/bold green]")
        report_generator = MarkdownReportGenerator(output_path, temp_img_dir)
        report_generator.generate_report(results)
        
        # Mostrar resumen
        elapsed_time = time.time() - start_time
        self.console.print(f"[bold green]Evaluación completada en {elapsed_time:.2f} segundos.[/bold green]")
        self.console.print(f"[bold green]Informe generado en: {output_path}[/bold green]")
        
        return True
    
    def run(self):
        """Ejecuta el CLI."""
        try:
            args = self.parse_arguments()
            
            if args.interactive:
                return self.interactive_mode()
            else:
                return self.run_evaluation(
                    image_path=args.image,
                    directory_path=args.directory,
                    use_saas=args.use_saas,
                    saas_api_key=args.saas_api_key,
                    use_sdk=args.use_sdk,
                    sdk_ports=args.sdk_port,
                    sdk_versions=args.sdk_version,
                    output_path=args.output,
                    workers=args.workers,
                    verbose=args.verbose,
                )
        
        except KeyboardInterrupt:
            self.console.print("\n[bold yellow]Operación interrumpida por el usuario.[/bold yellow]")
            return False
        
        except Exception as e:
            self.console.print(f"[bold red]Error inesperado: {str(e)}[/bold red]")
            if args.verbose:
                import traceback
                self.console.print(traceback.format_exc())
            return False


if __name__ == "__main__":
    cli = LivenessEvaluatorCLI()
    success = cli.run()
    sys.exit(0 if success else 1)