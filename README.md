# Desaprobados por la sociedad

Generador estático para un diario independiente con estética de portal web de 2002.

## Requisitos

- Python 3.10 o posterior
- Dependencias de `requirements.txt`

## Primeros pasos

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
python scripts/build.py
python -m http.server 8000 -d dist
```

Abrí http://localhost:8000 para revisar la portada.

## Analítica de visitas

En `static/js/config.js`, pegá el token del fragmento de **Cloudflare Web
Analytics** en `CLOUDFLARE_WEB_ANALYTICS_TOKEN`. El generador copia este archivo
al sitio y agrega el beacon en todas las páginas; después, regenerá y publicá
el sitio. Los datos se consultan en el panel de Web Analytics de Cloudflare;
este servicio no muestra un contador público de visitas dentro de la página.

## Escribir una nota

Duplicá `content/plantilla.md` dentro de una carpeta de sección, por ejemplo `content/musica/mi-nota.md`.

El encabezado usa YAML entre `---`:

```yaml
---
title: "Título de la nota"
subtitle: "Una bajada breve"
author: "Nombre del autor"
date: "2026-10-17"
category: "Música"
featured: false
image: ""
image_alt: ""
tags:
  - rock
  - Morón
---
```

Después del segundo `---`, escribí el cuerpo en Markdown.

## Nube de temas

La nube muestra las etiquetas declaradas en `tags` y los términos de las listas
positivas definidas en `scripts/build.py` que aparecen en el título, la bajada o
el cuerpo de al menos una nota. Los términos ausentes no generan enlaces ni
páginas HTML. Las listas están organizadas por conjuntos (política, fútbol,
países y economía) y pueden ampliarse al editar el generador.

## Publicación

El sitio generado queda en `dist/`. Configurá GitHub Pages para publicar ese directorio, por ejemplo mediante GitHub Actions. El comando de abajo prepara las rutas para el repositorio; no cambia el directorio de salida.

Para generar el sitio para el repositorio [elpibe12345677/DesaprobadosMedia](https://github.com/elpibe12345677/DesaprobadosMedia), publicado en `https://elpibe12345677.github.io/DesaprobadosMedia/`, ejecutá:

```bash
python scripts/build.py --pages
```

`--pages` configura la raíz del sitio como `/DesaprobadosMedia/`. Para otros repositorios de proyecto, usá `--base-url /nombre-del-repositorio/`; en un sitio publicado desde la raíz del dominio no hace falta ninguno de los dos.

## Seguridad editorial

El generador desactiva el HTML crudo de Markdown. Las notas se consideran contenido editorial y deben revisarse antes de publicarse. Las imágenes deben guardarse dentro de `assets/images/`.

## Comandos

```bash
python scripts/build.py
python scripts/build.py --pages
python scripts/build.py --base-url /nombre-del-repositorio/
python scripts/build.py --check
```

`--check` valida los archivos Markdown sin generar el sitio.
