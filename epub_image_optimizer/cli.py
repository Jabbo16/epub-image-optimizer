import click
import logging
import sys
from click.exceptions import ClickException
import tinify

DEFAULT_OUTPUT_FOLDER = './epub_image_optimizer_output'
MIN_IMAGE_RESOLUTION = (1, 1)


@click.command()
@click.option('--input-dir', nargs=1, required=False, help='Input folder', type=click.Path(exists=True, file_okay=False, readable=True))
@click.option('--output-dir', nargs=1, default=DEFAULT_OUTPUT_FOLDER, help='Output folder', type=click.Path(file_okay=False, writable=True))
@click.option('--input-file', nargs=1, required=False, help='Input file', type=click.Path(exists=True, dir_okay=False, readable=True))
@click.option('--max-image-resolution', required=False, help='Fit image resolution to this values, good for handling images with higher resolutions than your ebook-reader', type=click.Tuple([int, int]))
@click.option('--tinify-api-key', nargs=1, required=False, help='Tinify api-key', type=str, envvar='TINIFY_API_KEY')
@click.option('--version', is_flag=True, help='Show current version')
def main(input_dir, output_dir, input_file, max_image_resolution, tinify_api_key, version):

    # Print version and exit
    if version:
        from epub_image_optimizer import __version__
        click.echo(__version__)
        sys.exit(0)

    # Custom validation
    # Both input options can not be present at the same time
    if input_dir and input_file:
        raise ClickException(
            '"--input-dir" and "--input-file" parameters can not be set at the same time')

    # Both input options can not be missing at the same time
    if not input_dir and not input_file:
        raise ClickException(
            'Atleast one of the "--input-dir" and "--input-file" parameters is required')

    # Check source file is epub
    if input_file:
        filename = click.format_filename(input_file, True)
        if not filename.__contains__(".epub"):
            raise ClickException(
                f'input-file "{filename}" is not an epub file')

    # Validate Tinify API key
    if tinify_api_key:
        try:
            tinify.key = tinify_api_key
            tinify.validate()
            click.echo("Validated Tinify API key, number of compressions done this month: {}, remaining compressions this month (if free mode): {}".format(
                tinify.compression_count, 500 - tinify.compression_count))
        except tinify.Error as e:
            # Validation of API key failed.
            raise ClickException(
                "Tinify API key validation failed: " + e.message)

    # Check image_size params
    if max_image_resolution and max_image_resolution < MIN_IMAGE_RESOLUTION:
        raise ClickException(
            '"--max-image-size" values can not be lower than "{}"'.format(MIN_IMAGE_RESOLUTION))

    # Check output dir, create if not already present
    # TODO
