import urllib.request
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from urllib.parse import urljoin

WEB_URL = "https://cieautomotive.com/noticias"
BASE_URL = "https://cieautomotive.com"
OUTPUT_FILE = Path("cie-automotive.xml")


def descargar_noticias():
    solicitud = urllib.request.Request(
        WEB_URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/124 Safari/537.36"
            ),
            "Accept": "text/html",
        },
    )

    with urllib.request.urlopen(solicitud, timeout=60) as respuesta:
        contenido = respuesta.read()

    soup = BeautifulSoup(contenido, "html.parser")

    noticias = []
    enlaces_encontrados = set()

    for bloque in soup.select(
        "li.col-12 div.border-bottom-grey"
    ):
        enlace_elemento = bloque.select_one("a[href]")
        fecha_elemento = bloque.select_one("p")
        textos = bloque.select("p")

        if not enlace_elemento or not fecha_elemento:
            continue

        titulo = enlace_elemento.get_text(" ", strip=True)
        enlace = urljoin(
            BASE_URL,
            enlace_elemento.get("href", ""),
        )
        fecha = fecha_elemento.get_text(" ", strip=True)

        descripcion = titulo

        if len(textos) > 1:
            posible_descripcion = textos[-1].get_text(
                " ",
                strip=True,
            )

            if posible_descripcion:
                descripcion = posible_descripcion

        if (
            not titulo
            or not enlace
            or enlace in enlaces_encontrados
        ):
            continue

        enlaces_encontrados.add(enlace)

        noticias.append(
            {
                "titulo": titulo,
                "enlace": enlace,
                "fecha": fecha,
                "descripcion": descripcion,
            }
        )

    return noticias


def crear_rss(noticias):
    rss = ET.Element(
        "rss",
        {
            "version": "2.0",
            "xmlns:atom": "http://www.w3.org/2005/Atom",
        },
    )

    canal = ET.SubElement(rss, "channel")

    ET.SubElement(canal, "title").text = (
        "Noticias de CIE Automotive"
    )
    ET.SubElement(canal, "link").text = WEB_URL
    ET.SubElement(canal, "description").text = (
        "Últimas noticias corporativas y financieras "
        "de CIE Automotive"
    )
    ET.SubElement(canal, "language").text = "es"
    ET.SubElement(canal, "lastBuildDate").text = format_datetime(
        datetime.now(timezone.utc)
    )

    enlace_atom = ET.SubElement(
        canal,
        "{http://www.w3.org/2005/Atom}link",
    )
    enlace_atom.set("href", WEB_URL)
    enlace_atom.set("rel", "self")
    enlace_atom.set("type", "application/rss+xml")

    for noticia in noticias:
        elemento = ET.SubElement(canal, "item")

        ET.SubElement(
            elemento,
            "title",
        ).text = noticia["titulo"]

        ET.SubElement(
            elemento,
            "link",
        ).text = noticia["enlace"]

        ET.SubElement(
            elemento,
            "description",
        ).text = noticia["descripcion"]

        ET.SubElement(
            elemento,
            "category",
        ).text = "CIE Automotive"

        identificador = ET.SubElement(elemento, "guid")
        identificador.set("isPermaLink", "true")
        identificador.text = noticia["enlace"]

        try:
            fecha_publicacion = datetime.strptime(
                noticia["fecha"],
                "%d/%m/%Y",
            ).replace(tzinfo=timezone.utc)

            ET.SubElement(
                elemento,
                "pubDate",
            ).text = format_datetime(fecha_publicacion)
        except ValueError:
            pass

    ET.indent(rss, space="  ")

    ET.ElementTree(rss).write(
        OUTPUT_FILE,
        encoding="utf-8",
        xml_declaration=True,
    )


def main():
    noticias = descargar_noticias()

    if not noticias:
        raise RuntimeError(
            "No se encontraron noticias de CIE Automotive"
        )

    crear_rss(noticias)

    print(
        f"RSS creada correctamente con "
        f"{len(noticias)} noticias"
    )


if __name__ == "__main__":
    main()
