#!/usr/bin/env python3
"""Build estático de Desaprobados a partir de Markdown + Jinja2."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import unicodedata
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any

import mistune
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

ROOT = Path(__file__).resolve().parents[1]
print(f"Directorio raíz: {ROOT}")
CONTENT_DIR = ROOT / "content"
TEMPLATES_DIR = ROOT / "templates"
ASSETS_DIR = ROOT / "assets"
STATIC_DIR = ROOT / "static"
OUTPUT_DIR = ROOT / "dist"

ALLOWED_CATEGORIES = {
    "Política": "politica",
    "Fútbol": "futbol",
    "Música": "musica",
    "Cultura": "cultura",
    "Historia": "historia",
    "Entrevistas": "entrevistas",
    "Sociedad": "sociedad",
    "Internacional": "internacional",
    "Editorial": "editorial",
    "Economía": "economia",
}
REQUIRED_FIELDS = ("title", "subtitle", "author", "date", "category")
ARGENTINE_POLITICIANS = {
    "Myriam Bregman", "Mauricio Macri", "Javier Milei", "Cristina Fernández de Kirchner",
    "Néstor Kirchner", "Alberto Fernández", "Sergio Massa", "Patricia Bullrich",
    "Axel Kicillof", "Victoria Villarruel", "Horacio Rodríguez Larreta", "Juan Grabois",
    "Juan Domingo Perón", "Eva Perón", "Raúl Alfonsín", "Arturo Illia",
}
INTERNATIONAL_POLITICIANS = {
    "Donald Trump", "Joe Biden", "Barack Obama", "Kamala Harris", "Lula da Silva",
    "Jair Bolsonaro", "Gabriel Boric", "Michelle Bachelet", "Gustavo Petro",
    "Claudia Sheinbaum", "Andrés Manuel López Obrador", "Nicolás Maduro",
    "Hugo Chávez", "Yamandú Orsi", "Pedro Sánchez", "Emmanuel Macron",
    "Vladimir Putin", "Volodímir Zelenski", "Xi Jinping", "Narendra Modi",
    "Benjamin Netanyahu", "Recep Tayyip Erdoğan",
}
FOOTBALL_PLAYERS = {
    "Lionel Messi", "Diego Maradona", "Ángel Di María", "Emiliano Martínez",
    "Julián Álvarez", "Lautaro Martínez", "Enzo Fernández", "Rodrigo De Paul",
    "Cristiano Ronaldo", "Neymar", "Kylian Mbappé", "Erling Haaland",
    "Vinícius Júnior", "Jude Bellingham", "Luka Modrić", "Mohamed Salah",
    "Robert Lewandowski", "Pelé", "Marta",
}
ARGENTINE_FOOTBALL_CLUBS = {
    "Boca Juniors", "River Plate", "Independiente", "Racing Club", "San Lorenzo",
    "Huracán", "Vélez Sarsfield", "Estudiantes de La Plata", "Gimnasia y Esgrima La Plata",
    "Rosario Central", "Newell's Old Boys", "Talleres de Córdoba", "Belgrano",
    "Instituto", "Lanús", "Banfield", "Argentinos Juniors", "Defensa y Justicia",
    "Godoy Cruz", "Platense", "Sarmiento de Junín", "Quilmes", "Chacarita Juniors",
    "Ferro Carril Oeste", "San Martín de Tucumán", "Gimnasia y Tiro",
    "Deportivo Morón", "Almirante Brown", "Atlanta", "Temperley",
}
BRAZILIAN_FOOTBALL_CLUBS = {
    "Flamengo", "Palmeiras", "Corinthians", "São Paulo", "Santos", "Grêmio",
    "Internacional", "Atlético Mineiro", "Cruzeiro", "Botafogo", "Fluminense",
    "Vasco da Gama", "Bahia", "Fortaleza", "Athletico Paranaense",
}
SPANISH_FOOTBALL_CLUBS = {
    "Real Madrid", "Barcelona", "Atlético de Madrid", "Athletic Club", "Sevilla",
    "Valencia", "Real Betis", "Real Sociedad", "Villarreal", "Girona",
}
ITALIAN_FOOTBALL_CLUBS = {
    "Juventus", "Inter de Milán", "AC Milan", "Roma", "Napoli", "Lazio",
    "Atalanta", "Fiorentina", "Bologna",
}
GERMAN_FOOTBALL_CLUBS = {
    "Bayern Múnich", "Borussia Dortmund", "Bayer Leverkusen", "RB Leipzig",
    "Eintracht Frankfurt", "Werder Bremen", "Stuttgart", "Schalke 04",
}
POLITICAL_TERMS = {
    "política", "Estado", "Estado de bienestar", "democracia", "gobierno",
    "Congreso", "Senado", "Cámara de Diputados", "elecciones", "sindicato",
    "derechos humanos", "justicia social",
}
COUNTRIES = {
    "Afganistán", "Albania", "Alemania", "Andorra", "Angola", "Antigua y Barbuda",
    "Arabia Saudita", "Argelia", "Argentina", "Armenia", "Australia", "Austria",
    "Azerbaiyán", "Bahamas", "Barbados", "Bangladés", "Bélgica", "Belice", "Benín",
    "Bielorrusia", "Birmania", "Bolivia", "Bosnia y Herzegovina", "Botsuana",
    "Brasil", "Brunéi", "Bulgaria", "Burkina Faso", "Burundi", "Bután", "Cabo Verde",
    "Camboya", "Camerún", "Canadá", "Catar", "Chad", "Chile", "China", "Chipre",
    "Colombia", "Comoras", "Congo", "Corea del Norte", "Corea del Sur",
    "Costa de Marfil", "Costa Rica", "Croacia", "Cuba", "Dinamarca", "Dominica",
    "Ecuador", "Egipto", "El Salvador", "Emiratos Árabes Unidos", "Eritrea",
    "Eslovaquia", "Eslovenia", "España", "Estados Unidos", "Estonia", "Esuatini",
    "Etiopía", "Fiyi", "Filipinas", "Finlandia", "Francia", "Gabón", "Gambia",
    "Georgia", "Ghana", "Granada", "Grecia", "Guatemala", "Guinea", "Guinea-Bisáu",
    "Guinea Ecuatorial", "Guyana", "Haití", "Honduras", "Hungría", "India",
    "Indonesia", "Irak", "Irán", "Irlanda", "Islandia", "Islas Marshall", "Islas Salomón",
    "Israel", "Italia", "Jamaica", "Japón", "Jordania", "Kazajistán", "Kenia",
    "Kirguistán", "Kiribati", "Kuwait", "Laos", "Lesoto", "Letonia", "Líbano",
    "Liberia", "Libia", "Liechtenstein", "Lituania", "Luxemburgo", "Madagascar",
    "Malasia", "Malaui", "Maldivas", "Malí", "Malta", "Marruecos", "Mauricio",
    "Mauritania", "México", "Micronesia", "Moldavia", "Mónaco", "Mongolia",
    "Montenegro", "Mozambique", "Namibia", "Nauru", "Nepal", "Nicaragua", "Níger",
    "Nigeria", "Noruega", "Nueva Zelanda", "Omán", "Países Bajos", "Pakistán",
    "Palaos", "Palestina", "Panamá", "Papúa Nueva Guinea", "Paraguay", "Perú",
    "Polonia", "Portugal", "Reino Unido", "República Centroafricana", "República Checa",
    "República Democrática del Congo", "República Dominicana", "Ruanda", "Rumania",
    "Rusia", "Samoa", "San Cristóbal y Nieves", "San Marino", "San Vicente y las Granadinas",
    "Santa Lucía", "Santo Tomé y Príncipe", "Senegal", "Serbia", "Seychelles",
    "Sierra Leona", "Singapur", "Siria", "Somalia", "Sri Lanka", "Sudáfrica",
    "Sudán", "Sudán del Sur", "Suecia", "Suiza", "Surinam", "Tailandia", "Taiwán",
    "Tanzania", "Tayikistán", "Timor Oriental", "Togo", "Tonga", "Trinidad y Tobago",
    "Túnez", "Turkmenistán", "Turquía", "Tuvalu", "Ucrania", "Uganda", "Uruguay",
    "Uzbekistán", "Vanuatu", "Vaticano", "Venezuela", "Vietnam", "Yemen", "Yibuti",
    "Zambia", "Zimbabue",
}
ECONOMIC_POLICIES = {
    "neoliberalismo", "neoliberal", "liberalismo", "libertarismo", "keynesianismo",
    "socialismo", "proteccionismo", "desarrollismo", "privatización", "privatizaciones",
    "estatización", "estatizaciones", "ajuste fiscal", "ajuste económico",
    "devaluación", "inflación", "control de precios", "desregulación",
    "redistribución del ingreso", "impuesto a las ganancias", "deuda externa",
    "Fondo Monetario Internacional", "FMI", "dolarización",
}
ALLOWED_TERMS = set().union(
    ARGENTINE_POLITICIANS,
    INTERNATIONAL_POLITICIANS,
    FOOTBALL_PLAYERS,
    ARGENTINE_FOOTBALL_CLUBS,
    BRAZILIAN_FOOTBALL_CLUBS,
    SPANISH_FOOTBALL_CLUBS,
    ITALIAN_FOOTBALL_CLUBS,
    GERMAN_FOOTBALL_CLUBS,
    POLITICAL_TERMS,
    COUNTRIES,
    ECONOMIC_POLICIES,
)


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "nota"


def parse_date(value: Any, path: Path) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value.strip())
        except ValueError:
            pass
    raise ValueError(f"{path}: 'date' debe tener formato YYYY-MM-DD.")


def read_markdown(path: Path) -> tuple[dict[str, Any], str]:
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("---\n") and not raw.startswith("---\r\n"):
        raise ValueError(f"{path.relative_to(ROOT)}: falta el encabezado YAML entre ---.")

    lines = raw.splitlines()
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        raise ValueError(f"{path.relative_to(ROOT)}: no se encontró el cierre del encabezado YAML.")

    metadata = yaml.safe_load("\n".join(lines[1:end])) or {}
    body = "\n".join(lines[end + 1:]).strip()
    if not isinstance(metadata, dict):
        raise ValueError(f"{path.relative_to(ROOT)}: el encabezado debe ser un objeto YAML.")

    for field in REQUIRED_FIELDS:
        if not str(metadata.get(field, "")).strip():
            raise ValueError(f"{path.relative_to(ROOT)}: falta el campo obligatorio '{field}'.")

    metadata["date"] = parse_date(metadata["date"], path).isoformat()
    category = str(metadata["category"]).strip()
    # Acepta categorías definidas sin importar mayúsculas/minúsculas.
    canonical = next((c for c in ALLOWED_CATEGORIES if c.casefold() == category.casefold()), None)
    if not canonical:
        choices = ", ".join(ALLOWED_CATEGORIES)
        raise ValueError(f"{path.relative_to(ROOT)}: categoría '{category}' no válida. Usá: {choices}.")
    metadata["category"] = canonical

    for field in ("title", "subtitle", "author"):
        metadata[field] = str(metadata[field]).strip()

    metadata["featured"] = bool(metadata.get("featured", False))
    metadata["image"] = str(metadata.get("image", "") or "").strip()
    metadata["image_alt"] = str(metadata.get("image_alt", "") or "").strip()
    tags = metadata.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]
    if not isinstance(tags, list):
        raise ValueError(f"{path.relative_to(ROOT)}: 'tags' debe ser una lista.")
    metadata["tags"] = [str(tag).strip() for tag in tags if str(tag).strip()]
    if not body:
        raise ValueError(f"{path.relative_to(ROOT)}: el cuerpo de la nota está vacío.")

    return metadata, body


def markdown_to_html(body: str) -> str:
    # No habilitar HTML crudo: las notas no pueden insertar scripts o markup arbitrario.
    renderer = mistune.create_markdown(
        escape=True,
        plugins=["table", "strikethrough", "url"],
    )
    return renderer(body)


def article_tag_counts(article: dict[str, Any]) -> tuple[Counter[str], dict[str, str]]:
    counts: Counter[str] = Counter()
    display_names: dict[str, str] = {}
    allowed_names = {slugify(term): term for term in sorted(ALLOWED_TERMS, key=str.casefold)}

    searchable_text = " ".join(
        (article["title"], article["subtitle"], article["search_text"])
    )
    normalized_text = unicodedata.normalize("NFKD", searchable_text)
    normalized_text = "".join(
        char for char in normalized_text if not unicodedata.combining(char)
    ).casefold()

    # Los tags explícitos también forman parte de la allowlist.
    for raw_tag in article["tags"]:
        key = slugify(raw_tag)
        if key:
            counts[key] += 2
            display_names.setdefault(key, raw_tag.strip())

    for key, term in allowed_names.items():
        normalized_term = unicodedata.normalize("NFKD", term)
        normalized_term = "".join(
            char for char in normalized_term if not unicodedata.combining(char)
        ).casefold()
        pattern = rf"(?<![a-z0-9]){re.escape(normalized_term)}(?![a-z0-9])"
        occurrences = len(re.findall(pattern, normalized_text))
        if occurrences:
            counts[key] += occurrences
            display_names.setdefault(key, term)

    return counts, display_names


def make_tag_cloud(articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: Counter[str] = Counter()
    display_names: dict[str, str] = {}

    for article in articles:
        article_counts, article_names = article_tag_counts(article)
        counts.update(article_counts)
        for key, name in article_names.items():
            display_names.setdefault(key, name)

    if not counts:
        return []

    min_count, max_count = min(counts.values()), max(counts.values())
    result = []
    for key, count in counts.most_common(24):
        size = 12 if max_count == min_count else round(11 + (count - min_count) * 13 / (max_count - min_count))
        result.append({
            "slug": key,
            "name": display_names[key],
            "count": count,
            "size": size,
        })
    return result


def make_archive(articles: list[dict[str, Any]]) -> list[dict[str, str]]:
    months: dict[str, str] = {}
    for article in articles:
        dt = date.fromisoformat(article["date"])
        slug = f"{dt.year:04d}-{dt.month:02d}"
        label = dt.strftime("%m/%Y")
        months.setdefault(slug, label)
    return [{"slug": slug, "label": label} for slug, label in sorted(months.items(), reverse=True)]


def safe_image_path(image: str, source_path: Path) -> str:
    if not image:
        return ""
    normalized = image.replace("\\", "/").lstrip("/")
    if normalized.startswith("assets/images/"):
        full = (ROOT / normalized).resolve()
        if ROOT.resolve() in full.parents and full.is_file():
            return normalized
        raise ValueError(f"{source_path.relative_to(ROOT)}: no existe la imagen '{normalized}'.")
    raise ValueError(
        f"{source_path.relative_to(ROOT)}: las imágenes deben estar dentro de assets/images/."
    )


def collect_articles() -> list[dict[str, Any]]:
    if not CONTENT_DIR.exists():
        raise ValueError("No existe la carpeta content/.")
    articles: list[dict[str, Any]] = []
    used_urls: set[str] = set()

    for path in sorted(CONTENT_DIR.rglob("*.md")):
        metadata, body = read_markdown(path)
        slug = slugify(path.stem)
        url = f"noticias/{slug}.html"
        if url in used_urls:
            raise ValueError(f"Dos notas generan la misma URL: {url}. Renombrá uno de los archivos.")
        used_urls.add(url)

        metadata["image"] = safe_image_path(metadata["image"], path)
        category_slug = ALLOWED_CATEGORIES[metadata["category"]]
        article = dict(metadata)
        article.update({
            "slug": slug,
            "url": url,
            "source": str(path.relative_to(ROOT)),
            "category_slug": category_slug,
            "search_text": body,
            "body": Markup(markdown_to_html(body)),
        })
        articles.append(article)

    articles.sort(key=lambda item: (item["date"], item["title"].casefold()), reverse=True)

    featured = [article for article in articles if article["featured"]]
    if len(featured) > 1:
        raise ValueError(
            "Hay más de una nota con featured: true. Dejá una sola como destacada."
        )
    if not featured and articles:
        articles[0]["featured"] = True

    return articles


def build_tag_pages(env: Environment, articles: list[dict[str, Any]], tags: list[dict[str, Any]],
                    context: dict[str, Any], out: Path) -> None:
    by_tag: dict[str, list[dict[str, Any]]] = {tag["slug"]: [] for tag in tags}
    for article in articles:
        article_tags, _ = article_tag_counts(article)
        for tag_slug in article_tags.keys() & by_tag.keys():
            by_tag[tag_slug].append(article)

    template = env.get_template("section.html")
    for tag in tags:
        target = out / "temas" / f'{tag["slug"]}.html'
        target.parent.mkdir(parents=True, exist_ok=True)
        page_context = dict(context)
        page_context.update({
            "title": f'Tema: {tag["name"]}',
            "description": f'Artículos relacionados con {tag["name"]}.',
            "breadcrumb": f'Tema: {tag["name"]}',
            "root": "../",
            "section_name": f'Tema: {tag["name"]}',
            "section_description": f'Publicaciones relacionadas con {tag["name"]}.',
            "articles": by_tag[tag["slug"]],
        })
        target.write_text(template.render(**page_context), encoding="utf-8")


def build_site(base_url: str, check_only: bool = False) -> int:
    articles = collect_articles()
    if check_only:
        print(f"OK: {len(articles)} nota(s) validada(s).")
        return 0

    if not TEMPLATES_DIR.exists():
        raise ValueError("No existe templates/.")
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # Para GitHub Pages en un subdirectorio, root debe incluir el prefijo del repositorio.
    prefix = "/" + base_url.strip("/") + "/" if base_url.strip("/") else "/"
    root_value = prefix
    tags = make_tag_cloud(articles)
    archive = make_archive(articles)
    latest = articles[:8]
    featured = next((a for a in articles if a["featured"]), None)
    context = {
        "title": "Portada",
        "description": "Desaprobados por la sociedad: prensa independiente desde el oeste.",
        "breadcrumb": "Portada",
        "root": root_value,
        "articles": articles,
        "latest": latest,
        "featured": featured,
        "tags": tags,
        "archive": archive,
    }

    # Regeneración limpia para no dejar páginas obsoletas.
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)

    home = env.get_template("home.html")
    (OUTPUT_DIR / "index.html").write_text(home.render(**context), encoding="utf-8")

    not_found = env.get_template("404.html")
    not_found_context = dict(context)
    not_found_context.update({
        "title": "Página no encontrada",
        "description": "La página que buscás no existe o ya no está disponible.",
        "breadcrumb": "Página no encontrada",
    })
    (OUTPUT_DIR / "404.html").write_text(
        not_found.render(**not_found_context), encoding="utf-8"
    )

    article_template = env.get_template("article.html")
    for article in articles:
        target = OUTPUT_DIR / article["url"]
        target.parent.mkdir(parents=True, exist_ok=True)
        page_context = dict(context)
        page_context.update({
            "title": article["title"],
            "description": article["subtitle"],
            "breadcrumb": article["title"],
            "article": article,
            "root": prefix,
        })
        target.write_text(article_template.render(**page_context), encoding="utf-8")

    section_template = env.get_template("section.html")
    categories = sorted(ALLOWED_CATEGORIES.keys())
    for category in categories:
        category_slug = ALLOWED_CATEGORIES[category]
        section_articles = [a for a in articles if a["category"] == category]
        target = OUTPUT_DIR / "secciones" / f"{category_slug}.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        page_context = dict(context)
        page_context.update({
            "title": category,
            "description": f'Publicaciones de la sección {category}.',
            "breadcrumb": category,
            "root": "../",
            "section_name": category,
            "section_description": f'Artículos publicados en la sección {category}.',
            "articles": section_articles,
        })
        target.write_text(section_template.render(**page_context), encoding="utf-8")

    # Archivos mensuales y página índice del archivo.
    archive_dir = OUTPUT_DIR / "archivo"
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_rows = []
    for month in archive:
        month_articles = [
            a for a in articles
            if a["date"][:7] == month["slug"]
        ]
        target = archive_dir / f'{month["slug"]}.html'
        page_context = dict(context)
        page_context.update({
            "title": f'Archivo {month["label"]}',
            "description": f'Publicaciones de {month["label"]}.',
            "breadcrumb": f'Archivo {month["label"]}',
            "root": "../",
            "section_name": f'Archivo {month["label"]}',
            "section_description": f'Artículos publicados durante {month["label"]}.',
            "articles": month_articles,
        })
        target.write_text(section_template.render(**page_context), encoding="utf-8")
        archive_rows.append(month)

    archive_index = dict(context)
    archive_index.update({
        "title": "Archivo",
        "description": "Archivo de publicaciones de Desaprobados.",
        "breadcrumb": "Archivo",
        "root": "../",
        "section_name": "Archivo de publicaciones",
        "section_description": "Todas las ediciones archivadas.",
        "articles": articles,
    })
    (archive_dir / "index.html").write_text(section_template.render(**archive_index), encoding="utf-8")

    # Páginas editoriales sencillas para que los enlaces del menú no queden rotos.
    info_template = env.get_template("info.html")
    info_pages = {
        "acerca.html": ("Quiénes somos", "Desaprobados por la sociedad es un diario independiente hecho por un grupo de estudiantes y colaboradores. Publicamos sobre política, fútbol, música, historia, cultura y la escena local, provincial e internacional."),
        "fuentes.html": ("Fuentes y criterios", "Las notas deben identificar sus fuentes cuando corresponda, enlazar documentos públicos y distinguir hechos comprobados, testimonios y opiniones. Si encontrás un error, contactá a la redacción para que podamos revisarlo."),
    }
    for filename, (heading, copy) in info_pages.items():
        page_context = dict(context)
        page_context.update({
            "title": heading, "description": copy, "breadcrumb": heading,
            "root": prefix, "info_heading": heading, "info_copy": copy,
        })
        (OUTPUT_DIR / filename).write_text(info_template.render(**page_context), encoding="utf-8")

    build_tag_pages(env, articles, tags, context, OUTPUT_DIR)

    # JSON legible para herramientas futuras; no contiene el HTML del cuerpo.
    json_articles = []
    for a in articles:
        json_articles.append({
            "title": a["title"],
            "subtitle": a["subtitle"],
            "author": a["author"],
            "date": a["date"],
            "category": a["category"],
            "category_slug": a["category_slug"],
            "url": a["url"],
            "featured": a["featured"],
            "tags": a["tags"],
            "image": a["image"],
        })
    (OUTPUT_DIR / "articles.json").write_text(
        json.dumps(json_articles, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # Copiar recursos públicos.
    if STATIC_DIR.exists():
        shutil.copytree(STATIC_DIR, OUTPUT_DIR / "static", dirs_exist_ok=True)
    if ASSETS_DIR.exists():
        shutil.copytree(ASSETS_DIR, OUTPUT_DIR / "assets", dirs_exist_ok=True)

    print(f"Sitio generado en: {OUTPUT_DIR}")
    print(f"Notas: {len(articles)} | Secciones: {len(categories)} | Temas: {len(tags)}")
    print("Para previsualizar: python -m http.server 8000 -d dist")
    print(f"Acceder en: http://localhost:8000{prefix}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera el sitio estático de Desaprobados.")
    base_url_options = parser.add_mutually_exclusive_group()
    base_url_options.add_argument(
        "--base-url",
        default="",
        help="Prefijo de GitHub Pages, por ejemplo /desaprobados/. Vacío para dominio raíz.",
    )
    base_url_options.add_argument(
        "--pages",
        action="store_true",
        help="Prepara las rutas para el repositorio GitHub Pages DesaprobadosMedia.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Valida los Markdown y metadatos sin generar HTML.",
    )
    args = parser.parse_args()
    base_url = "DesaprobadosMedia" if args.pages else args.base_url
    try:
        return build_site(base_url, check_only=args.check)
    except (ValueError, OSError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
