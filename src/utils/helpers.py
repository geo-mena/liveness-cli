#!/usr/bin/env python3
"""
Funciones utilitarias compartidas para el CLI de evaluación de liveness.
"""

import os
import socket
from typing import List
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
