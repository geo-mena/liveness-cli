#!/usr/bin/env python3
"""
🌱 Analizador de calidad JPEG usando servicio web. Implementación simplificada que usa únicamente el endpoint externo.
"""

import requests
import base64
from typing import Dict, List, Optional
from PIL import Image

class JpegQualityAnalyzer:
    """Clase para analizar la calidad de compresión de imágenes JPEG usando servicio web."""
    
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.endpoint = "https://send.up.railway.app/v1/analyze/quality"
    
    def analyze_jpeg_quality(self, image_path: str) -> Dict:
        """
        Analiza la calidad JPEG de una imagen usando el servicio web.
        
        Args:
            image_path: Ruta a la imagen JPEG
            
        Returns:
            Dict con información de calidad y formato progresivo
        """
        try:
            # Verificar que es una imagen JPEG
            if not self._is_jpeg(image_path):
                return {
                    'quality': None,
                    'is_progressive': False,
                    'method': 'not_jpeg',
                    'error': 'La imagen no es un JPEG válido'
                }
            
            # Convertir imagen a base64
            base64_data = self._image_to_base64(image_path)
            if not base64_data:
                return {
                    'quality': None,
                    'is_progressive': False,
                    'method': 'conversion_error',
                    'error': 'Error convirtiendo imagen a base64'
                }
            
            # Llamar al servicio web
            return self._call_quality_service([base64_data], [0])[0]
            
        except Exception as e:
            return {
                'quality': None,
                'is_progressive': False,
                'method': 'service_error',
                'error': f'Error llamando al servicio: {str(e)}'
            }
    
    def analyze_multiple_images(self, image_paths: List[str]) -> List[Dict]:
        """
        Analiza múltiples imágenes en una sola llamada al servicio.
        
        Args:
            image_paths: Lista de rutas a imágenes JPEG
            
        Returns:
            Lista de diccionarios con análisis de cada imagen
        """
        try:
            base64_images = []
            valid_indices = []
            results = []
            
            # Procesar cada imagen
            for i, image_path in enumerate(image_paths):
                if self._is_jpeg(image_path):
                    base64_data = self._image_to_base64(image_path)
                    if base64_data:
                        base64_images.append(base64_data)
                        valid_indices.append(i)
                        continue
                
                # Si la imagen no es válida, añadir error
                results.append({
                    'quality': None,
                    'is_progressive': False,
                    'method': 'invalid_image',
                    'error': f'Imagen no válida: {image_path}'
                })
            
            # Llamar al servicio web con todas las imágenes válidas
            if base64_images:
                service_results = self._call_quality_service(base64_images, valid_indices)
                
                # Insertar resultados en las posiciones correctas
                service_index = 0
                for i in range(len(image_paths)):
                    if i in valid_indices:
                        results.insert(i, service_results[service_index])
                        service_index += 1
            
            return results
            
        except Exception as e:
            # Retornar errores para todas las imágenes
            return [{
                'quality': None,
                'is_progressive': False,
                'method': 'batch_error',
                'error': f'Error en análisis por lotes: {str(e)}'
            } for _ in image_paths]
    
    def _is_jpeg(self, image_path: str) -> bool:
        """Verifica si el archivo es un JPEG válido."""
        try:
            with Image.open(image_path) as img:
                return img.format == 'JPEG'
        except Exception:
            return False
    
    def _image_to_base64(self, image_path: str) -> Optional[str]:
        """Convierte una imagen a formato base64 con prefijo."""
        try:
            with open(image_path, "rb") as image_file:
                base64_data = base64.b64encode(image_file.read()).decode('utf-8')
                return f"data:image/jpeg;base64,{base64_data}"
        except Exception:
            return None
    
    def _call_quality_service(self, base64_images: List[str], indices: List[int]) -> List[Dict]:
        """Llama al servicio web de análisis de calidad."""
        try:
            # Preparar payload
            payload = {
                "base64_codes": base64_images
            }
            
            # Llamar al servicio
            response = requests.post(
                self.endpoint,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                return self._parse_service_response(response.json(), indices)
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                return [{
                    'quality': None,
                    'is_progressive': False,
                    'method': 'http_error',
                    'error': error_msg
                } for _ in indices]
                
        except requests.exceptions.Timeout:
            return [{
                'quality': None,
                'is_progressive': False,
                'method': 'timeout_error',
                'error': 'Timeout llamando al servicio'
            } for _ in indices]
        except requests.exceptions.RequestException as e:
            return [{
                'quality': None,
                'is_progressive': False,
                'method': 'request_error',
                'error': f'Error de conexión: {str(e)}'
            } for _ in indices]
        except Exception as e:
            return [{
                'quality': None,
                'is_progressive': False,
                'method': 'parse_error',
                'error': f'Error procesando respuesta: {str(e)}'
            } for _ in indices]
    
    def _parse_service_response(self, response_data: Dict, indices: List[int]) -> List[Dict]:
        """Parsea la respuesta del servicio web."""
        results = []
        
        try:
            if not response_data.get('success', False):
                # Error en el servicio
                error_msg = response_data.get('message', 'Error desconocido del servicio')
                return [{
                    'quality': None,
                    'is_progressive': False,
                    'method': 'service_error',
                    'error': error_msg
                } for _ in indices]
            
            analyses = response_data.get('data', {}).get('analyses', [])
            
            for i, analysis_data in enumerate(analyses):
                if 'error' in analysis_data:
                    # Imagen con error
                    results.append({
                        'quality': None,
                        'is_progressive': False,
                        'method': 'image_error',
                        'error': analysis_data['error']
                    })
                else:
                    # Imagen analizada correctamente
                    analysis = analysis_data.get('analysis', {})
                    quality_metrics = analysis.get('quality_metrics', {})
                    
                    quality = quality_metrics.get('jpeg_quality')
                    is_progressive = quality_metrics.get('is_progressive', False)
                    compression_type = quality_metrics.get('compression_type', 'baseline')
                    
                    # Verificar que tenemos datos válidos
                    if quality is not None:
                        results.append({
                            'quality': int(quality),
                            'is_progressive': is_progressive,
                            'method': 'web_service',
                            'error': None,
                            'compression_type': compression_type
                        })
                    else:
                        results.append({
                            'quality': None,
                            'is_progressive': False,
                            'method': 'invalid_response',
                            'error': 'Respuesta del servicio sin datos de calidad'
                        })
            
            return results
            
        except Exception as e:
            return [{
                'quality': None,
                'is_progressive': False,
                'method': 'parse_error',
                'error': f'Error parseando respuesta: {str(e)}'
            } for _ in indices]
    
    def get_analysis_summary(self, image_path: str) -> str:
        """Obtiene un resumen textual del análisis de calidad."""
        result = self.analyze_jpeg_quality(image_path)
        
        if result['quality'] is None:
            return f"No se pudo analizar: {result.get('error', 'Error desconocido')}"
        
        quality = result['quality']
        
        # Interpretación de calidad
        if quality >= 90:
            quality_desc = "Excelente"
        elif quality >= 80:
            quality_desc = "Buena"
        elif quality >= 70:
            quality_desc = "Moderada"
        else:
            quality_desc = "Baja"
        
        return f"Calidad: {quality}% ({quality_desc})"
    
    def get_dependencies_status(self) -> Dict:
        """Obtiene el estado del servicio web."""
        try:
            # Hacer una llamada de prueba al servicio
            response = requests.get(self.endpoint.replace('/analyze/quality', '/health'), timeout=5)
            service_available = response.status_code == 200
        except:
            service_available = False
        
        return {
            'web_service': service_available,
            'service_url': self.endpoint,
            'recommended_install': 'Servicio web activo' if service_available else 'Verificar conexión a internet'
        }
