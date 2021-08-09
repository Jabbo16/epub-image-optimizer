from pathlib import Path
from typing import Tuple
import zipfile
import re
import tinify
import logging
from PIL import Image
from io import BytesIO, StringIO
import datetime
from defusedxml.lxml import _etree, parse
from lxml.html import HTMLParser


def get_opf(epub_zipfile: zipfile.ZipFile) -> str:
    """
    Get the .opf file within the ebook archive.

    Returns:
        (str): the path to the .opf file.
        None: if not found
    """
    for fname in epub_zipfile.namelist():
        if fname.endswith(".opf"):
            return fname
    return None

def get_cover_xhtml(epub_zipfile: zipfile.ZipFile) -> str:
    """
    Get the cover.xhtml file within the ebook archive.

    Returns:
        (str): the path to the cover.xhtml file.
        None: if not found
    """
    for fname in epub_zipfile.namelist():
        if fname.endswith("cover.xhtml"):
            return fname
    return None

def find_cover_image(opf_file: bytes, opf_folder: Path, epub_zipfile: zipfile.ZipFile) -> Path:
    root = _etree.fromstring(opf_file)
    ns = {
        "opf": "http://www.idpf.org/2007/opf",
    }
    try:
        # Method #1: Search metadata first
        metadata = root.find("opf:metadata", ns)
        cover_content = None
        for item in list(metadata):
            if item.get("name") == "cover":
                cover_content = item.get("content")
                break
        image_pattern = "([-\w]+\.(?:jpg|png|jpeg))"
        regex = re.findall(image_pattern, cover_content, re.IGNORECASE)
        if not regex:
            manifest = root.find("opf:manifest", ns)
            for item in list(manifest):
                if item.get("id") == cover_content:
                    image_href = item.get("href")
                    regex = re.findall(image_pattern, image_href, re.IGNORECASE)
                    if not regex:
                        raise Exception
                    return Path(opf_folder, image_href).as_posix()
            raise Exception
        return Path(opf_folder, cover_content).as_posix()
    except Exception:
        # Cover not found in metadata, try alternative method #2
        # Search in manifest if there is an item with the "cover-image" id
        try:
            manifest = root.find("opf:manifest", ns)
            for item in list(manifest):
                if item.get("id") == "cover-image":
                    image_href = item.get("href")
                    regex = re.findall(image_pattern, image_href, re.IGNORECASE)
                    if not regex:
                        raise Exception
                    return Path(opf_folder, image_href).as_posix()
            raise Exception
        except Exception:
            # Cover not found in manifest, try alternative method #3
            # Search in cover.xhtml file
            try:
                cover_xhtml_path = get_cover_xhtml(epub_zipfile)
                if not cover_xhtml_path:
                    return None
                with epub_zipfile.open(cover_xhtml_path, "r") as cover_xhtml_file:
                    cover_xhtml_content = cover_xhtml_file.read()
                    root = parse(StringIO(str(cover_xhtml_content)), parser=HTMLParser())
                    cover_image = root.xpath('//img/@src')[0]
                    return Path(opf_folder, cover_image).as_posix()
            except Exception as e:
                print(e)
                pass
    return None


def optimize_epub(
    input_epub: Path, output_dir: Path, max_image_resolution: Tuple[int, int] = None, tinify_api_key: str = None,
) -> Path:
    src_epub = input_epub.absolute()
    dst_epub = Path(
        output_dir, src_epub.name.replace(".epub", "_optimized.epub")
    ).absolute()

    with zipfile.ZipFile(src_epub) as epub_zipfile, zipfile.ZipFile(
        dst_epub, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as outzip:
        opf_file_path = get_opf(epub_zipfile)
        if not opf_file_path:
            pass
            # TODO do something if not opf found
        opf_folder = Path(opf_file_path).parent
        cover_image_path = None
        print(opf_file_path)
        with epub_zipfile.open(opf_file_path, "r") as opf_file:
            opf_content = opf_file.read()
            cover_image_path = find_cover_image(opf_content, opf_folder, epub_zipfile)
        if not cover_image_path:
            raise Exception(f"Cover image not found in EPUB {src_epub}")
        print(cover_image_path)
        for item in epub_zipfile.infolist():
            if item.filename in cover_image_path:
                continue
            buffer = epub_zipfile.read(item.filename)
            outzip.writestr(item.filename, buffer)
        with epub_zipfile.open(cover_image_path) as src_cover:
            ztext = src_cover.read()
            result_data = ztext
            if max_image_resolution:
                image = Image.open(BytesIO(ztext))
                image.thumbnail(max_image_resolution)
                result_data = BytesIO()
                image.save(result_data, format=image.format)
                result_data = result_data.getvalue()
            if tinify_api_key:
                tinify.key = tinify_api_key
                result_data = tinify.from_buffer(result_data).to_buffer()
            cover_zipfile = zipfile.ZipInfo(
                filename=cover_image_path, date_time=datetime.datetime.now().timetuple()
            )
            outzip.writestr(cover_zipfile, result_data)
            return dst_epub
