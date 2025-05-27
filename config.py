#!/usr/bin/env python3
"""
Configuración global para el CLI de evaluación de liveness.
"""

# Configuración por defecto para servicios
DEFAULT_SAAS_URL = "https://api.identity-platform.io/services/evaluatePassiveLivenessToken"
DEFAULT_SAAS_API_KEY = ""
DEFAULT_SDK_BASE_URL = "http://localhost:"
DEFAULT_SDK_ENDPOINT = "/api/v1/selphid/passive-liveness/evaluate"

# Configuración por defecto para procesamiento
DEFAULT_WORKERS = 5

# Extensiones de imágenes válidas
VALID_IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff')

# Extensiones de archivos de texto válidas (para base64)
VALID_TXT_EXTENSIONS = ('.txt',)

# Configuración de timeouts (en segundos)
REQUEST_TIMEOUT = 30
PORT_CHECK_TIMEOUT = 2

# Configuración del reporte
DEFAULT_OUTPUT_FILE = "informe_liveness.md"
TEMP_IMAGES_DIR = "temp_images"

# Configuración de la imagen temporal (para archivos .txt convertidos)
DEFAULT_IMAGE_QUALITY = 85
DEFAULT_IMAGE_FORMAT = 'JPEG'