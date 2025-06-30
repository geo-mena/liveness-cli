#!/usr/bin/env python3
"""
🌱 Módulo para generar informes de evaluación de liveness en formato Markdown.
"""

import os
from typing import List, Dict
from src.utils.helpers import ensure_directory_exists, create_report_path_with_date

class MarkdownReportGenerator:
    """Clase para generar informes en formato Markdown."""
    
    def __init__(self, output_path: str, image_dir: str):
        # Crear ruta con subdirectorio de fecha y manejo de duplicados
        self.output_path, self.dated_directory = create_report_path_with_date(output_path)
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
        
        # Crear encabezado HTML de la tabla
        header_columns = ["Title", "Photo", "Resolution", "Size"]
        
        # Añadir columnas de análisis JPEG si están presentes
        jpeg_columns = []
        if "Calidad JPEG" in results[0]:
            jpeg_columns.append("Calidad JPEG")
            header_columns.extend(jpeg_columns)
        
        # Añadir columnas dinámicas (SaaS y SDK versiones)
        diagnostic_columns = [col for col in results[0].keys() if col.startswith("Diagnostic")]
        if diagnostic_columns:
            header_columns.extend(diagnostic_columns)
        
        # Iniciar contenido del informe con tabla HTML y estilos CSS
        report_content = """<style>
table {
    border-collapse: collapse;
    width: 100%;
    margin: 20px 0;
    table-layout: fixed;
}
table, th, td {
    border: 1px solid #ddd;
}
th, td {
    padding: 8px;
    text-align: center;
    vertical-align: middle;
}
th {
    font-weight: bold;
}
/* Columnas con ancho fijo */
th:nth-child(1), td:nth-child(1) { /* Title */
    width: 120px;
    word-wrap: break-word;
}
th:nth-child(2), td:nth-child(2) { /* Photo */
    width: 120px;
}
/* Columnas responsivas */
th:nth-child(n+3), td:nth-child(n+3) {
    width: auto;
    min-width: 80px;
}
/* Estilos para imágenes */
img {
    max-width: 100%;
    height: auto;
    max-height: 160px;
    object-fit: contain;
}
</style>

<table>
<thead>
<tr>
"""
        for col in header_columns:
            report_content += f"<th>{col}</th>"
        report_content += "</tr>\n</thead>\n<tbody>\n"
        
        # Añadir filas
        for result in results:
            report_content += "<tr>"
            
            # Columna Title
            report_content += f"<td>{result['Title']}</td>"
            
            # Columna Photo
            report_content += f"<td><img src=\"{result['ImagePath']}\" alt=\"Photo\"></td>"
            
            # Columnas fijas
            report_content += f"<td>{result['Resolución']}</td>"
            report_content += f"<td>{result['Tamaño']}</td>"
            
            # Columnas de análisis JPEG
            for col in jpeg_columns:
                report_content += f"<td>{result.get(col, 'N/A')}</td>"
            
            # Columnas dinámicas
            for col in diagnostic_columns:
                report_content += f"<td>{result.get(col, 'N/A')}</td>"
            
            report_content += "</tr>\n"
        
        # Cerrar tabla HTML
        report_content += "</tbody>\n</table>"
        
        # Guardar informe
        with open(self.output_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        
        return report_content
