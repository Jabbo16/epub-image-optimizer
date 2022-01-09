import os
from pathlib import Path

from click.testing import CliRunner

from epub_image_optimizer import __version__
from epub_image_optimizer.cli import main

TEST_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
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
    """ Test the version command """
    result = runner.invoke(main, VERSION_COMMAND)
    assert result.exit_code == 0
    assert result.output.strip() == __version__


def test_no_inputs():
    """ Test error while no input is given """
    result = runner.invoke(main, [])
    assert result.exit_code == 1


def test_both_inputs():
    """ Test error while both type of inputs used """
    result = runner.invoke(main, BAD_BOTH_PARAMS_COMMAND)
    assert result.exit_code == 1


def test_bad_tinify_key():
    """ Test error while bad tinify key is used """
    result = runner.invoke(main, BAD_TINIFY_COMMAND)
    assert result.exit_code == 2


def test_bad_max_image_res():
    """ Test error while bad max image resolution is used """
    result = runner.invoke(main, BAD_MAX_IMAGE_RES_COMMAND_1)
    assert result.exit_code == 2
    result = runner.invoke(main, BAD_MAX_IMAGE_RES_COMMAND_2)
    assert result.exit_code == 2
    result = runner.invoke(main, BAD_MAX_IMAGE_RES_COMMAND_3)
    assert result.exit_code == 2


def test_bad_input_file_not_exists():
    """ Test error while non-existing input file is given """
    result = runner.invoke(main, BAD_INPUT_FILE_NOTEXISTS_COMMAND)
    assert result.exit_code == 2
    assert result.output.__contains__("does not exist")


def test_bad_input_file_not_epub():
    """ Test error while non-epub input file is given """
    result = runner.invoke(main, BAD_INPUT_FILE_NOT_EPUB_COMMAND)
    assert result.exit_code == 2
    assert result.output.__contains__("not an epub file")


def test_bad_input_folder():
    """ Test error while non-existing input folder is given """
    result = runner.invoke(main, BAD_INPUT_FOLDER_COMMAND)
    assert result.exit_code == 2
    assert result.output.__contains__("does not exist")


def test_valid_input_file():
    """ Test valid input file """
    result = runner.invoke(main, BASE_COMMAND_FILE)
    assert result.exit_code == 0


def test_valid_input_folder():
    """ Test valid input folder """
    result = runner.invoke(main, BASE_COMMAND_FOLDER)
    print(result.output)
    assert result.exit_code == 0
