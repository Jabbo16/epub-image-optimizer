import logging
import signal
import sys
from concurrent.futures import ThreadPoolExecutor
from glob import glob
from pathlib import Path
from threading import Event
from typing import Tuple

import click
import coloredlogs
import tinify
from click.exceptions import ClickException
from rich.progress import BarColumn, Progress, TextColumn, TimeRemainingColumn

from epub_image_optimizer.image_optimizer import optimize_epub
from epub_image_optimizer.progress_bar import OptimizeImageColumn

DEFAULT_OUTPUT_FOLDER = "./epub_image_optimizer_output"
MIN_IMAGE_RESOLUTION = (1, 1)


def validate_input_file(ctx, param, value) -> Path:
    """
    Validate if input file is an epub file

    Args:
        ctx ([type]): Click context
        param ([type]): Click parameter
        value ([type]): Click parameter value

    Raises:
        click.BadParameter: If input file is not an epub file

    Returns:
        Path: Path to the input file
    """
    if not value:
        return
    # Check source file is epub
    filename = click.format_filename(value, True)
    if not filename.endswith(".epub"):
        raise click.BadParameter(f'"{filename}" is not an epub file', ctx, param)
    return value


def validate_tinify_api_key(ctx, param, value) -> str:
    """
    Validates that the Tinify API key is valid

    Args:
        ctx ([type]): Click context
        param ([type]): Click parameter
        value ([type]): Click parameter value

    Raises:
        click.BadParameter: If validation fails

    Returns:
        str: Tinify API key
    """
    # Validate Tinify API key
    if not value:
        return
    try:
        tinify.key = value
        tinify.validate()
        click.echo(
            "Validated Tinify API key, number of compressions done this month: {}, "
            "remaining compressions this month (if free mode): {}".format(
                tinify.compression_count, 500 - tinify.compression_count
            )
        )
    except tinify.Error as e:
        # Validation of API key failed.
        raise click.BadParameter(
            f"Tinify API key validation failed: {e.message}", ctx, param
        )
    return value


def validate_max_image_resolution(ctx, param, value) -> Tuple[int, int]:
    """
    Validates Width and Height

    Args:
        ctx ([type]): Click context
        param ([type]): Click parameter
        value ([type]): Click parameter value

    Raises:
        click.BadParameter: if target size is lower than :attr:`MIN_IMAGE_RESOLUTION`

    Returns:
        Tuple[int, int]: Size to fit images
    """
    # Check image_size params
    if not value:
        return
    if value < MIN_IMAGE_RESOLUTION:
        raise click.BadParameter(
            f'"--max-image-size" values can not be lower than "{MIN_IMAGE_RESOLUTION}"',
            ctx,
            param,
        )
    return value


def validate_output_dir(unused_ctx, unused_param, value) -> Path:
    """
    Validate output dir, creates dir

    Args:
        ctx ([type]): Click context
        param ([type]): Click parameter
        value ([type]): Click parameter value

    Raises:
        ClickException: If program fails to create output directory

    Returns:
        Path: Output directory path
    """
    output_folder = Path(value)
    # Create folder
    try:
        output_folder.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise ClickException(
            f"Can not create output folder {output_folder.absolute()}: {e}"
        )
    return output_folder.absolute()


