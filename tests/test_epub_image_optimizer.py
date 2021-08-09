from epub_image_optimizer import __version__
from click.testing import CliRunner
from epub_image_optimizer.cli import main


def test_version():
    assert __version__ == '0.1.0'


def test_version_cli():
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert result.output.strip() == __version__
