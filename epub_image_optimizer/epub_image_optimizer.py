from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET
import re
import shutil
import tinify
import tempfile
import logging
from PIL import Image
from io import BytesIO
import datetime


def get_opf(epub_zipfile):
    """
    Get the .opf file within the ebook archive.

    Raises:
        Exception: If it cannot parse metadata file

    Returns:
        (str): the path to the .opf file.
    """
    for fname in epub_zipfile.namelist():
        if fname.endswith(".opf"):
            return fname
    raise Exception


def find_cover_image(opf_file, opf_folder):
    try:
        root = ET.fromstring(opf_file)
        ns = {
            "opf": "http://www.idpf.org/2007/opf",
        }

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
        return Path(opf_folder, cover_content).as_posix()
    except Exception as e:
        return None


def optimize_epub(
    input_epub, output_dir, max_image_resolution=None, tinify_api_key=None
):
    src_epub = Path(input_epub).absolute()
    dst_epub = Path(
        output_dir, src_epub.name.replace(".epub", "_optimized.epub")
    ).absolute()

    with zipfile.ZipFile(src_epub) as epub_zipfile, zipfile.ZipFile(
        dst_epub, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as outzip:
        opf_file = get_opf(epub_zipfile)
        opf_folder = Path(opf_file).parent
        cover_image_path = None

        with epub_zipfile.open(opf_file, "r") as zfile:
            ztext = zfile.read()
            cover_image_path = find_cover_image(ztext, opf_folder)

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