@click.command()
@click.option(
    "--input-dir",
    nargs=1,
    required=False,
    help="Input folder",
    type=click.Path(exists=True, file_okay=False, readable=True),
)
@click.option(
    "--output-dir",
    nargs=1,
    default=DEFAULT_OUTPUT_FOLDER,
    help="Output folder",
    callback=validate_output_dir,
    type=click.Path(file_okay=False, writable=True),
)
@click.option(
    "--input-file",
    nargs=1,
    required=False,
    help="Path to Epub Input file",
    callback=validate_input_file,
    type=click.Path(exists=True, dir_okay=False, readable=True),
)
@click.option(
    "--max-image-resolution",
    required=False,
    callback=validate_max_image_resolution,
    help="Fit image resolution to this values, good for handling \
        images with higher resolutions than your ebook-reader",
    type=click.Tuple([int, int]),
)
@click.option(
    "--tinify-api-key",
    nargs=1,
    required=False,
    callback=validate_tinify_api_key,
    help="Tinify api-key",
    type=str,
    envvar="TINIFY_API_KEY",
)
@click.option(
    "--only-cover",
    is_flag=True,
    help="Optimize only the cover image, ignoring all other images",
)
@click.option(
    "--keep-color",
    is_flag=True,
    help="If this flag is present images will preserve colors (not converted to BW)",
)
@click.option(
    "--workers",
    required=False,
    nargs=1,
    default=None,
    type=int,
    help="Number of threaded workers to use, default is 'cpu count + 4'",
)
@click.option(
    "--log-level",
    required=False,
    nargs=1,
    default="INFO",
    type=click.Choice(["INFO", "DEBUG", "WARN", "ERROR"], case_sensitive=False),
    help="Set log level, default is 'INFO'",
)
@click.option("--version", is_flag=True, help="Show current version")
def main(
    input_dir: Path,
    output_dir: Path,
    input_file: Path,
    max_image_resolution: Tuple[int, int],
    tinify_api_key: str,
    only_cover: bool,
    keep_color: bool,
    workers: int,
    log_level: str,
    version: bool,
):
    """EPUB Image Optimization tool"""
    # Check if version is True, in that case, print version and exit
    if version:
        from epub_image_optimizer import __version__

        click.echo(__version__)
        sys.exit(0)
    # Custom validation
    # Both input options can not be present at the same time
    if input_dir and input_file:
        raise ClickException(
            '"--input-dir" and "--input-file" \
                parameters can not be set at the same time'
        )

    # Both input options can not be missing at the same time
    if not input_dir and not input_file:
        raise ClickException(
            'Atleast one of the "--input-dir" and "--input-file" parameters is required'
        )
    log = logging.getLogger("epub_image_optimizer")
    coloredlogs.install(
        fmt="%(asctime)s,%(msecs)03d %(name)s %(levelname)s %(message)s",
        level=log_level,
        logger=log,
    )
    input_epubs = None
    if input_dir:
        input_epubs = [Path(epub) for epub in glob(str(Path(input_dir, "*.epub")))]
    else:
        input_epubs = [Path(input_file)]
    if not input_epubs:
        # TODO better exception handling overall
        raise Exception(f"No epubs found in input-dir {input_dir}")

    done_event = Event()

    def handle_sigint():
        """Handle SIGINT signal"""
        done_event.set()

    signal.signal(signal.SIGINT, handle_sigint)
    progress = Progress(
        TextColumn("[bold blue]{task.fields[filename]}", justify="left"),
        BarColumn(bar_width=None),
        "[progress.percentage]{task.percentage:>3.1f}%",
        "•",
        OptimizeImageColumn(),
        "•",
        TimeRemainingColumn(),
    )
    click.echo(f"Optimizing {len(input_epubs)} epubs to {output_dir.absolute()}")
    with progress, ThreadPoolExecutor(max_workers=workers) as pool:
        for input_epub in input_epubs:
            # Create a logger object.
            epub_log = logging.getLogger(input_epub.name)
            coloredlogs.install(
                fmt="%(asctime)s,%(msecs)03d %(name)s %(levelname)s %(message)s",
                level=log_level,
                logger=epub_log,
            )
            try:
                log.debug("Optimizing EPUB file %s", input_epub.absolute())
                task_id = progress.add_task(
                    "optimize", filename=input_epub.name, start=False
                )
                pool.submit(
                    optimize_epub,
                    input_epub,
                    output_dir,
                    only_cover,
                    keep_color,
                    epub_log,
                    progress,
                    task_id,
                    done_event,
                    max_image_resolution,
                    tinify_api_key,
                )
            except Exception as e:
                log.exception("Error optimizing %s: %s", input_epub.name, e)
