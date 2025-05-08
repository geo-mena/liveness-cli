#!/usr/bin/env python3
"""
Módulo para procesar y evaluar imágenes con servicios de liveness.
"""

import os
import base64
import socket
import requests
from typing import Dict, Optional
from PIL import Image
from rich.console import Console

from config import DEFAULT_SAAS_URL, DEFAULT_SDK_BASE_URL, DEFAULT_SDK_ENDPOINT

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

    def get_sdk_url(self, port: int) -> str:
        """Obtiene la URL completa del SDK para un puerto dado."""
        return f"{DEFAULT_SDK_BASE_URL}{port}{DEFAULT_SDK_ENDPOINT}"