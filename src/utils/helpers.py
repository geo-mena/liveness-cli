#!/usr/bin/env python3
"""
Funciones utilitarias compartidas para el CLI de evaluación de liveness.
"""

import os
import socket
from datetime import datetime
from typing import List, Tuple
from src.utils.config import VALID_IMAGE_EXTENSIONS

def validate_image_path(image_path: str) -> bool:
    """Valida que la ruta de imagen existe y es un archivo válido."""
    if not os.path.isfile(image_path):
        return False
    
    return any(image_path.lower().endswith(ext) for ext in VALID_IMAGE_EXTENSIONS)

def get_images_from_directory(directory_path: str) -> List[str]:
    """Obtiene todas las imágenes válidas de un directorio."""
    if not os.path.isdir(directory_path):
        return []
    
    images = []
    for filename in os.listdir(directory_path):
        if filename.lower().endswith(VALID_IMAGE_EXTENSIONS):
            images.append(os.path.join(directory_path, filename))
    
    return sorted(images)

def check_port_open(port: int, host: str = 'localhost', timeout: int = 2) -> bool:
    """Comprueba si un puerto está abierto."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = False
    try:
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port)) == 0
    except:
        pass
    finally:
        sock.close()
    return result

def ensure_directory_exists(file_path: str) -> None:
    """Asegura que el directorio padre de un archivo existe."""
    directory = os.path.dirname(os.path.abspath(file_path))
    os.makedirs(directory, exist_ok=True)

def get_base_filename(file_path: str) -> str:
    """Obtiene el nombre base de un archivo sin extensión."""
    return os.path.splitext(os.path.basename(file_path))[0]

def create_dated_directory(base_reports_dir: str) -> str:
    """Crea un subdirectorio con la fecha de hoy dentro del directorio base de reportes.
    
    Args:
        base_reports_dir: Directorio base donde crear el subdirectorio con fecha
        
    Returns:
        str: Ruta del directorio creado con formato YYYY-MM-DD
    """
    today = datetime.now().strftime("%Y-%m-%d")
    dated_dir = os.path.join(base_reports_dir, today)
    os.makedirs(dated_dir, exist_ok=True)
    return dated_dir

def get_unique_report_path(directory: str, base_filename: str, extension: str = ".md") -> str:
    """Genera una ruta única para el reporte, añadiendo un número secuencial si es necesario.
    
    Args:
        directory: Directorio donde crear el archivo
        base_filename: Nombre base del archivo sin extensión
        extension: Extensión del archivo (por defecto .md)
        
    Returns:
        str: Ruta completa única para el reporte
    """
    base_path = os.path.join(directory, base_filename + extension)
    
    # Si el archivo no existe, devolver la ruta base
    if not os.path.exists(base_path):
        return base_path
    
    # Si existe, buscar un número secuencial disponible
    counter = 1
    while True:
        numbered_filename = f"{base_filename}_{counter:02d}{extension}"
        numbered_path = os.path.join(directory, numbered_filename)
        
        if not os.path.exists(numbered_path):
            return numbered_path
        
        counter += 1
        
        # Protección contra bucle infinito (máximo 99 archivos)
        if counter > 99:
            raise ValueError(f"Demasiados archivos con el mismo nombre base: {base_filename}")

def create_report_path_with_date(base_output_path: str) -> Tuple[str, str]:
    """Crea una ruta de reporte con subdirectorio de fecha y manejo de nombres duplicados.
    
    Args:
        base_output_path: Ruta de salida original (ej: "reports/informe_liveness.md")
        
    Returns:
        Tuple[str, str]: (ruta_completa_del_reporte, directorio_con_fecha)
    """
    # Extraer componentes de la ruta
    base_dir = os.path.dirname(base_output_path)
    filename_with_ext = os.path.basename(base_output_path)
    filename_base = get_base_filename(filename_with_ext)
    extension = os.path.splitext(filename_with_ext)[1]
    
    # Si no hay directorio base, usar "reports" por defecto
    if not base_dir:
        base_dir = "reports"
    
    # Crear directorio con fecha
    dated_directory = create_dated_directory(base_dir)
    
    # Obtener ruta única para el reporte
    unique_report_path = get_unique_report_path(dated_directory, filename_base, extension)
    
    return unique_report_path, dated_directory
