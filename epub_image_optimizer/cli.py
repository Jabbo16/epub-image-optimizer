import logging
import sys
from glob import glob
from pathlib import Path
from typing import Tuple

import click
import tinify
from click.exceptions import ClickException

from epub_image_optimizer.image_optimizer import optimize_epub

DEFAULT_OUTPUT_FOLDER = "./epub_image_optimizer_output"
MIN_IMAGE_RESOLUTION = (1, 1)


def validate_input_file(ctx, param, value) -> Path:
    if not value:
        return
    # Check source file is epub
    filename = click.format_filename(value, True)
    if not filename.__contains__(".epub"):
        raise click.BadParameter(f'"{filename}" is not an epub file', ctx, param)
    return value


def validate_tinify_api_key(ctx, param, value) -> str:
    # Validate Tinify API key
    if not value:
        return
    try:
        tinify.key = value
        tinify.validate()
        click.echo(
            f"Validated Tinify API key, number of compressions done this month: {tinify.compression_count}, "
            f"remaining compressions this month (if free mode): {500 - tinify.compression_count}"
        )
    except tinify.Error as e:
        # Validation of API key failed.
        raise click.BadParameter(
            f"Tinify API key validation failed: {e.message}", ctx, param
        )
    return value


def validate_max_image_resolution(ctx, param, value) -> Tuple[int, int]:
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
    "--all-images",
    is_flag=True,
    help="Optimize all images inside ebook, not only the cover",
)
@click.option(
    "--keep-color",
    is_flag=True,
    help="If this flag is present images will preserve colors (not converted to BW)",
)
@click.option("--version", is_flag=True, help="Show current version")
def main(
    input_dir: Path,
    output_dir: Path,
    input_file: Path,
    max_image_resolution: Tuple[int, int],
    tinify_api_key: str,
    all_images: bool,
    keep_color: bool,
    version: bool,
):
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

    input_epubs = None
    if input_dir:
        input_epubs = [Path(epub) for epub in glob(str(Path(input_dir, "*.epub")))]
    else:
        input_epubs = [Path(input_file)]
    if not input_epubs:
        # TODO better exception handling overall
        raise Exception(f"No epubs found in input-dir {input_dir}")
    for input_epub in input_epubs:
        output_epub = optimize_epub(
            input_epub, output_dir, all_images, keep_color, max_image_resolution, tinify_api_key
        )
        # TODO log
        click.echo(f"Created optimized EPUB file {output_epub.absolute()}")
