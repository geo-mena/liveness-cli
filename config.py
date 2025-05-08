#!/usr/bin/env python3
"""
Configuración global para el CLI de evaluación de liveness.
"""

# Configuración por defecto para servicios
DEFAULT_SAAS_URL = "https://api.identity-platform.io/services/evaluatePassiveLivenessToken"
DEFAULT_SAAS_API_KEY = "M4D1KZ6bj2LBhXupHWbnnk8E93AmhpGxVPNXY9R4"
DEFAULT_SDK_BASE_URL = "http://localhost:"
DEFAULT_SDK_ENDPOINT = "/api/v1/selphid/passive-liveness/evaluate"

# Configuración por defecto para procesamiento
DEFAULT_WORKERS = 5

# Extensiones de imágenes válidas
VALID_IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff')