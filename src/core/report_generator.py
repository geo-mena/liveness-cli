#!/usr/bin/env python3
"""
🌱 Módulo para generar informes de evaluación de liveness en formato Markdown.
"""

import os
from typing import List, Dict
from src.utils.helpers import ensure_directory_exists

class MarkdownReportGenerator:
    """Clase para generar informes en formato Markdown."""
    
    def __init__(self, output_path: str, image_dir: str):
        self.output_path = output_path
        self.image_dir = image_dir

        # Dimensiones estándar para las imágenes
        self.image_width = 120
        self.image_height = 160
        
    def generate_report(self, results: List[Dict]) -> str:
        """Genera un informe en formato Markdown con los resultados de la evaluación."""
        
        # Crear directorio de salida si no existe
        ensure_directory_exists(self.output_path)
        
        # Determinar columnas basadas en el primer resultado que debería tener todas las columnas
        if not results:
            return ""
        
        # Crear encabezado de la tabla
        header = "| Title | "
        header_separator = "| ----- | "
        
        # Añadir columnas fijas
        fixed_columns = ["Photo", "Resolution", "Size"]
        header += " | ".join(fixed_columns) + " | "
        header_separator += " | ".join(["-" * len(col) for col in fixed_columns]) + " | "
        
        # Añadir columnas de análisis JPEG si están presentes
        jpeg_columns = []
        if "Calidad JPEG" in results[0]:
            jpeg_columns.append("Calidad JPEG")
        
        if jpeg_columns:
            header += " | ".join(jpeg_columns) + " | "
            header_separator += " | ".join(["-" * len(col) for col in jpeg_columns]) + " | "
        
        # Añadir columnas dinámicas (SaaS y SDK versiones)
        diagnostic_columns = [col for col in results[0].keys() if col.startswith("Diagnostic")]
        if diagnostic_columns:
            header += " | ".join(diagnostic_columns) + " |"
            header_separator += " | ".join(["-" * len(col) for col in diagnostic_columns]) + " |"
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
            row += f"<img src=\"{result['ImagePath']}\" width=\"{self.image_width}\" height=\"{self.image_height}\" alt=\"Photo\"> | {result['Resolución']} | {result['Tamaño']} | "
            
            # Añadir columnas de análisis JPEG
            if jpeg_columns:
                row += " | ".join([result.get(col, "N/A") for col in jpeg_columns]) + " | "
            
            # Añadir columnas dinámicas
            if diagnostic_columns:
                row += " | ".join([result.get(col, "N/A") for col in diagnostic_columns]) + " |"
            else:
                # Eliminar el último " | " si no hay columnas dinámicas
                row = row[:-3] + " |"
            
            report_content += f"{row}\n"
        
        # Guardar informe
        with open(self.output_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        
        return report_content
