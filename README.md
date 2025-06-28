<div align="center">

# 🔍 Passive Liveness CLI

Una herramienta de línea de comandos para evaluar imágenes con servicios de liveness, utilizando tanto APIs SaaS como SDKs locales.

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/geo-mena/liveness-cli)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.7%2B-blue)](https://python.org)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey)](https://github.com/geo-mena/liveness-cli)

</div>

## 📋 Tabla de Contenidos
- [✨ Características](#-características)
- [📦 Instalación](#-instalación)
- [⚡ Uso](#-uso)
- [🌄 Análisis de Calidad JPEG](#-análisis-de-calidad-jpeg)
- [⚙️ Opciones](#️-opciones)
- [🏗️ Estructura del Código](#️-estructura-del-código)
- [📄 Formato del Informe](#-formato-del-informe)
- [📋 Requisitos](#-requisitos)
- [📸 Ejemplos](#-ejemplos)
- [🛠️ Solución de Problemas](#️-solución-de-problemas)

## ✨ Características

- Evaluación de imágenes individuales o directorios completos
- Integración con servicios SaaS (Identity Platform) y SDK local
- Opcional **Análisis de calidad JPEG**
- Soporte para múltiples versiones del SDK (hasta 3)
- Generación de informes en formato Markdown
- Interfaz interactiva y modo de línea de comandos
- Procesamiento paralelo para mayor velocidad

## 📦 Instalación

1. Clona este repositorio:
   ```bash
   git clone https://github.com/geo-mena/liveness-cli.git
   cd liveness-cli
   ```

2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## ⚡ Uso

### Modo Interactivo

La forma más fácil de usar el CLI es en modo interactivo:

```bash
python liveness_cli.py --interactive
```

Esto iniciará un asistente que te guiará a través de todas las opciones.

### Modo Línea de Comandos

También puedes usar el CLI directamente desde la línea de comandos:

```bash
# Evaluar una imagen individual con el servicio SaaS
python liveness_cli.py --image ruta/a/imagen.jpg --use-saas --output informe.md

# Evaluar un directorio de imágenes con análisis de calidad JPEG
python liveness_cli.py --directory ruta/a/imagenes --use-saas --analyze-jpeg-quality --output informe.md

# Evaluar un directorio de imágenes con el servicio SDK en el puerto 8080
python liveness_cli.py --directory ruta/a/imagenes --use-sdk --sdk-port 8080 --sdk-version "6.12" --output informe.md

# Evaluar con SaaS, SDK y análisis JPEG
python liveness_cli.py --directory ruta/a/imagenes --use-saas --use-sdk --sdk-port 8080 9090 --sdk-version "6.12" "6.5" --analyze-jpeg-quality --output informe.md
```

## 🌄 Análisis de Calidad JPEG

El CLI incluye funcionalidad avanzada para analizar la calidad de compresión de imágenes JPEG:

- **Análisis preciso**: Determina el porcentaje de calidad de compresión JPEG
- **Solo imágenes JPEG**: La funcionalidad está diseñada específicamente para archivos JPEG
- **Resultados numéricos**: Muestra el porcentaje de calidad (ej: 85%)
- **Detección de errores**: Maneja casos de imágenes corruptas o no válidas

### Uso del Análisis JPEG

```bash
# Activar análisis JPEG en modo interactivo
python liveness_cli.py --interactive

# Responder "y" cuando pregunte por análisis JPEG
```

## ⚙️ Opciones

### Configuración de Imágenes
- `--image`, `-img`: Ruta a una imagen individual para evaluar
- `--directory`, `-dir`: Directorio que contiene imágenes para evaluar

### Configuración de SaaS
- `--use-saas`: Usar el servicio SaaS para la evaluación
- `--saas-api-key`: API key para el servicio SaaS

### Configuración de SDK
- `--use-sdk`: Usar el servicio SDK local para la evaluación
- `--sdk-port`: Puerto(s) donde se ejecuta el servicio SDK local (máximo 3)
- `--sdk-version`: Versión(es) del SDK correspondiente a cada puerto

### Configuración del Informe
- `--output`, `-o`: Ruta donde guardar el informe generado

### Otras Opciones
- `--workers`, `-w`: Número de workers para procesamiento paralelo
- `--verbose`, `-v`: Mostrar información detallada durante la ejecución
- `--analyze-jpeg-quality`: Analizar la calidad JPEG de las imágenes
- `--interactive`, `-i`: Ejecutar en modo interactivo

## 🏗️ Estructura del Código

El código está organizado con una arquitectura modular escalable:

```shell
liveness-cli/
├── README.md                  # Documentación del proyecto
├── __init__.py                # Inicialización del paquete
├── liveness_cli.py            # Punto de entrada principal
├── requirements.txt           # Dependencias del proyecto
├── setup.py                   # Script de instalación
└── src/                       # Paquete principal del proyecto
    ├── __init__.py
    ├── cli.py                 # Coordinador principal del CLI
    ├── commands/              # Comandos CLI modulares
    │   ├── __init__.py
    │   ├── evaluate.py        # Comando de evaluación
    │   └── interactive.py     # Comando modo interactivo
    ├── core/                  # Lógica de negocio central
    │   ├── __init__.py
    │   ├── image_processor.py # Procesamiento de imágenes
    │   ├── jpeg_quality_analyzer.py # Análisis de calidad JPEG
    │   └── report_generator.py# Generación de reportes
    └── utils/                 # Utilidades y herramientas auxiliares
        ├── __init__.py
        ├── config.py          # Configuraciones del sistema
        └── helpers.py         # Funciones utilitarias compartidas
```

### Arquitectura

- **`src/commands/`**: Comandos CLI separados por responsabilidad
- **`src/core/`**: Lógica de negocio (procesamiento, reportes, análisis JPEG)
- **`src/utils/`**: Utilidades compartidas (configuración, helpers)
- **`backup/`**: Versión original completa para referencia

Esta estructura modular sigue los principios de Clean Code, separando las responsabilidades en diferentes componentes y facilitando el mantenimiento y escalabilidad futura.

## 📄 Formato del Informe

El informe generado es un archivo Markdown con una tabla que incluye:

- Título de la imagen
- Imagen (miniatura)
- Resolución
- Tamaño
- **Calidad JPEG** (si se habilitó el análisis)
- Diagnóstico SaaS (si se habilitó)
- Diagnóstico SDK para cada versión (si se habilitó)

## 📋 Requisitos

- Python 3.7 o superior
- Dependencias listadas en `requirements.txt`
- Para la evaluación con SDK: servicio SDK funcionando en los puertos especificados
- Para la evaluación con SaaS: conexión a Internet y API key válida

## 📸 Ejemplos

### Evaluación Básica
```bash
python liveness_cli.py -i
```

### Evaluación con Análisis JPEG
```bash
python liveness_cli.py --directory ./imagenes_test --use-saas --analyze-jpeg-quality --output ./informes/informe_jpeg.md
```

### Evaluación Avanzada
```bash
python liveness_cli.py --directory ./imagenes_test --use-saas --use-sdk --sdk-port 8080 9090 --sdk-version "6.12" "6.5" --analyze-jpeg-quality --output ./informes/informe_$(date +%Y%m%d).md --workers 10 --verbose
```

## 🛠️ Solución de Problemas

- **Error de conexión al SDK**: Asegúrate de que el servicio SDK esté ejecutándose en el puerto especificado.
- **Error en la API SaaS**: Verifica que la API key sea válida y tengas conexión a Internet.
- **Imágenes no encontradas**: Verifica las rutas proporcionadas para las imágenes o el directorio.
- **Error en análisis JPEG**: Si el análisis JPEG falla, aparecerá "Error: [mensaje]" en la columna correspondiente del informe.
- **"No es JPEG"**: El análisis de calidad solo funciona con archivos JPEG. Otros formatos mostrarán este mensaje.
