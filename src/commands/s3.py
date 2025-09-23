#!/usr/bin/env python3

import boto3
import os
import sys
import json
import inquirer
from datetime import datetime
from pathlib import Path
from inquirer.themes import GreenPassion
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.align import Align

class CustomTheme(GreenPassion):
    def __init__(self):
        super(CustomTheme, self).__init__()
        self.Question.mark_color = '\x1b[38;2;217;120;87m'
        self.Question.brackets_color = '\x1b[38;2;217;120;87m'
        self.List.selection_color = '\x1b[38;2;217;120;87m'
        self.List.selection_cursor = '❯'

class S3Command:
    def __init__(self):
        self.console = Console()
        self.theme = CustomTheme()
        self.profile_name = "SaaS-Support"
        self.bucket_name = "sa-east-1.c3po.identity-api.logs"
        self.session = None
        self.s3_client = None

    def connect_to_aws(self):
        """Inicializar conexión con AWS SSO"""
        try:
            self.session = boto3.Session(profile_name=self.profile_name)
            self.s3_client = self.session.client('s3')
            self.console.print(f"[bold green]Conectado a AWS con perfil: {self.profile_name}[/bold green]")
            return True
        except Exception as e:
            self.console.print(f"[bold red]Error conectando a AWS: {e}[/bold red]")
            self.console.print("[yellow]Asegúrate de ejecutar: aws sso login --profile SaaS-Support[/yellow]")
            return False

    def build_s3_path(self, client, tenant, year, month, day, resource, json_file=None):
        """Construye la ruta S3 basada en los parámetros"""
        base_path = f"client={client}/tenant={tenant}/year={year}/month={month:02d}/day={day:02d}/resource={resource}/"

        if json_file:
            return base_path + json_file
        return base_path

    def list_files(self, s3_path):
        """Lista archivos en la ruta S3"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=s3_path
            )

            if 'Contents' not in response:
                self.console.print(f"[yellow]No se encontraron archivos en: s3://{self.bucket_name}/{s3_path}[/yellow]")
                return []

            files = [obj['Key'] for obj in response['Contents'] if obj['Key'].endswith('.json')]
            return files

        except Exception as e:
            self.console.print(f"[bold red]Error listando archivos: {e}[/bold red]")
            return []

    def list_resources(self, client, tenant, year, month, day):
        """Lista resources disponibles para una fecha específica"""
        base_path = f"client={client}/tenant={tenant}/year={year}/month={month:02d}/day={day:02d}/"

        try:
            self.console.print(f"[cyan]Buscando resources en: s3://{self.bucket_name}/{base_path}[/cyan]")

            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=base_path,
                Delimiter='/'
            )

            resources = []
            if 'CommonPrefixes' in response:
                for prefix in response['CommonPrefixes']:
                    resource_path = prefix['Prefix']
                    if 'resource=' in resource_path:
                        resource_name = resource_path.split('resource=')[1].rstrip('/')
                        if resource_name:
                            resources.append(resource_name)

            return sorted(list(set(resources)))

        except Exception as e:
            self.console.print(f"[bold red]Error listando resources: {e}[/bold red]")
            return []

    def download_file(self, s3_key, local_path):
        """Descarga un archivo individual"""
        try:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            self.s3_client.download_file(self.bucket_name, s3_key, local_path)
            return True
        except Exception as e:
            self.console.print(f"[bold red]Error descargando {s3_key}: {e}[/bold red]")
            return False

    def search_files(self, client, tenant, year, month, day, resource, json_file=None, save_results=True):
        """Función para buscar archivos sin descargarlos"""

        s3_path = self.build_s3_path(client, tenant, year, month, day, resource)

        self.console.print(f"[cyan]Buscando en: s3://{self.bucket_name}/{s3_path}[/cyan]")

        if json_file:
            full_path = s3_path + json_file
            self.console.print(f"[cyan]Buscando archivo específico: {json_file}[/cyan]")

            try:
                response = self.s3_client.head_object(Bucket=self.bucket_name, Key=full_path)

                file_info = {
                    "found": True,
                    "file": json_file,
                    "path": full_path,
                    "size": response['ContentLength'],
                    "last_modified": response['LastModified'].isoformat(),
                    "search_params": {
                        "client": client,
                        "tenant": tenant,
                        "year": year,
                        "month": month,
                        "day": day,
                        "resource": resource
                    }
                }

                self.console.print("[bold green]Archivo encontrado:[/bold green]")
                self.console.print(f"   [white]Ruta: {full_path}[/white]")
                self.console.print(f"   [white]Tamaño: {response['ContentLength']} bytes[/white]")
                self.console.print(f"   [white]Última modificación: {response['LastModified']}[/white]")

                if save_results:
                    self.save_search_results([file_info], f"search_{json_file.replace('.json', '')}")

                return [file_info]

            except self.s3_client.exceptions.NoSuchKey:
                self.console.print(f"[bold red]Archivo no encontrado: {json_file}[/bold red]")
                file_info = {
                    "found": False,
                    "file": json_file,
                    "path": full_path,
                    "error": "File not found"
                }
                return [file_info]
        else:
            files = self.list_files(s3_path)

            if not files:
                self.console.print("[bold red]No se encontraron archivos JSON en esta ubicación[/bold red]")
                return []

            self.console.print(f"[bold green]Encontrados {len(files)} archivos JSON:[/bold green]")

            files_info = []
            for i, file_key in enumerate(files, 1):
                filename = os.path.basename(file_key)

                try:
                    response = self.s3_client.head_object(Bucket=self.bucket_name, Key=file_key)

                    file_info = {
                        "found": True,
                        "file": filename,
                        "path": file_key,
                        "size": response['ContentLength'],
                        "last_modified": response['LastModified'].isoformat()
                    }

                    files_info.append(file_info)
                    self.console.print(f"   [white]{i:2d}. {filename} ({response['ContentLength']} bytes)[/white]")

                except Exception as e:
                    self.console.print(f"   [red]{i:2d}. {filename} (Error obteniendo info: {e})[/red]")

            if save_results:
                search_results = {
                    "search_timestamp": datetime.now().isoformat(),
                    "search_params": {
                        "client": client,
                        "tenant": tenant,
                        "year": year,
                        "month": month,
                        "day": day,
                        "resource": resource
                    },
                    "total_files": len(files_info),
                    "files": files_info
                }
                self.save_search_results(search_results, "search_listing")

            return files_info

    def save_search_results(self, results, filename_prefix="search"):
        """Guarda los resultados de búsqueda en un archivo JSON"""
        try:
            search_dir = "searches"
            os.makedirs(search_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{search_dir}/{filename_prefix}_{timestamp}.json"

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)

            self.console.print(f"[bold green]Resultados guardados en: {filename}[/bold green]")
            return filename

        except Exception as e:
            self.console.print(f"[yellow]Error guardando resultados: {e}[/yellow]")
            return None

    def download_files(self, client, tenant, year, month, day, resource, json_file=None):
        """Función principal para descargar archivos"""

        s3_path = self.build_s3_path(client, tenant, year, month, day, resource, json_file)

        local_dir = f"downloads/{client}/{resource}/{year}-{month:02d}-{day:02d}"

        if json_file:
            self.console.print(f"[cyan]Descargando archivo específico: {json_file}[/cyan]")
            local_file_path = f"{local_dir}/{json_file}"

            if self.download_file(s3_path, local_file_path):
                self.console.print(f"[bold green]Descargado: {local_file_path}[/bold green]")
                return [local_file_path]
            else:
                return []
        else:
            self.console.print(f"[cyan]Buscando archivos en: s3://{self.bucket_name}/{s3_path}[/cyan]")
            files = self.list_files(s3_path)

            if not files:
                return []

            self.console.print(f"[cyan]Encontrados {len(files)} archivos JSON[/cyan]")
            downloaded_files = []

            for file_key in files:
                filename = os.path.basename(file_key)
                local_file_path = f"{local_dir}/{filename}"

                if self.download_file(file_key, local_file_path):
                    self.console.print(f"[green]Descargado: {filename}[/green]")
                    downloaded_files.append(local_file_path)
                else:
                    self.console.print(f"[red]Error descargando: {filename}[/red]")

            return downloaded_files

    def get_mode_selection(self):
        """Selecciona el modo de operación"""
        mode_questions = [
            inquirer.List(
                'mode',
                message='Selecciona el modo de operación:',
                choices=[
                    ('SEARCH - Buscar archivos (sin descargar)', 'search'),
                    ('DOWNLOAD - Descargar archivos', 'download'),
                ],
            ),
        ]
        return inquirer.prompt(mode_questions, theme=self.theme)

    def get_basic_params(self):
        """Obtiene parámetros básicos del usuario"""
        current_year = datetime.now().year
        current_month = datetime.now().month
        current_day = datetime.now().day

        basic_questions = [
            inquirer.Text(
                'client',
                message='Client ID:',
                validate=lambda _, x: len(x.strip()) > 0 or 'Client ID es requerido',
            ),
            inquirer.Text(
                'tenant',
                message='Tenant ID:',
                validate=lambda _, x: len(x.strip()) > 0 or 'Tenant ID es requerido',
            ),
            inquirer.Text(
                'year',
                message=f'Año [{current_year}]:',
                default=str(current_year),
                validate=lambda _, x: x.isdigit() and 2020 <= int(x) <= 2030 or 'Año inválido (2020-2030)',
            ),
            inquirer.Text(
                'month',
                message=f'Mes (1-12) [{current_month}]:',
                default=str(current_month),
                validate=lambda _, x: x.isdigit() and 1 <= int(x) <= 12 or 'Mes inválido (1-12)',
            ),
            inquirer.Text(
                'day',
                message=f'Día (1-31) [{current_day}]:',
                default=str(current_day),
                validate=lambda _, x: x.isdigit() and 1 <= int(x) <= 31 or 'Día inválido (1-31)',
            ),
        ]
        return inquirer.prompt(basic_questions, theme=self.theme)

    def get_resource_selection(self, client, tenant, year, month, day):
        """Selecciona el resource"""
        self.console.print(f"[cyan]Buscando resources disponibles para {day:02d}/{month:02d}/{year}...[/cyan]")

        available_resources = self.list_resources(client, tenant, year, month, day)

        if not available_resources:
            self.console.print("[yellow]No se encontraron resources para esta fecha[/yellow]")
            self.console.print("[yellow]Prueba con otra fecha o verifica los parámetros[/yellow]")

            manual_questions = [
                inquirer.Confirm(
                    'manual',
                    message='¿Quieres escribir el resource manualmente?',
                    default=False,
                ),
            ]
            manual_answer = inquirer.prompt(manual_questions, theme=self.theme)

            if not manual_answer or not manual_answer['manual']:
                return None

            resource_questions = [
                inquirer.Text(
                    'resource',
                    message='Resource:',
                    validate=lambda _, x: len(x.strip()) > 0 or 'Resource es requerido',
                ),
            ]
            return inquirer.prompt(resource_questions, theme=self.theme)
        else:
            self.console.print(f"[green]Resources disponibles ({len(available_resources)}):[/green]")
            for i, res in enumerate(available_resources, 1):
                self.console.print(f"   [white]{i:2d}. {res}[/white]")

            choices = [(res, res) for res in available_resources]
            choices.append(('Escribir manualmente', 'manual'))

            resource_questions = [
                inquirer.List(
                    'resource',
                    message='Selecciona resource:',
                    choices=choices,
                ),
            ]

            resource_answer = inquirer.prompt(resource_questions, theme=self.theme)

            if not resource_answer:
                return None

            if resource_answer['resource'] == 'manual':
                manual_questions = [
                    inquirer.Text(
                        'resource',
                        message='Escribe el resource:',
                        validate=lambda _, x: len(x.strip()) > 0 or 'Resource es requerido',
                    ),
                ]
                return inquirer.prompt(manual_questions, theme=self.theme)

            return resource_answer

    def get_search_options(self):
        """Obtiene opciones específicas para búsqueda"""
        search_questions = [
            inquirer.List(
                'search_type',
                message='Opciones de búsqueda:',
                choices=[
                    ('Buscar archivo específico', 'specific'),
                    ('Listar todos los archivos del directorio', 'list'),
                ],
            ),
        ]

        search_answer = inquirer.prompt(search_questions, theme=self.theme)

        if not search_answer:
            return None

        if search_answer['search_type'] == 'specific':
            file_questions = [
                inquirer.Text(
                    'json_file',
                    message='Nombre del archivo JSON a buscar:',
                    validate=lambda _, x: len(x.strip()) > 0 or 'Nombre de archivo es requerido',
                ),
            ]
            file_answer = inquirer.prompt(file_questions, theme=self.theme)

            if file_answer and file_answer['json_file']:
                json_file = file_answer['json_file']
                if not json_file.endswith('.json'):
                    json_file += '.json'
                return {'json_file': json_file}

        return {'json_file': None}

    def get_download_options(self):
        """Obtiene opciones específicas para descarga"""
        download_questions = [
            inquirer.Text(
                'json_file',
                message='Archivo JSON específico (opcional, ej: 75c8d8b2-fbf9-4ca0-976f-130652a113a2.json):',
                default='',
            ),
        ]

        download_answer = inquirer.prompt(download_questions, theme=self.theme)

        if not download_answer:
            return None

        json_file = download_answer['json_file'].strip()
        if json_file and not json_file.endswith('.json'):
            json_file += '.json'

        return {'json_file': json_file if json_file else None}

    def run_s3_flow(self):
        """Ejecuta el flujo completo de S3"""

        if not self.connect_to_aws():
            return False

        mode_answer = self.get_mode_selection()
        if not mode_answer:
            return False

        mode = mode_answer['mode']
        self.console.print(f"[bold cyan]Modo seleccionado: {mode.upper()}[/bold cyan]")

        basic_params = self.get_basic_params()
        if not basic_params:
            return False

        client = basic_params['client']
        tenant = basic_params['tenant']
        year = int(basic_params['year'])
        month = int(basic_params['month'])
        day = int(basic_params['day'])

        resource_answer = self.get_resource_selection(client, tenant, year, month, day)
        if not resource_answer:
            return False

        resource = resource_answer['resource']
        self.console.print(f"[green]Resource seleccionado: {resource}[/green]")

        if mode == 'search':
            options = self.get_search_options()
        else:
            options = self.get_download_options()

        if not options:
            return False

        json_file = options.get('json_file')

        if mode == 'search':
            self.console.print("[cyan]Iniciando búsqueda...[/cyan]")
            search_results = self.search_files(
                client=client,
                tenant=tenant,
                year=year,
                month=month,
                day=day,
                resource=resource,
                json_file=json_file
            )

            self.console.print("\n" + "=" * 50)
            if search_results:
                found_files = [r for r in search_results if r.get('found', False)]
                self.console.print(f"[bold green]Búsqueda completada! {len(found_files)} archivos encontrados[/bold green]")

                if json_file:
                    if found_files:
                        self.console.print("[green]Archivo encontrado y disponible para descarga[/green]")
                    else:
                        self.console.print("[red]Archivo no encontrado[/red]")
                else:
                    self.console.print("[green]Resultados guardados en archivo JSON en carpeta 'searches/'[/green]")
            else:
                self.console.print("[red]No se encontraron archivos[/red]")
        else:
            self.console.print("[cyan]Iniciando descarga...[/cyan]")
            downloaded_files = self.download_files(
                client=client,
                tenant=tenant,
                year=year,
                month=month,
                day=day,
                resource=resource,
                json_file=json_file
            )

            self.console.print("\n" + "=" * 50)
            if downloaded_files:
                self.console.print(f"[bold green]Descarga completada! {len(downloaded_files)} archivos descargados[/bold green]")
                self.console.print("[green]Archivos descargados:[/green]")
                for file_path in downloaded_files:
                    self.console.print(f"   [white]• {file_path}[/white]")
            else:
                self.console.print("[red]No se descargaron archivos[/red]")

        return True