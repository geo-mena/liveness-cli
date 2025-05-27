#!/usr/bin/env python3
"""
Módulo para procesar y evaluar imágenes con servicios de liveness.
Soporta tanto archivos de imagen tradicionales como archivos .txt con contenido base64.
"""

import os
import base64
import socket
import requests
import io
from typing import Dict, Optional
from PIL import Image
from rich.console import Console

from config import DEFAULT_SAAS_URL, DEFAULT_SDK_BASE_URL, DEFAULT_SDK_ENDPOINT

class ImageProcessor:
    """Clase para procesar y evaluar imágenes con servicios de liveness."""
    
    def __init__(self, verbose=False):
        """
        Inicializa el procesador de imágenes.
        
        Args:
            verbose (bool): Si debe mostrar información detallada durante la ejecución
        """
        self.verbose = verbose
        self.console = Console()
    
    def convert_image_to_base64(self, image_path: str) -> Optional[str]:
        """
        Convierte una imagen a formato base64.
        
        Args:
            image_path (str): Ruta al archivo de imagen
            
        Returns:
            Optional[str]: String base64 de la imagen o None si hay error
        """
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            if self.verbose:
                self.console.print(f"[bold red]Error al convertir la imagen {image_path}: {str(e)}[/bold red]")
            return None
    
    def read_base64_from_txt(self, txt_path: str) -> Optional[str]:
        """
        Lee el código base64 directamente de un archivo .txt.
        
        Args:
            txt_path (str): Ruta al archivo .txt que contiene base64
            
        Returns:
            Optional[str]: Contenido base64 del archivo o None si hay error
        """
        try:
            with open(txt_path, "r", encoding='utf-8') as txt_file:
                content = txt_file.read().strip()
                
                # Remover posibles prefijos de data URL si existen
                if content.startswith('data:'):
                    # Buscar la coma que separa el prefijo del contenido base64
                    comma_index = content.find(',')
                    if comma_index != -1:
                        content = content[comma_index + 1:]
                
                # Verificar si el contenido parece ser base64 válido
                if self.is_valid_base64(content):
                    return content
                else:
                    if self.verbose:
                        self.console.print(f"[bold yellow]Advertencia: El archivo {txt_path} no contiene base64 válido[/bold yellow]")
                    return None
                    
        except Exception as e:
            if self.verbose:
                self.console.print(f"[bold red]Error al leer el archivo txt {txt_path}: {str(e)}[/bold red]")
            return None
    
    def is_valid_base64(self, content: str) -> bool:
        """
        Verifica si una cadena es base64 válido.
        
        Args:
            content (str): Contenido a verificar
            
        Returns:
            bool: True si es base64 válido, False en caso contrario
        """
        try:
            # Limpiar espacios en blanco y saltos de línea
            content = content.replace('\n', '').replace('\r', '').replace(' ', '')
            
            # Verificar que la longitud sea múltiplo de 4 (característica del base64)
            if len(content) % 4 != 0:
                return False
            
            # Intentar decodificar el base64
            decoded = base64.b64decode(content, validate=True)
            
            # Verificar si el resultado decodificado puede ser una imagen
            # Comprobar tamaño mínimo y headers comunes de imágenes
            if len(decoded) < 100:  # Muy pequeño para ser una imagen
                return False
            
            # Verificar headers de formatos de imagen comunes
            # JPEG: FF D8 FF
            # PNG: 89 50 4E 47
            # GIF: 47 49 46
            # BMP: 42 4D
            image_headers = [
                b'\xff\xd8\xff',  # JPEG
                b'\x89\x50\x4e\x47',  # PNG
                b'\x47\x49\x46',  # GIF
                b'\x42\x4d',  # BMP
                b'RIFF',  # WebP (parte del header)
            ]
            
            # Verificar si comienza con algún header conocido
            for header in image_headers:
                if decoded.startswith(header):
                    return True
            
            # Si no reconoce el header, pero se decodificó correctamente,
            # intentar abrir como imagen con PIL
            try:
                img = Image.open(io.BytesIO(decoded))
                img.verify()  # Verificar que es una imagen válida
                return True
            except:
                return False
            
        except Exception:
            return False
    
    def get_image_info_from_base64(self, base64_content: str, filename: str) -> Dict:
        """
        Obtiene información de la imagen desde contenido base64.
        
        Args:
            base64_content (str): Contenido base64 de la imagen
            filename (str): Nombre del archivo para referencia
            
        Returns:
            Dict: Diccionario con información de la imagen (resolución y tamaño)
        """
        try:
            # Limpiar el contenido base64
            base64_content = base64_content.replace('\n', '').replace('\r', '').replace(' ', '')
            
            # Decodificar base64
            image_data = base64.b64decode(base64_content)
            
            # Crear objeto Image desde los datos
            img = Image.open(io.BytesIO(image_data))
            
            # Calcular tamaño
            size_bytes = len(image_data)
            size_kb = size_bytes / 1024
            
            return {
                "resolution": f"{img.width} x {img.height}",
                "size": f"{size_kb:.0f} KB"
            }
        except Exception as e:
            if self.verbose:
                self.console.print(f"[bold red]Error al obtener información de la imagen desde base64 {filename}: {str(e)}[/bold red]")
            return {
                "resolution": "N/A",
                "size": "N/A"
            }
    
    def get_image_info(self, image_path: str) -> Dict:
        """
        Obtiene información de la imagen (resolución y tamaño).
        
        Args:
            image_path (str): Ruta al archivo de imagen
            
        Returns:
            Dict: Diccionario con información de la imagen (resolución y tamaño)
        """
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
    
    def evaluate_with_saas(self, file_path: str, api_url: str, api_key: str, is_txt_file: bool = False) -> Dict:
        """
        Evalúa una imagen con el servicio SaaS de liveness.
        
        Args:
            file_path (str): Ruta al archivo (imagen o .txt)
            api_url (str): URL de la API del servicio SaaS
            api_key (str): Clave de API para el servicio
            is_txt_file (bool): True si el archivo es .txt con base64
            
        Returns:
            Dict: Resultado de la evaluación
        """
        try:
            # Obtener base64 según el tipo de archivo
            if is_txt_file:
                image_base64 = self.read_base64_from_txt(file_path)
            else:
                image_base64 = self.convert_image_to_base64(file_path)
                
            if not image_base64:
                return {
                    "status": "error",
                    "diagnostic": "Error al obtener imagen en base64"
                }
            
            # Preparar datos para la solicitud
            payload = {
                "imageBuffer": image_base64
            }
            
            # Configurar encabezados
            headers = {
                "x-api-key": api_key,
                "Content-Type": "application/json"
            }
            
            if self.verbose:
                self.console.print(f"[blue]Enviando solicitud SaaS para: {os.path.basename(file_path)}[/blue]")
            
            # Enviar solicitud a la API
            response = requests.post(api_url, json=payload, headers=headers, timeout=30)
            
            # Verificar si la solicitud fue exitosa
            if response.status_code == 200:
                result = response.json()
                return {
                    "status": "success",
                    "diagnostic": result.get("serviceResultLog", "Sin resultado")
                }
            else:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_detail = response.json().get("message", response.text)
                    error_msg += f" - {error_detail}"
                except:
                    error_msg += f" - {response.text[:200]}"
                
                return {
                    "status": "error",
                    "diagnostic": f"Error: {error_msg}"
                }
        
        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "diagnostic": "Error: Timeout al conectar con el servicio SaaS"
            }
        except requests.exceptions.ConnectionError:
            return {
                "status": "error",
                "diagnostic": "Error: No se pudo conectar al servicio SaaS"
            }
        except Exception as e:
            return {
                "status": "error",
                "diagnostic": f"Error: {str(e)}"
            }
    
    def evaluate_with_sdk(self, file_path: str, sdk_url: str, is_txt_file: bool = False) -> Dict:
        """
        Evalúa una imagen con el servicio SDK de liveness.
        
        Args:
            file_path (str): Ruta al archivo (imagen o .txt)
            sdk_url (str): URL del servicio SDK
            is_txt_file (bool): True si el archivo es .txt con base64
            
        Returns:
            Dict: Resultado de la evaluación
        """
        try:
            # Obtener base64 según el tipo de archivo
            if is_txt_file:
                image_base64 = self.read_base64_from_txt(file_path)
            else:
                image_base64 = self.convert_image_to_base64(file_path)
                
            if not image_base64:
                return {
                    "status": "error",
                    "diagnostic": "Error al obtener imagen en base64"
                }
            
            # Preparar datos para la solicitud
            payload = {
                "image": image_base64
            }
            
            if self.verbose:
                self.console.print(f"[blue]Enviando solicitud SDK para: {os.path.basename(file_path)}[/blue]")
            
            # Enviar solicitud a la API
            response = requests.post(sdk_url, json=payload, timeout=30)
            
            # Verificar si la solicitud fue exitosa
            if response.status_code == 200:
                result = response.json()
                return {
                    "status": "success",
                    "diagnostic": result.get("diagnostic", "Sin diagnóstico")
                }
            else:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_detail = response.json().get("message", response.text)
                    error_msg += f" - {error_detail}"
                except:
                    error_msg += f" - {response.text[:200]}"
                
                return {
                    "status": "error",
                    "diagnostic": f"Error: {error_msg}"
                }
        
        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "diagnostic": "Error: Timeout al conectar con el servicio SDK"
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

    def check_port_open(self, port: int, host: str = 'localhost', timeout: int = 2) -> bool:
        """
        Comprueba si un puerto está abierto.
        
        Args:
            port (int): Puerto a verificar
            host (str): Host a verificar (por defecto localhost)
            timeout (int): Timeout en segundos para la conexión
            
        Returns:
            bool: True si el puerto está abierto, False en caso contrario
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = False
        try:
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port)) == 0
        except Exception as e:
            if self.verbose:
                self.console.print(f"[yellow]Error al verificar puerto {port}: {str(e)}[/yellow]")
        finally:
            sock.close()
        return result

    def get_sdk_url(self, port: int) -> str:
        """
        Obtiene la URL completa del SDK para un puerto dado.
        
        Args:
            port (int): Puerto del servicio SDK
            
        Returns:
            str: URL completa del servicio SDK
        """
        return f"{DEFAULT_SDK_BASE_URL}{port}{DEFAULT_SDK_ENDPOINT}"

    def create_placeholder_image_from_base64(self, base64_content: str, output_path: str) -> bool:
        """
        Crea una imagen temporal desde base64 para incluir en el reporte.
        
        Args:
            base64_content (str): Contenido base64 de la imagen
            output_path (str): Ruta donde guardar la imagen
            
        Returns:
            bool: True si se creó exitosamente, False en caso contrario
        """
        try:
            # Limpiar el contenido base64
            base64_content = base64_content.replace('\n', '').replace('\r', '').replace(' ', '')
            
            # Decodificar base64
            image_data = base64.b64decode(base64_content)
            
            # Verificar que sea una imagen válida antes de guardar
            img = Image.open(io.BytesIO(image_data))
            img.verify()
            
            # Reabrir la imagen para guardarla (verify() cierra el objeto)
            img = Image.open(io.BytesIO(image_data))
            
            # Convertir a RGB si es necesario (para JPEG)
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Guardar como archivo de imagen
            img.save(output_path, 'JPEG', quality=85)
            
            if self.verbose:
                self.console.print(f"[green]Imagen temporal creada: {output_path}[/green]")
            
            return True
            
        except Exception as e:
            if self.verbose:
                self.console.print(f"[bold red]Error al crear imagen desde base64: {str(e)}[/bold red]")
            return False

    def validate_image_file(self, file_path: str) -> bool:
        """
        Valida si un archivo es una imagen válida.
        
        Args:
            file_path (str): Ruta al archivo
            
        Returns:
            bool: True si es una imagen válida, False en caso contrario
        """
        try:
            with Image.open(file_path) as img:
                img.verify()
            return True
        except Exception:
            return False

    def validate_txt_file(self, file_path: str) -> bool:
        """
        Valida si un archivo .txt contiene base64 válido.
        
        Args:
            file_path (str): Ruta al archivo .txt
            
        Returns:
            bool: True si contiene base64 válido, False en caso contrario
        """
        try:
            content = self.read_base64_from_txt(file_path)
            return content is not None and self.is_valid_base64(content)
        except Exception:
            return False

    def get_file_type_info(self, file_path: str) -> Dict:
        """
        Obtiene información sobre el tipo de archivo.
        
        Args:
            file_path (str): Ruta al archivo
            
        Returns:
            Dict: Información del tipo de archivo
        """
        file_extension = os.path.splitext(file_path)[1].lower()
        file_size = os.path.getsize(file_path)
        
        return {
            "extension": file_extension,
            "size_bytes": file_size,
            "size_kb": file_size / 1024,
            "is_image": file_extension in ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'),
            "is_txt": file_extension == '.txt'
        }

    def batch_validate_files(self, file_paths: list, is_txt_mode: bool = False) -> Dict:
        """
        Valida un lote de archivos.
        
        Args:
            file_paths (list): Lista de rutas de archivos
            is_txt_mode (bool): True si se esperan archivos .txt
            
        Returns:
            Dict: Resultados de la validación
        """
        valid_files = []
        invalid_files = []
        
        for file_path in file_paths:
            if is_txt_mode:
                if self.validate_txt_file(file_path):
                    valid_files.append(file_path)
                else:
                    invalid_files.append(file_path)
            else:
                if self.validate_image_file(file_path):
                    valid_files.append(file_path)
                else:
                    invalid_files.append(file_path)
        
        return {
            "valid_files": valid_files,
            "invalid_files": invalid_files,
            "total_files": len(file_paths),
            "valid_count": len(valid_files),
            "invalid_count": len(invalid_files)
        }