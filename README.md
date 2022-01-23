# epub-image-optimizer

![GitHub Workflow Status](https://img.shields.io/github/workflow/status/jabbo16/epub-image-optimizer/tests)
![PyPI](https://img.shields.io/pypi/v/epub-image-optimizer)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/epub-image-optimizer)
[![codecov](https://codecov.io/gh/Jabbo16/epub-image-optimizer/branch/main/graph/badge.svg?token=FCE3APT4ZP)](https://codecov.io/gh/Jabbo16/epub-image-optimizer)
[![DeepSource](https://deepsource.io/gh/Jabbo16/epub-image-optimizer.svg/?label=active+issues&show_trend=true)](https://deepsource.io/gh/Jabbo16/epub-image-optimizer/?ref=repository-badge)
![GitHub](https://img.shields.io/github/license/jabbo16/epub-image-optimizer)

Small Python CLI application to optimize images (including the cover) inside epub files. Perfect fit for optimizing LNs as they usually have a lot of images.

## Installation

From [PyPI](https://pypi.python.org/pypi/epub-image-optimizer/) directly:

```shell
pip install epub-image-optimizer
```

or

```shell
python3 -m pip install epub-image-optimizer
```

## Usage

```text
Usage: epub-image-optimizer [OPTIONS]

  EPUB Image Optimization tool

Options:
  --input-dir DIRECTORY           Input folder
  --output-dir DIRECTORY          Output folder
  --input-file FILE               Path to Epub Input file
  --max-image-resolution <INTEGER INTEGER>...
                                  Fit image resolution to this values, good
                                  for handling images with higher
                                  resolutions than your ebook-reader
  --tinify-api-key TEXT           Tinify api-key
  --only-cover                    Optimize only the cover image, ignoring all
                                  other images
  --workers INTEGER               Number of threaded workers to use, default
                                  is 'cpu count + 4'
  --keep-color                    If this flag is present images will preserve
                                  colors (not converted to BW)
  --log-level [INFO|DEBUG|WARN|ERROR]
                                  Set log level, default is 'INFO'
  --version                       Show current version
  --help                          Show this message and exit.
```

## Examples

### Convert all images to BW

```shell
epub-image-optimizer --input-file <my-epub>
```

### Convert only cover to BW

```shell
epub-image-optimizer --input-file <my-epub> --only-cover
```

### Optimize all images while keeping colors

```shell
epub-image-optimizer --input-file <my-epub> --keep-color
```

Note: At the moment this won't do anything as there is currently no optimization if not using Tinify.

### Optimize all images using Tinify while keeping colors

```shell
epub-image-optimizer --input-file <my-epub> --keep-color --tinify-api-key <tinify-api-key>
```

Note: You can obtain your Tinify API Key [here](https://tinypng.com/developers). Free tier is limited to 500 images/month.

### Optimize and fit all images to custom resolution while keeping colors

```shell
epub-image-optimizer --input-dir <folder> --max-image-resolution 1680 1264 --tinify-api-key <tinify-api-key>
```

Note: This will optimize all epubs inside `input-dir` folder, used my Kobo Libra H2O screen size as example.

## Development

[Poetry](https://github.com/python-poetry/poetry) is used for managing packages, dependencies and building the project.

Poetry can be installed by following the [instructions](https://github.com/python-poetry/poetry). Afterwards you can use `poetry install` within the project folder to install all dependencies.
