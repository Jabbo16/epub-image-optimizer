from epub_image_optimizer import __version__
from click.testing import CliRunner
from epub_image_optimizer.cli import main
import os
from pathlib import Path

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_EPUB = Path(TEST_DIR, "moby-dick.epub")
TEST_BAD_EPUB = Path(TEST_DIR, "notanepub.test")
TEST_BAD_FOLDER = Path(TEST_DIR, "idontexist")

VERSION_COMMAND = ["--version"]
BAD_BOTH_PARAMS_COMMAND = ["--input-dir", ".", "--input-file", TEST_EPUB]
BASE_COMMAND_FILE = ["--input-file", TEST_EPUB]
BASE_COMMAND_FOLDER = ["--input-dir", TEST_DIR]
BAD_TINIFY_COMMAND = BASE_COMMAND_FILE + ["--tinify-api-key", "dawdwada"]
BAD_MAX_IMAGE_RES_COMMAND_1 = BASE_COMMAND_FILE + ["--max-image-resolution", "1", "0"]
BAD_MAX_IMAGE_RES_COMMAND_2 = BASE_COMMAND_FILE + ["--max-image-resolution", "0", "1"]
BAD_MAX_IMAGE_RES_COMMAND_3 = BASE_COMMAND_FILE + ["--max-image-resolution", "0", "0"]
BAD_INPUT_FILE_NOTEXISTS_COMMAND = ["--input-file", "idontexist"]
BAD_INPUT_FILE_NOT_EPUB_COMMAND = ["--input-file", TEST_BAD_EPUB]
BAD_INPUT_FOLDER_COMMAND = ["--input-dir", TEST_BAD_FOLDER]

runner = CliRunner()


def test_version_cli():
    result = runner.invoke(main, VERSION_COMMAND)
    if result.exit_code != 0:
        raise AssertionError
    if result.output.strip() != __version__:
        raise AssertionError


def test_no_inputs():
    result = runner.invoke(main, [])
    if result.exit_code != 1:
        raise AssertionError


def test_both_inputs():
    result = runner.invoke(main, BAD_BOTH_PARAMS_COMMAND)
    if result.exit_code != 1:
        raise AssertionError


def test_bad_tinify_key():
    result = runner.invoke(main, BAD_TINIFY_COMMAND)
    if result.exit_code != 2:
        raise AssertionError


def test_bad_max_image_res():
    result = runner.invoke(main, BAD_MAX_IMAGE_RES_COMMAND_1)
    if result.exit_code != 2:
        raise AssertionError
    result = runner.invoke(main, BAD_MAX_IMAGE_RES_COMMAND_2)
    if result.exit_code != 2:
        raise AssertionError
    result = runner.invoke(main, BAD_MAX_IMAGE_RES_COMMAND_3)
    if result.exit_code != 2:
        raise AssertionError


def test_bad_input_file_not_exists():
    result = runner.invoke(main, BAD_INPUT_FILE_NOTEXISTS_COMMAND)
    if result.exit_code != 2:
        raise AssertionError
    if not result.output.__contains__("does not exist"):
        raise AssertionError


def test_bad_input_file_not_epub():
    result = runner.invoke(main, BAD_INPUT_FILE_NOT_EPUB_COMMAND)
    if result.exit_code != 2:
        raise AssertionError
    if not result.output.__contains__("not an epub file"):
        raise AssertionError


def test_bad_input_folder():
    result = runner.invoke(main, BAD_INPUT_FOLDER_COMMAND)
    if result.exit_code != 2:
        raise AssertionError
    if not result.output.__contains__("does not exist"):
        raise AssertionError


def test_valid_input_file():
    result = runner.invoke(main, BASE_COMMAND_FILE)
    if result.exit_code != 0:
        raise AssertionError


def test_valid_input_folder():
    result = runner.invoke(main, BASE_COMMAND_FOLDER)
    if result.exit_code != 0:
        raise AssertionError
