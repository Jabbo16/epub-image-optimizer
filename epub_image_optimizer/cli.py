from epub_image_optimizer.epub_image_optimizer import optimize_epub
import click
import logging
import sys
from click.exceptions import ClickException
import tinify
from pathlib import Path

DEFAULT_OUTPUT_FOLDER = "./epub_image_optimizer_output"
MIN_IMAGE_RESOLUTION = (1, 1)


def validate_input_file(ctx, param, value):
    if value:
        # Check source file is epub
        filename = click.format_filename(value, True)
        if not filename.__contains__(".epub"):
            raise click.BadParameter(f'"{filename}" is not an epub file', ctx, param)
        return value


def validate_tinify_api_key(ctx, param, value):
    # Validate Tinify API key
    if value:
        try:
            tinify.key = value
            tinify.validate()
            click.echo(
                "Validated Tinify API key, number of compressions done this month: {}, remaining compressions this month (if free mode): {}".format(
                    tinify.compression_count, 500 - tinify.compression_count
                )
            )
        except tinify.Error as e:
            # Validation of API key failed.
            raise click.BadParameter(
                "Tinify API key validation failed: " + e.message, ctx, param
            )
        return value


def validate_max_image_resolution(ctx, param, value):
    # Check image_size params
    if value:
        if value < MIN_IMAGE_RESOLUTION:
            raise click.BadParameter(
                '"--max-image-size" values can not be lower than "{}"'.format(
                    MIN_IMAGE_RESOLUTION, ctx, param
                )
            )
        return value


def validate_output_dir(ctx, param, value):
    output_folder = Path(value)
    # Create folder
    try:
        output_folder.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise ClickException(
            "Can not create output folder {}: {}".format(output_folder.absolute(), e)
        )
    return output_folder.absolute()


def show_version(ctx, param, value):
    # Print version and exit
    if value:
        from epub_image_optimizer import __version__

        click.echo(__version__)
        sys.exit(0)


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
    help="Fit image resolution to this values, good for handling images with higher resolutions than your ebook-reader",
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
    "--version", is_flag=True, help="Show current version", callback=show_version
)
def main(
    input_dir, output_dir, input_file, max_image_resolution, tinify_api_key, version
):
    # Custom validation
    # Both input options can not be present at the same time
    if input_dir and input_file:
        raise ClickException(
            '"--input-dir" and "--input-file" parameters can not be set at the same time'
        )

    # Both input options can not be missing at the same time
    if not input_dir and not input_file:
        raise ClickException(
            'Atleast one of the "--input-dir" and "--input-file" parameters is required'
        )
    # TODO get epubs from either file or all inside folder, iterate and call function
    input_epub = input_file
    output_epub = optimize_epub(
        input_epub, output_dir, max_image_resolution, tinify_api_key
    )
