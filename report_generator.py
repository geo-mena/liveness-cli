#!/usr/bin/env python3
"""
Módulo para generar informes de evaluación de liveness en formato Markdown.
"""

import os
from typing import List, Dict

class MarkdownReportGenerator:
    """Clase para generar informes en formato Markdown."""
    
    def __init__(self, output_path: str, image_dir: str):
        self.output_path = output_path
        self.image_dir = image_dir
        
    def generate_report(self, results: List[Dict]) -> str:
        """Genera un informe en formato Markdown con los resultados de la evaluación."""
        
        # Crear directorio de salida si no existe
        os.makedirs(os.path.dirname(os.path.abspath(self.output_path)), exist_ok=True)
        
        # Determinar columnas basadas en el primer resultado que debería tener todas las columnas
        if not results:
            return ""
        
        # Crear encabezado de la tabla
        header = "| Title | "
        header_separator = "| ----- | "
        
        # Añadir columnas fijas
        fixed_columns = ["Foto", "Resolución", "Tamaño"]
        header += " | ".join(fixed_columns) + " | "
        header_separator += " | ".join(["-" * len(col) for col in fixed_columns]) + " | "
        
        # Añadir columnas dinámicas (SaaS y SDK versiones)
        dynamic_columns = [col for col in results[0].keys() if col.startswith("Diagnostic")]
        if dynamic_columns:
            header += " | ".join(dynamic_columns) + " |"
            header_separator += " | ".join(["-" * len(col) for col in dynamic_columns]) + " |"
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
            row += f"![Foto]({result['ImagePath']}) | {result['Resolución']} | {result['Tamaño']} | "
            
            # Añadir columnas dinámicas
            if dynamic_columns:
                row += " | ".join([result[col] for col in dynamic_columns]) + " |"
            else:
                # Eliminar el último " | " si no hay columnas dinámicas
                row = row[:-3] + " |"
            
            report_content += f"{row}\n"
        
        # Guardar informe
        with open(self.output_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        
        return report_content