#!/usr/bin/env python3
"""
Módulo para procesar y evaluar imágenes con servicios de liveness.
"""

import os
import base64
import requests
from typing import Dict, Optional
from PIL import Image
from rich.console import Console

from src.utils.config import DEFAULT_SAAS_URL, DEFAULT_SDK_BASE_URL, DEFAULT_SDK_ENDPOINT
from src.utils.helpers import check_port_open
from src.core.jpeg_quality_analyzer import JpegQualityAnalyzer

class ImageProcessor:
    """Clase para procesar y evaluar imágenes con servicios de liveness."""
    
    def __init__(self, verbose=False, analyze_jpeg_quality=False):
        self.verbose = verbose
        self.analyze_jpeg_quality = analyze_jpeg_quality
        self.console = Console()
        self.jpeg_analyzer = JpegQualityAnalyzer(verbose=verbose) if analyze_jpeg_quality else None
    
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
        """Obtiene información de la imagen (resolución, tamaño y calidad JPEG si está habilitado)."""
        try:
            img = Image.open(image_path)
            size_bytes = os.path.getsize(image_path)
            size_kb = size_bytes / 1024
            
            info = {
                "resolution": f"{img.width} x {img.height}",
                "size": f"{size_kb:.0f} KB"
            }
            
            # Añadir análisis de calidad JPEG si está habilitado
            if self.analyze_jpeg_quality and self.jpeg_analyzer:
                if img.format == 'JPEG':
                    jpeg_info = self.jpeg_analyzer.analyze_jpeg_quality(image_path)
                    if jpeg_info['quality'] is not None:
                        info["jpeg_quality"] = f"{jpeg_info['quality']}%"
                    else:
                        info["jpeg_quality"] = f"Error: {jpeg_info.get('error', 'No disponible')}"
                else:
                    info["jpeg_quality"] = "No es JPEG"
            
            return info
            
        except Exception as e:
            if self.verbose:
                self.console.print(f"[bold red]Error al obtener información de la imagen {image_path}: {str(e)}[/bold red]")
            info = {
                "resolution": "N/A",
                "size": "N/A"
            }
            if self.analyze_jpeg_quality:
                info["jpeg_quality"] = "Error"
            return info
    
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
        return check_port_open(port)

    def get_sdk_url(self, port: int) -> str:
        """Obtiene la URL completa del SDK para un puerto dado."""
        return f"{DEFAULT_SDK_BASE_URL}{port}{DEFAULT_SDK_ENDPOINT}"
    
    def get_jpeg_dependencies_status(self) -> Dict:
        """Obtiene el estado del servicio web para análisis JPEG."""
        if self.jpeg_analyzer:
            return self.jpeg_analyzer.get_dependencies_status()
        return {
            'web_service': False,
            'service_url': 'N/A',
            'recommended_install': 'Análisis JPEG no habilitado'
        }
