import datetime
import logging
import re
import zipfile
from io import BytesIO, StringIO
from pathlib import Path
from threading import Event
from typing import List, Tuple

import tinify
from defusedxml.lxml import _etree, parse
from PIL import Image
from rich.progress import Progress, TaskID

IMAGE_PATTERN = r"([-\w]+\.(?:jpg|png|jpeg))"


def get_opf(epub_zipfile: zipfile.ZipFile) -> str:
    """
    Get the .opf file within the ebook archive.

    Args:
        epub_zipfile (zipfile.ZipFile): Epub zipfile

    Returns:
        (str): the path to the .opf file.
        (None): if not found
    """
    for fname in epub_zipfile.namelist():
        if fname.endswith(".opf"):
            return fname
    return None


def get_cover_xhtml(epub_zipfile: zipfile.ZipFile) -> str:
    """
    Get the cover.xhtml file within the ebook archive.

    Args:
        epub_zipfile (zipfile.ZipFile): Epub zipfile

    Returns:
        (str): the path to the cover.xhtml file.
        (None): if not found
    """
    for fname in epub_zipfile.namelist():
        if fname.endswith("cover.xhtml"):
            return fname
    return None


def get_images(epub_zipfile: zipfile.ZipFile) -> List[Path]:
    """
    Find and return a list of all images inside the epub file

    Args:
        epub_zipfile (zipfile.ZipFile): Epub zipfile

    Returns:
        List[Path]: List of paths of each image found
    """
    images = []
    for fname in epub_zipfile.namelist():
        if re.findall(IMAGE_PATTERN, fname, re.IGNORECASE):
            images.append(Path(fname).as_posix())
    return images


def find_cover_image(
    opf_file: bytes, opf_folder: Path, epub_zipfile: zipfile.ZipFile
) -> Path:
    """
    Searches for cover image inside the epub file.
    It has 3 different alternatives:
    First, tries to retrieve cover image from metadata tags found in the opf file.
    Second, tries to retrieve cover image from manifest tags found in the opf file.
    At last, tries to find the cover image by looking at the 'cover.xhtml' file.

    Args:
        opf_file (bytes): content of the .opf file of the epub file
        opf_folder (Path): path where the .opf file is located inside the epub file
        epub_zipfile (zipfile.ZipFile): epub zipfile

    Returns:
        Path: Cover image location
    """
    root = _etree.fromstring(opf_file)
    ns = {"opf": "http://www.idpf.org/2007/opf"}
    try:
        # Method #1: Search metadata first
        metadata = root.find("opf:metadata", ns)
        cover_content = None
        for item in list(metadata):
            if item.get("name") == "cover":
                cover_content = item.get("content")
                break
        regex = re.findall(IMAGE_PATTERN, cover_content, re.IGNORECASE)
        if not regex:
            manifest = root.find("opf:manifest", ns)
            for item in list(manifest):
                if item.get("id") == cover_content:
                    image_href = item.get("href")
                    regex = re.findall(IMAGE_PATTERN, image_href, re.IGNORECASE)
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
                    regex = re.findall(IMAGE_PATTERN, image_href, re.IGNORECASE)
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
                    root = parse(
                        StringIO(str(cover_xhtml_content)), parser=_etree.HTMLParser()
                    )
                    cover_image = root.xpath("//img/@src")[0]
                    return Path(opf_folder, cover_image).as_posix()
            except Exception:
                pass
    return None


def optimize_epub(
    input_epub: Path,
    output_dir: Path,
    only_cover: bool,
    keep_color: bool,
    log: logging.Logger,
    progress: Progress,
    task_id: TaskID,
    done_event: Event,
    max_image_resolution: Tuple[int, int] = None,
    tinify_api_key: str = None,
) -> Path:
    """
    Main method, optimizes images inside epub file

    Args:
        input_epub (Path): Path to the epub file to optimize
        output_dir (Path): Path where the output epub file will be created
        only_cover (bool): if True, optimize only cover image
        keep_color (bool): if True, don't transform images to B&W
        max_image_resolution (Tuple[int, int], optional): Fit images to this resolution if bigger.
        tinify_api_key (str, optional): API key for the Tinify image optimizing service.

    Raises:
        Exception: If it can't optimize epub or if cover image is not found (if only_cover is True)

    Returns:
        Path: Path to the generated, optimized epub file
    """
    src_epub = input_epub.absolute()
    dst_epub = Path(
        output_dir, src_epub.name.replace(".epub", "_optimized.epub")
    ).absolute()

    with zipfile.ZipFile(src_epub) as epub_zipfile, zipfile.ZipFile(
        dst_epub, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as outzip:
        images_to_optimize = []
        if only_cover:
            opf_file_path = get_opf(epub_zipfile)
            if not opf_file_path:
                # TODO do something if not opf found
                log.warn("OPF file not found")
            opf_folder = Path(opf_file_path).parent
            cover_image_path = None
            with epub_zipfile.open(opf_file_path, "r") as opf_file:
                opf_content = opf_file.read()
                cover_image_path = find_cover_image(
                    opf_content, opf_folder, epub_zipfile
                )
            if not cover_image_path:
                raise Exception(f"Cover image not found in EPUB {src_epub}")
            images_to_optimize.append(cover_image_path)
        else:
            # Find all images inside epub
            images_to_optimize += get_images(epub_zipfile)
        if len(images_to_optimize) == 0:
            raise Exception(f"No images found in EPUB {src_epub}")
        for item in epub_zipfile.infolist():
            if item.filename in images_to_optimize:
                continue
            buffer = epub_zipfile.read(item.filename)
            outzip.writestr(item.filename, buffer)
        # Setup progress bar
        progress.update(task_id, total=int(len(images_to_optimize)))
        progress.start_task(task_id)
        for image_path in images_to_optimize:
            with epub_zipfile.open(image_path) as image_file:
                ztext = image_file.read()
                result_data = ztext
                image = Image.open(BytesIO(ztext))
                image_format = image.format
                if max_image_resolution:
                    image.thumbnail(max_image_resolution)
                if not keep_color:
                    image = image.convert("L")
                result_data = BytesIO()
                image.save(result_data, format=image_format)
                result_data = result_data.getvalue()
                if tinify_api_key:
                    tinify.key = tinify_api_key
                    try:
                        result_data = tinify.from_buffer(result_data).to_buffer()
                    except tinify.AccountError as e:
                        log.exception(e)
                        raise Exception(e.message)
                cover_zipfile = zipfile.ZipInfo(
                    filename=image_path, date_time=datetime.datetime.now().timetuple()
                )
                outzip.writestr(cover_zipfile, result_data)
                log.debug("Optimized Image %s", image_path)
                progress.update(task_id, advance=1)
                if done_event.is_set():
                    return dst_epub
        return dst_epub
