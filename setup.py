#!/usr/bin/env python3
"""
Script de instalación para el CLI de evaluación de liveness.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="liveness-cli",
    version="1.1.0",
    author="Equipo de Facephi",
    author_email="geovannymena@facephi.com",
    description="CLI para evaluar imágenes con servicios de liveness",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/geo-mena/liveness-cli",
    packages=find_packages(),
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "liveness-cli=src.cli:main",
        ],
    },
)
