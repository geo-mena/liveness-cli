#!/usr/bin/env python3
"""
🌱 Comando para evaluar imágenes con servicios de liveness.
"""

import os
import time
import argparse
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Optional
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TimeElapsedColumn

from src.utils.config import DEFAULT_SAAS_API_KEY, DEFAULT_SAAS_URL, DEFAULT_WORKERS
from src.utils.helpers import validate_image_path, get_images_from_directory, get_base_filename
from src.core.image_processor import ImageProcessor
from src.core.report_generator import MarkdownReportGenerator

class EvaluateCommand:
    """Comando para evaluar imágenes con servicios de liveness."""
    
    def __init__(self):
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
        report_group.add_argument("--output", "-o", type=str, default="reports/informe_liveness.md",
                                help="Ruta donde guardar el informe generado")
        
        # Otros argumentos
        parser.add_argument("--workers", "-w", type=int, default=DEFAULT_WORKERS,
                          help="Número de workers para procesamiento paralelo")
        parser.add_argument("--verbose", "-v", action="store_true",
                          help="Mostrar información detallada durante la ejecución")
        parser.add_argument("--analyze-jpeg-quality", action="store_true",
                          help="Analizar la calidad JPEG de las imágenes (requiere dependencias adicionales)")
        
        return parser.parse_args()
    
    def run(self, args):
        """Ejecuta el comando de evaluación."""
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
            analyze_jpeg_quality=args.analyze_jpeg_quality,
        )
    
    def run_evaluation(self, image_path=None, directory_path=None, use_saas=False, 
                      saas_api_key=DEFAULT_SAAS_API_KEY, use_sdk=False, sdk_ports=None, 
                      sdk_versions=None, output_path="reports/informe_liveness.md", workers=DEFAULT_WORKERS, 
                      verbose=False, analyze_jpeg_quality=False):
        """Ejecuta la evaluación de imágenes."""
        # Configurar el procesador de imágenes con verbosidad y análisis JPEG
        image_processor = ImageProcessor(verbose=verbose, analyze_jpeg_quality=analyze_jpeg_quality)
        
        # Recopilar imágenes para procesar
        images = []
        
        if image_path:
            if validate_image_path(image_path):
                images.append(image_path)
            else:
                self.console.print(f"[bold red]Error: La imagen {image_path} no existe o no es válida.[/bold red]")
                return False
        
        elif directory_path:
            images = get_images_from_directory(directory_path)
            if not images:
                self.console.print(f"[bold red]Error: No se encontraron imágenes en el directorio {directory_path}.[/bold red]")
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
                if not image_processor.check_port_open(port):
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
                image_title = get_base_filename(image_path)
                
                # Copiar imagen al directorio temporal
                temp_img_path = os.path.join(temp_img_dir, base_filename)
                with open(image_path, "rb") as src_file, open(temp_img_path, "wb") as dst_file:
                    dst_file.write(src_file.read())
                
                # URL relativa para el informe
                relative_img_path = os.path.join("temp_images", base_filename)
                
                # Obtener información de la imagen
                image_info = image_processor.get_image_info(image_path)
                
                result = {
                    "Title": image_title,
                    "ImagePath": relative_img_path,
                    "Resolución": image_info["resolution"],
                    "Tamaño": image_info["size"]
                }
                
                # Añadir información de calidad JPEG si está habilitada
                if analyze_jpeg_quality and "jpeg_quality" in image_info:
                    result["Calidad JPEG"] = image_info["jpeg_quality"]
                
                # Evaluar con SaaS
                if use_saas:
                    saas_result = image_processor.evaluate_with_saas(
                        image_path, DEFAULT_SAAS_URL, saas_api_key
                    )
                    result["Diagnostic SaaS"] = saas_result.get("diagnostic", "Error")
                
                # Evaluar con SDK
                if use_sdk:
                    for i, (port, version) in enumerate(zip(sdk_ports, sdk_versions)):
                        sdk_url = image_processor.get_sdk_url(port)
                        sdk_result = image_processor.evaluate_with_sdk(image_path, sdk_url)
                        result[f"Diagnostic SDK {version}"] = sdk_result.get("diagnostic", "Error")
                
                return result
            
            except Exception as e:
                if verbose:
                    self.console.print(f"[bold red]Error al procesar la imagen {image_path}: {str(e)}[/bold red]")
                return {
                    "Title": get_base_filename(image_path) if image_path else "Error",
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
